#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include <ArduinoJson.h>
#include <XPowersLib.h>
#include <Wire.h>
#include <math.h>
#include <BLEDevice.h>
#include "services/gap/ble_svc_gap.h"
#include <BLEServer.h>
#include <BLE2902.h>
#include <BLESecurity.h>
#include <Preferences.h>
#include <TouchDrvCSTXXX.hpp>
#include "ghost.h"
#include "ghost_poses.h"
#include "ghost_motion.h"
#include "usage_layout.h"
#include "render_timing.h"
#include "smooth_text.h"
#include "face_navigation.h"
#include "lucide_icons.h"
#include "notification_sound.h"
#include "notification_audio.h"
#include "response_alert.h"

static constexpr char VERSION[] = "0.7.0";
static constexpr uint16_t BG=0x0000, SPRITE_BG=0x20E4, PURPLE=0x923F, RED=0xFB2F, WHITE=0xFFFF, MUTED=0xAD55, GREEN=0x6EF3;
Arduino_DataBus *bus = new Arduino_ESP32QSPI(12,38,4,5,6,7);
Arduino_CO5300 *panel = new Arduino_CO5300(bus,39,0,480,480,0,0,0,0);
// Compose in RAM; transfer only the changed black animation region on each tick.
Arduino_Canvas *gfx = new Arduino_Canvas(480,480,panel);
XPowersPMU pmu;
TouchDrvCST92xx touch;bool touchOK=false;volatile bool touchPending=false;uint32_t touchEvents=0;String lastWake="boot";
void IRAM_ATTR touchInterrupt(){touchPending=true;}
bool pmuOK=false, available=false, stale=true, details=false;
float used=0, limit=0, overage=0;
unsigned long lastUsage=0, lastPaint=0, lastButton=0;
char input[4096]; size_t count=0; bool overflow=false;
String activity="Unknown", reset="Unknown", plan="KIRO";
unsigned long stateSince=0;
Preferences preferences;
String pairingToken,deviceName,sleepMode="auto",screenLayout="ghost",defaultScreenLayout="ghost";
int brightness=180,sleepAfter=120;
bool sleeping=false;
bool soundEnabled=false,audioOK=false;
String soundPreset="chime";
ResponseAlert responseAlert;
uint32_t soundEvents=0;
uint32_t controlSeq=0,swipeEvents=0,faceHintUntil=0;
void compactFaceGhost();
void paintFaceHint();
unsigned long lastInteraction=0;
uint32_t usageSeq=0, displayedSeq=0;
bool displayAvailable=false;float displayUsed=0,displayLimit=0,displayOverage=0;
void draw();
void paintStatic(bool linked);
uint16_t* regionPixels=nullptr;
uint32_t animationTicks=0,partialFrames=0,fullFrames=0,lastRenderUs=0,maxPartialUs=0,maxTickGap=0;
uint32_t lastAnimationTick=0;
bool powerBattery=false,powerUSB=false,powerCharging=false;
int powerPercent=0;
uint32_t powerSample=0,frameNow=0;
bool powerSampled=false;
void samplePower(){
    uint32_t now=millis();
    if(powerSampled && now-powerSample<1000)return;
    powerSampled=true;powerSample=now;
    powerBattery=pmuOK && pmu.isBatteryConnect();powerUSB=pmuOK && pmu.isVbusIn();
    powerCharging=pmuOK && pmu.isCharging();powerPercent=powerBattery?pmu.getBatteryPercent():0;
}
void flushRegion(Rect r){
    const uint16_t* source=gfx->getFramebuffer();
    for(int y=0;y<r.h;y++)memcpy(regionPixels+y*r.w,source+(r.y+y)*480+r.x,r.w*sizeof(uint16_t));
    panel->draw16bitRGBBitmap(r.x,r.y,regionPixels,r.w,r.h);
    partialFrames++;
}

static const char* SERVICE_UUID="f3641400-00b0-4240-ba50-05ca45bf8abc";
static const char* RX_UUID="f3641401-00b0-4240-ba50-05ca45bf8abc";
static const char* TX_UUID="f3641402-00b0-4240-ba50-05ca45bf8abc";
BLECharacteristic* bleTx=nullptr;
volatile bool bleConnected=false,advertiseAgain=false;
bool replyBLE=false;
volatile uint32_t bleGeneration=0;
uint32_t txGeneration=0,txLast=0,txDropped=0;
ReplyQueue<8192> replies;
QueueHandle_t blePackets;
struct Packet {char bytes[4096];};
class Connections:public BLEServerCallbacks {
    void onConnect(BLEServer*) override {bleGeneration++;bleConnected=true;}
    void onDisconnect(BLEServer*) override {bleConnected=false;bleGeneration++;advertiseAgain=true;}
};
class Receive:public BLECharacteristicCallbacks {
    Packet incoming{};size_t size=0;bool dropped=false;uint32_t generation=0;
    void onWrite(BLECharacteristic* characteristic) override {
        if(generation!=bleGeneration){generation=bleGeneration;size=0;dropped=false;}
        String value=characteristic->getValue();
        for(size_t i=0;i<value.length();i++){
            char c=value[i];
            if(c=='\n') {if(!dropped){incoming.bytes[size]=0;xQueueSend(blePackets,&incoming,0);}size=0;dropped=false;}
            else if(c!='\r'){if(size<4095)incoming.bytes[size++]=c;else dropped=true;}
        }
    }
};
void advertiseName(){
    BLEDevice::getAdvertising()->stop();
    ble_svc_gap_device_name_set(deviceName.length()?deviceName.c_str():"Kirometer");
    BLEAdvertisementData scan;scan.setName(deviceName.length()?deviceName.c_str():"Kirometer");
    BLEDevice::getAdvertising()->setScanResponseData(scan);
    BLEDevice::startAdvertising();
}
void reply(const String& message){
    if(!replyBLE){Serial.println(message);return;}
    if(bleConnected && !replies.push(message.c_str(),message.length()))txDropped++;
}
void serviceReplies(){
    if(txGeneration!=bleGeneration || !bleConnected){
        txGeneration=bleGeneration;replies.clear();
        // Discard requests from a disconnected client, including queued controls.
        if(!bleConnected)xQueueReset(blePackets);
    }
    if(!bleConnected || !replies.size() || millis()-txLast<8)return;
    uint8_t chunk[20];size_t n=replies.pop(chunk,sizeof(chunk));
    bleTx->setValue(chunk,n);bleTx->notify();txLast=millis();
}

String statusJson() {
    samplePower();
    JsonDocument doc;
    doc["animation_interval_ms"]=FRAME_INTERVAL_MS;doc["animation_ticks"]=animationTicks;
    doc["partial_frames"]=partialFrames;doc["full_frames"]=fullFrames;
    doc["last_render_us"]=lastRenderUs;doc["max_partial_render_us"]=maxPartialUs;
    doc["max_animation_gap_ms"]=maxTickGap;doc["ble_reply_drops"]=txDropped;
    doc["type"]="kirometer.status"; doc["protocol"]=1; doc["version"]=VERSION;
    char id[17]; snprintf(id,sizeof(id),"%012llx",ESP.getEfuseMac()); doc["device_id"]=id;
    doc["uptime_seconds"]=millis()/1000;doc["bluetooth_connected"]=bleConnected;doc["device_name"]=deviceName;doc["bluetooth_supported"]=true;doc["paired"]=pairingToken.length()>0;
    doc["touch_supported"]=touchOK;doc["touch_events"]=touchEvents;doc["last_wake"]=lastWake;
    doc["default_screen_layout"]=defaultScreenLayout;doc["screen_layouts_version"]=2;doc["swipe_events"]=swipeEvents;doc["screen_layouts_supported"]=true;doc["screen_layout"]=screenLayout;
    doc["controls_supported"]=true;doc["brightness"]=brightness;doc["sleep_mode"]=sleepMode;doc["sleeping"]=sleeping;doc["sleep_after"]=sleepAfter;doc["control_seq"]=controlSeq;
    doc["sounds_supported"]=true;doc["audio_ready"]=audioOK;doc["sound_enabled"]=soundEnabled;doc["sound_preset"]=soundPreset;doc["sound_events"]=soundEvents;
    doc["usage_connected"]=lastUsage && millis()-lastUsage<30000;
    doc["activity"]=activity;doc["usage_available"]=available; doc["usage_stale"]=stale;
    doc["displayed_seq"]=displayedSeq;doc["display_usage_available"]=displayAvailable;
    if(displayAvailable){doc["display_usage_used"]=displayUsed;doc["display_usage_limit"]=displayLimit;doc["display_usage_overage"]=displayOverage;}
    else{doc["display_usage_used"]=nullptr;doc["display_usage_limit"]=nullptr;doc["display_usage_overage"]=nullptr;}
    doc["charging"]=powerCharging;
    if(powerBattery) doc["battery_percent"]=powerPercent;
    else doc["battery_percent"]=nullptr;
    doc["power_source"]=pmuOK ? (powerUSB?"usb":"battery") : "unknown";
    String result;serializeJson(doc,result);return result;
}
void status(){reply(statusJson());}

void handle(const char *line) {
    JsonDocument doc;
    if(deserializeJson(doc,line)) return;
    if(doc["protocol"].as<int>()!=1) return;
    if(replyBLE && (pairingToken.length()<32 || doc["token"].as<String>()!=pairingToken))return;
    String type=doc["type"].as<String>();
    if(type=="kirometer.status") {status();return;}
    if(type!="kirometer.usage") return;
    JsonVariant controls=doc["controls"];
    uint32_t cs=controls["seq"] | 0;
    if(cs && cs!=controlSeq){
        if(controls["sound_enabled"].is<bool>()){soundEnabled=controls["sound_enabled"].as<bool>();preferences.putBool("sound_enabled",soundEnabled);}
        String sound=controls["sound_preset"] | "";
        if(NotificationSound::index(sound.c_str())>=0){soundPreset=sound;preferences.putString("sound_preset",soundPreset);}
        if(controls["brightness"].is<int>()){brightness=constrain(controls["brightness"].as<int>(),5,255);panel->setBrightness(brightness);preferences.putInt("brightness",brightness);}
        String layout=controls["screen_layout"] | "";
        if(validLayout(layout.c_str())){
            screenLayout=defaultScreenLayout=layout;preferences.putString("screen_layout",layout);details=false;lastInteraction=millis();
        }
        String mode=controls["sleep_mode"] | "";
        if(mode=="awake" || mode=="sleep" || mode=="auto"){sleepMode=mode;preferences.putString("sleep_mode",mode);lastInteraction=millis();}
        if(controls["sleep_after"].is<int>()){sleepAfter=constrain(controls["sleep_after"].as<int>(),30,3600);preferences.putInt("sleep_after",sleepAfter);}
        if(!replyBLE && controls["pairing_token"].is<const char*>()){
            String token=controls["pairing_token"].as<String>();
            if(token.length()==48){pairingToken=token;preferences.putString("ble_token",token);}
        }
        String name=controls["device_name"] | "";
        bool validName=name.length()>0 && name.length()<=26;
        for(size_t i=0;i<name.length();i++)if((uint8_t)name[i]<32 || name[i]==127)validName=false;
        if(validName){deviceName=name;preferences.putString("device_name",name);advertiseName();}
        controlSeq=cs;
    }
    JsonVariant c=doc["credits"][0];
    bool valid=c["used"].is<float>() && c["limit"].is<float>();
    float u=c["used"].as<float>(), l=c["limit"].as<float>();
    available=doc["available"].as<bool>() && valid && isfinite(u) && isfinite(l) && u>=0 && l>=0;
    stale=doc["stale"].isNull() || doc["stale"].as<bool>();
    if(available){used=u;limit=l;overage=max(0.0f,u-l);} else {used=limit=overage=0;}
    reset=c["reset_at"].is<const char*>()?String(c["reset_at"].as<const char*>()):"Unknown";
    reset=reset.substring(0,20);
    bool baseline=doc["notification_baseline"].as<bool>() || !lastUsage || millis()-lastUsage>30000;
    if(responseAlert.observe(doc["response_event"] | "",baseline,soundEnabled && audioOK,doc["needs_response"].as<bool>())){
        playNotificationSound(NotificationSound::index(soundPreset.c_str()));soundEvents++;
    }
    String a=doc["activity"] | "unknown";
    String nextActivity=a=="working"?"Working":a=="idle"?"Ready":a=="attention"?"Needs attention":a=="complete"?"Complete":a=="error"?"Error":"Unknown";
    if(nextActivity!=activity){activity=nextActivity;stateSince=millis();lastInteraction=millis();}
    plan=doc["plan"].is<const char*>()?String(doc["plan"].as<const char*>()):"KIRO";plan=plan.substring(0,18);
    usageSeq=doc["seq"].as<uint32_t>();
    lastUsage=millis();
    draw();
    JsonDocument ack;ack["type"]="kirometer.ack";ack["protocol"]=1;ack["seq"]=doc["seq"];ack["accepted"]=true;
    String ackJson;serializeJson(ack,ackJson);reply(ackJson);if(replyBLE)status();
}

void label(int x,int y,const String &text,int size,uint16_t color=WHITE){
    smoothText(gfx->getFramebuffer(),480,480,x,y,text.c_str(),size,color);
}
String number(float n){return String(n,n==floor(n)?0:1);}

void centered(int y,const String &text,int size,uint16_t color=WHITE){
    auto bounds=textBounds(text.c_str(),size);int w=bounds.w,x1=bounds.x;
    label((480-w)/2-x1,y,text,size,color);
}
void wakeDisplay(const char* source){
    if(sleepMode=="sleep"){sleepMode="auto";preferences.putString("sleep_mode",sleepMode);}
    lastInteraction=millis();lastWake=source;details=false;sleeping=false;draw();
}
void peekingGhost(int x,int y,int rotation){
    bool blink=frameNow%5000>=4800;
    for(int gy=0;gy<GHOST_H;gy++)for(int gx=0;gx<GHOST_W;gx++){
        uint16_t color=GHOST[gy*GHOST_W+gx];
        if(blink && gy>=39 && gy<69 && ((gx>=59 && gx<77)||(gx>=85 && gx<103)))color=(gy>=52 && gy<55)?SPRITE_BG:WHITE;
        if(color==SPRITE_BG || color==BG)continue;
        int px=gx,py=gy;
        if(rotation==1){px=GHOST_H-1-gy;py=gx;}
        else if(rotation==2){px=GHOST_W-1-gx;py=GHOST_H-1-gy;}
        else if(rotation==3){px=gy;py=GHOST_W-1-gx;}
        gfx->drawPixel(x+px,y+py,color);
    }
}
// State-specific poses stay inside the reserved black partial-refresh region.
void heroGhost(){
    GhostState state=activity=="Working"?GhostState::Working:activity=="Needs attention"?GhostState::Attention:activity=="Complete"?GhostState::Complete:activity=="Error"?GhostState::Error:activity=="Ready"?GhostState::Ready:GhostState::Unknown;
    GhostPose pose=ghostPose(state,frameNow-stateSince);
    const uint16_t* frames[]={GHOST_SOUTH,GHOST_EAST,GHOST_NORTH,GHOST_WEST};
    const uint16_t* blinks[]={GHOST_SOUTH_BLINK,GHOST_EAST_BLINK,GHOST_NORTH_BLINK,GHOST_WEST_BLINK};
    const uint16_t* sprite=(pose.blink?blinks:frames)[static_cast<int>(pose.facing)];
    for(int dy=0;dy<190;dy++)for(int dx=0;dx<156;dx++){
        uint16_t color=sprite[(dy*150/190)*123+dx*123/156];
        gfx->drawPixel(pose.x+dx,pose.y+dy,color);
    }
}
void rightLabel(int right,int y,const String& text,int size,uint16_t color=WHITE){
    auto bounds=textBounds(text.c_str(),size);int w=bounds.w,x1=bounds.x;
    label(right-w-x1,y,text,size,color);
}
void miniGhost(){
    int bob=lroundf(sinf(frameNow*0.0015707963f)*2);
    const uint16_t* sprite=frameNow%5000>=4750?GHOST_SOUTH_BLINK:GHOST_SOUTH;
    for(int y=0;y<56;y++)for(int x=0;x<46;x++)
        gfx->drawPixel(25+x,14+y+bob,sprite[(y*150/56)*123+x*123/46]);
}
void paintAnimation(){
    if(sleeping){
        unsigned phase=frameNow%20000;
        if(phase<5500){
            int reveal=int(sin(phase/5500.0f*3.1416f)*105);
            int edge=(frameNow/20000)%4;
            if(edge==0)peekingGhost(-GHOST_H+reveal,178,1);
            else if(edge==1)peekingGhost(480-reveal,178,3);
            else if(edge==2)peekingGhost(178,480-reveal,0);
            else peekingGhost(178,-GHOST_H+reveal,2);
        }
    }else if(!details && faceIndex(screenLayout.c_str())>=0){
        compactFaceGhost();
    }else if(!details && screenLayout=="usage"){
        miniGhost();
    }else if(!details){
        heroGhost();
        if(activity=="Working"){
            // Smoothly pulse within the reserved dots area.
            for(int i=0;i<3;i++){
                float pulse=(sinf(frameNow*0.0062831853f-i*2.0944f)+1)*0.5f;
                gfx->fillCircle(225+i*15,343,3+lroundf(pulse*2),pulse>.45f?PURPLE:0x39A7);
            }
        }
    }
}
void draw() {
    frameNow=millis();samplePower();
    bool linked=lastUsage && frameNow-lastUsage<30000;
    sleeping=sleepMode=="sleep" || (sleepMode=="auto" && activity=="Ready" && frameNow-lastInteraction>unsigned(sleepAfter)*1000);
    // Cache only visible state. Sequence acknowledgments still advance for unchanged usage.
    bool hint=!sleeping && !details && int32_t(faceHintUntil-frameNow)>0;
    String key=sleeping?"sleep":String(details)+"|"+hint+"|"+screenLayout+"|"+linked+"|"+bleConnected+"|"+powerBattery+"|"+powerUSB+"|"+powerCharging+"|"+powerPercent+"|"+activity+"|"+plan+"|"+reset+"|"+available+"|"+stale+"|"+String(used,4)+"|"+String(limit,4)+"|"+String(overage,4);
    static String paintedKey;
    static bool oldPeekVisible=false;
    static unsigned oldEdge=0;
    bool full=key!=paintedKey;
    uint32_t started=micros();
    if(full){
        paintedKey=key;
        gfx->fillScreen(BG);
        if(!sleeping)paintStatic(linked);
        paintAnimation();if(hint)paintFaceHint();gfx->flush();fullFrames++;
    }else if(frameNow-lastPaint>=FRAME_INTERVAL_MS){
        bool visible=sleeping && frameNow%20000<5500;
        unsigned edge=(frameNow/20000)%4;
        if(!sleeping && !details){
            Rect r=faceRegion(screenLayout.c_str());
            gfx->fillRect(r.x,r.y,r.w,r.h,BG);
            paintAnimation();flushRegion(r);
        }else if(sleeping && (visible || oldPeekVisible)){
            if(oldPeekVisible && oldEdge!=edge){
                Rect old=peekRegion(oldEdge);gfx->fillRect(old.x,old.y,old.w,old.h,BG);flushRegion(old);
            }
            Rect r=peekRegion(edge);gfx->fillRect(r.x,r.y,r.w,r.h,BG);
            paintAnimation();flushRegion(r);
        }
        maxPartialUs=max(maxPartialUs,uint32_t(micros()-started));
    }else{
        displayedSeq=usageSeq;return;
    }
    if(lastAnimationTick)maxTickGap=max(maxTickGap,frameNow-lastAnimationTick);
    lastAnimationTick=frameNow;animationTicks++;lastPaint=frameNow;
    oldPeekVisible=sleeping && frameNow%20000<5500;oldEdge=(frameNow/20000)%4;
    lastRenderUs=micros()-started;
    displayedSeq=usageSeq;displayAvailable=available && !sleeping;displayUsed=used;displayLimit=limit;displayOverage=overage;
}

void powerIcons(int y);
void paintDeviceIndicators(){powerIcons(10);}
String resetLabel(){
    int month=reset.substring(5,7).toInt(),day=reset.substring(8,10).toInt();
    const char* months[]={"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
    if(reset.length()>=10 && reset[4]=='-' && reset[7]=='-' && month>=1 && month<=12 && day>=1 && day<=31)
        return String("Resets ")+months[month-1]+" "+day+", "+reset.substring(0,4);
    return "Reset date unavailable";
}
void fittedLabel(int x,int y,const String& value,int width,int size,uint16_t color=WHITE){
    while(size>1 && textBounds(value.c_str(),size).w>width)size--;
    label(x,y,value,size,color);
}
void paintUsageDashboard(bool linked){
    // Three readable sections; overage compares with the plan allowance, not a fictitious cap.
    gfx->fillRoundRect(20,80,440,42,10,0x2106);
    fittedLabel(36,88,plan,408,3,0xC51F);
    gfx->fillRoundRect(20,136,440,152,12,0x1082);
    label(36,148,"Plan credits",1,MUTED);
    UsageBars bars=usageBars(available,used,limit,overage);
    fittedLabel(36,183,available?number(used)+" / "+number(limit):"-- / --",286,3);
    rightLabel(444,186,bars.comparable?String(bars.usedPercent,0)+"%":"--%",2,0xC51F);
    gfx->fillRoundRect(36,234,408,14,7,0x2945);
    if(bars.includedWidth>0)gfx->fillRoundRect(36,234,max(2,bars.includedWidth),14,min(7,max(1,bars.includedWidth/2)),PURPLE);
    label(36,260,resetLabel(),1,MUTED);
    gfx->fillRoundRect(20,302,440,132,12,0x1082);
    label(36,314,"Overage credits",1,MUTED);
    fittedLabel(36,343,available?number(overage)+" credits":"Unavailable",408,3,overage>0?RED:WHITE);
    gfx->fillRoundRect(36,387,408,12,6,0x2945);
    if(bars.overageWidth>0)gfx->fillRoundRect(36,387,max(2,bars.overageWidth),12,min(6,max(1,bars.overageWidth/2)),RED);
    String extra=bars.comparable?number(bars.overagePercent)+"% of plan allowance":available?"No allowance to compare":"Usage unavailable";
    label(36,410,extra,1,MUTED);
    String connection=linked?"Connected":"Disconnected";
    if(stale)connection+=" - stale usage";
    int w=textBounds(connection.c_str(),1).w;
    int x=(480-w)/2;gfx->fillCircle(x-16,459,5,linked?GREEN:RED);
    label(x,450,connection,1,linked?GREEN:RED);
}
void lucide(int x,int y,const uint8_t* pixels,int size,uint16_t color=WHITE){
    auto canvas=gfx->getFramebuffer();
    for(int row=0;row<size;row++)for(int col=0;col<size;col++){
        int px=x+col,py=y+row;if(px<0 || py<0 || px>=480 || py>=480)continue;
        unsigned index=row*size+col,byte=pixels[index/2],a=(index&1)?byte&15:byte>>4;
        if(a)canvas[py*480+px]=blend565(color,canvas[py*480+px],a);
    }
}
void powerIcons(int y){
    if(bleConnected)lucide(340,y,icon_bluetooth_24,24);
    if(powerUSB)lucide(310,y,icon_plug_24,24,GREEN);
    if(powerBattery){
        label(373,y+3,String(powerPercent)+"%",1);
        auto icon=powerCharging?icon_battery_charging_24:powerPercent>=95?icon_battery_full_24:powerPercent>=40?icon_battery_medium_24:powerPercent>=10?icon_battery_low_24:icon_battery_24;
        lucide(431,y,icon,24,powerCharging?GREEN:WHITE);
    }else{
        lucide(431,y,powerUSB?icon_plug_24:icon_battery_warning_24,24,MUTED);
        label(371,y+3,powerUSB?"USB":"--",1,MUTED);
    }
}
void faceFooter(bool linked){
    gfx->fillCircle(30,447,4,linked?GREEN:RED);
    label(44,438,linked?(stale?"Connected - stale":"Connected"):"Disconnected",1,linked?GREEN:RED);
    powerIcons(432);
}
void faceBar(int x,int y,int width,float ratio,int height=12){
    gfx->fillRoundRect(x,y,width,height,height/2,0x2945);
    int fill=constrain(int(ratio*width),0,width);
    if(fill)gfx->fillRoundRect(x,y,max(height,fill),height,height/2,PURPLE);
}
void faceGauge(float ratio){
    // Antialiased arc; its center remains black for bounded mascot animation.
    auto canvas=gfx->getFramebuffer();const float start=0.8f*PI,span=1.4f*PI;
    for(int y=50;y<375;y++)for(int x=78;x<403;x++){
        float dx=x-240,dy=y-212,r=sqrtf(dx*dx+dy*dy),edge=7.5f-fabsf(r-154);
        if(edge<=0)continue;
        float angle=atan2f(dy,dx);while(angle<start)angle+=2*PI;
        if(angle>start+span)continue;
        uint16_t color=angle-start<=span*constrain(ratio,0.0f,1.0f)?PURPLE:0x2945;
        unsigned alpha=unsigned(min(1.0f,edge)*15);canvas[y*480+x]=blend565(color,canvas[y*480+x],alpha);
    }
}
void compactFaceGhost(){
    int index=faceIndex(screenLayout.c_str());Rect r=faceRegion(screenLayout.c_str());
    GhostState state=activity=="Working"?GhostState::Working:activity=="Needs attention"?GhostState::Attention:activity=="Complete"?GhostState::Complete:activity=="Error"?GhostState::Error:activity=="Ready"?GhostState::Ready:GhostState::Unknown;
    auto pose=ghostPose(state,frameNow-stateSince);
    const uint16_t* frames[]={GHOST_SOUTH,GHOST_EAST,GHOST_NORTH,GHOST_WEST};
    const uint16_t* blinks[]={GHOST_SOUTH_BLINK,GHOST_EAST_BLINK,GHOST_NORTH_BLINK,GHOST_WEST_BLINK};
    int direction=int(pose.facing);if(activity=="Ready" && direction==0){if(index==1)direction=1;if(index==2)direction=3;}
    const auto* sprite=(pose.blink?blinks:frames)[direction];
    const int widths[]={94,115,92,70},heights[]={115,140,112,86};int w=widths[index],h=heights[index];
    int x=r.x+(r.w-w)/2,y=r.y+(r.h-h)/2+lroundf(sinf((frameNow-stateSince)*0.00157f)*3);
    for(int row=0;row<h;row++)for(int col=0;col<w;col++)gfx->drawPixel(x+col,y+row,sprite[(row*150/h)*123+col*123/w]);
}
void paintFace(bool linked){
    int index=faceIndex(screenLayout.c_str());
    UsageBars bars=usageBars(available,used,limit,overage);
    String pct=bars.comparable?String(bars.usedPercent,0)+"%":"--%";
    String total=available?number(used):"--",allowance=available?number(limit):"--";
    String count=total+" / "+allowance;
    String extra=available?number(overage)+" extra credits":"Usage unavailable";
    if(index==0){
        centered(24,plan,2,0xC51F);faceGauge(bars.comparable?bars.usedPercent/100:0);
        centered(222,pct,5);centered(286,"plan used",1,MUTED);
        int size=textBounds((count+" credits").c_str(),3).w<=420?3:2;
        centered(330,count+" credits",size);
        gfx->fillRoundRect(102,374,276,43,21,overage>0?0x3083:0x1082);
        centered(386,extra,1,overage>0?RED:MUTED);
    }else if(index==1){
        fittedLabel(28,27,plan,215,2,0xC51F);
        fittedLabel(26,95,total,222,6);label(28,173,"of "+allowance+" credits",1,MUTED);
        fittedLabel(283,65,activity,168,2,0xC51F);gfx->drawFastVLine(260,74,197,0x2945);
        label(28,290,"PLAN USED",1,MUTED);rightLabel(452,281,pct,3,0xC51F);
        faceBar(28,328,424,bars.usedPercent/100,16);
        label(28,370,extra,1,overage>0?RED:MUTED);
        rightLabel(452,401,resetLabel(),1,MUTED);
    }else if(index==2){
        fittedLabel(28,27,plan,380,2,0xC51F);
        label(28,76,"MONTHLY / CREDITS",1,MUTED);
        fittedLabel(26,126,total,280,6);label(28,200,"/ "+allowance,3,MUTED);
        rightLabel(452,214,pct,3,0xC51F);
        for(int x=26;x<454;x+=13)gfx->drawFastHLine(x,271,5,0x632D);
        label(28,295,"Included plan",1,MUTED);faceBar(28,333,424,bars.usedPercent/100,10);
        label(28,370,"Overage",2,MUTED);String credits=available?number(overage)+" credits":"--";
        int size=textBounds(credits.c_str(),3).w<270?3:2;rightLabel(452,362,credits,size,overage>0?RED:WHITE);
        label(28,405,resetLabel(),1,MUTED);
    }else{
        fittedLabel(28,27,plan,290,2,0xC51F);
        label(28,109,overage>0?"EXTRA CREDITS":"CREDITS LEFT",1,overage>0?RED:MUTED);
        fittedLabel(22,171,available?number(overage>0?overage:max(0.0f,limit-used)):"--",424,7,overage>0?RED:WHITE);
        label(28,286,overage>0?"Plan allowance used":"Ready for your next idea",1,MUTED);
        fittedLabel(28,324,count+" used",308,3);faceBar(28,374,424,bars.usedPercent/100,8);
        label(28,398,overage>0?"Overage beyond your plan":resetLabel(),1,overage>0?RED:MUTED);
    }
    faceFooter(linked);
}
void paintFaceHint(){
    int index=allFaceIndex(screenLayout.c_str());if(index<0)return;
    gfx->fillRect(0,428,480,52,BG);centered(430,ALL_FACE_NAMES[index],1,0xC51F);
    for(int i=0;i<6;i++)gfx->fillCircle(195+i*18,465,i==index?4:3,i==index?PURPLE:0x632D);
}

void paintStatic(bool linked) {
    gfx->fillScreen(BG);
    if(!details && faceIndex(screenLayout.c_str())>=0){paintFace(linked);return;}
    paintDeviceIndicators();
    if(!details && screenLayout=="usage"){paintUsageDashboard(linked);return;}
    gfx->fillCircle(24,24,5,linked?GREEN:RED);
    label(38,13,linked?"Connected":"Disconnected",1);
    if(!details){
        uint16_t stateColor=activity=="Error"?RED:activity=="Complete"?GREEN:0xBB5F;
        centered(65,activity,activity=="Needs attention"?3:4,stateColor);
        // A single compact usage section; supporting metrics live behind its touch target.
        gfx->fillRoundRect(30,364,150,29,8,0x3108);
        String badge=plan; if(badge.length()>12)badge=badge.substring(0,11)+"…";
        label(39,370,badge,1,0xC51F);
        String value=available?number(used)+" / "+number(limit):"-- / --";
        int bw=textBounds(value.c_str(),3).w;
        rightLabel(450,365,value,bw<=254?3:2);
        gfx->fillRoundRect(30,408,420,12,6,0x39A7);
        float base=available?min(used,limit):0;
        float total=max(limit,base+overage);
        int included=total>0?constrain(int(base/total*420),0,420):0;
        int extra=available && total>0?constrain(int(overage/total*420),0,420-included):0;
        if(included>0)gfx->fillRect(30,408,max(2,included),12,PURPLE);
        if(extra>0)gfx->fillRect(30+included,408,extra,12,RED);
        label(30,438,available?number(max(0.0f,limit-used))+" credits left":"Usage unavailable",1,MUTED);
        if(available && overage>0)rightLabel(450,438,"+"+number(overage)+" overage",1,RED);
        else if(stale)rightLabel(450,438,"Stale",1,MUTED);
    }else{
        label(18,60,"Usage details",4);
        label(18,108,plan,2,0xC51F);
        const int ys[]={142,192,242,292,342};
        const char* names[]={"Used","Allowance","Left","Overage","Resets"};
        String values[]={available?number(used):"--",available?number(limit):"--",available?number(max(0.0f,limit-used)):"--",available?number(overage):"--",reset.substring(0,10)};
        for(int i=0;i<5;i++){
            label(18,ys[i]+10,names[i],2,MUTED);
            int valueSize=i==4?3:4;
            // Preserve a readable gap if a large account total needs a smaller font.
            while(valueSize>2 && textBounds(values[i].c_str(),valueSize).w>286)valueSize--;
            rightLabel(462,ys[i],values[i],valueSize,i==3?RED:WHITE);
            gfx->drawFastHLine(18,ys[i]+43,444,0x39A7);
        }
        label(18,392,stale?"Usage cache stale":"Usage cache fresh",2,MUTED);
        gfx->drawRoundRect(18,425,444,42,9,PURPLE);
        centered(436,faceIndex(screenLayout.c_str())>=0?"Back to face":screenLayout=="usage"?"Back to usage":"Back to ghost",2);
    }
}

void setup(){
    Serial.setRxBufferSize(4096);Serial.begin(115200);Wire.begin(15,14);
    pmuOK=pmu.begin(Wire,0x34,15,14);
    if(pmuOK){pmu.enableBattDetection();pmu.enableBattVoltageMeasure();}
    if(!gfx->begin()) {while(true){delay(1000);}}
    regionPixels=(uint16_t*)heap_caps_malloc(HERO_REGION.w*HERO_REGION.h*sizeof(uint16_t),MALLOC_CAP_8BIT);
    if(!regionPixels){Serial.println("Animation buffer allocation failed");while(true)delay(1000);}
    // Waveshare's 2.16-inch example uses MADCTL 0xA0 for this panel.
    bus->writeC8D8(0x36,0xA0);
    preferences.begin("kirometer",false);
    screenLayout=preferences.getString("screen_layout","ghost");
    if(!validLayout(screenLayout.c_str()))screenLayout="ghost";
    defaultScreenLayout=screenLayout;
    brightness=constrain(preferences.getInt("brightness",180),5,255);
    sleepMode=preferences.getString("sleep_mode","auto");sleepAfter=preferences.getInt("sleep_after",120);
    panel->setBrightness(brightness);
    soundEnabled=preferences.getBool("sound_enabled",false);soundPreset=preferences.getString("sound_preset","chime");
    if(NotificationSound::index(soundPreset.c_str())<0)soundPreset="chime";
    audioOK=beginNotificationAudio();
    // Waveshare CST9220: reset GPIO40, interrupt GPIO11 (not the display reset).
    touch.setPins(40,11);touchOK=touch.begin(Wire,0x5A,15,14);
    if(touchOK){touch.setMaxCoordinates(480,480);touch.setSwapXY(true);touch.setMirrorXY(true,false);attachInterrupt(11,touchInterrupt,FALLING);}

    pairingToken=preferences.getString("ble_token","");deviceName=preferences.getString("device_name","");
    blePackets=xQueueCreate(2,sizeof(Packet));
    BLEDevice::init(deviceName.length()?deviceName.c_str():"Kirometer");
    // One-time recovery from older merged factory images that erased bond storage.
    if(!preferences.getBool("ble_recovered",false)){ble_store_clear();preferences.putBool("ble_recovered",true);}

    BLESecurity::setAuthenticationMode(true,false,true);
    BLESecurity::setCapability(ESP_IO_CAP_NONE);
    BLESecurity::setInitEncryptionKey();BLESecurity::setRespEncryptionKey();
    BLEServer* server=BLEDevice::createServer();server->setCallbacks(new Connections());
    BLEService* service=server->createService(SERVICE_UUID);
    BLECharacteristic* rx=service->createCharacteristic(RX_UUID,BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_ENC);
    rx->setAccessPermissions(ESP_GATT_PERM_WRITE_ENCRYPTED);rx->setCallbacks(new Receive());
    bleTx=service->createCharacteristic(TX_UUID,BLECharacteristic::PROPERTY_NOTIFY);
    BLECharacteristic* pairing=service->createCharacteristic("f3641403-00b0-4240-ba50-05ca45bf8abc",BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_READ_ENC);
    pairing->setValue("Kirometer");
    service->start();BLEDevice::getAdvertising()->addServiceUUID(SERVICE_UUID);advertiseName();
    pinMode(0,INPUT_PULLUP);pinMode(18,INPUT_PULLUP);
    status();draw();
}
void loop(){
    if(advertiseAgain){advertiseAgain=false;advertiseName();}
    serviceReplies();
    Packet packet;if(replies.free()>=4096 && xQueueReceive(blePackets,&packet,0)==pdTRUE){replyBLE=true;handle(packet.bytes);replyBLE=false;}
    static bool touchDown=false;
    static TouchGesture gesture;
    static unsigned long lastTouchPoll=0;
    if(touchOK && (touchPending || touchDown) && millis()-lastTouchPoll>=20){
        touchPending=false;lastTouchPoll=millis();int16_t tx[5],ty[5];
        bool pressed=touch.getPoint(tx,ty,5)>0;
        if(pressed && !touchDown){
            touchEvents++;bool wakeOnly=sleeping;lastInteraction=millis();
            gesture.begin(tx[0],ty[0],millis(),wakeOnly);
            if(wakeOnly)wakeDisplay("touch");
        }else if(pressed){gesture.move(tx[0],ty[0]);lastInteraction=millis();}
        else if(touchDown){
            auto action=gesture.end(millis());int x=gesture.x(),y=gesture.y();
            if(action==Gesture::Next || action==Gesture::Previous){
                details=false;screenLayout=nextFace(screenLayout.c_str(),action==Gesture::Next?1:-1);swipeEvents++;faceHintUntil=millis()+1300;
                lastInteraction=millis();draw();
            }else if(action==Gesture::Tap && x>=18 && x<=462){
                bool usageTarget=faceIndex(screenLayout.c_str())>=0?(y>=75 && y<=427):screenLayout=="usage"?(y>=136 && y<=434):(y>=354 && y<=461);
                if(!details && usageTarget){details=true;draw();}
                else if(details && y>=425){details=false;draw();}
            }
        }
        touchDown=pressed;
    }
    while(Serial.available()){
        char c=Serial.read();
        if(c=='\n'){if(!overflow){input[count]=0;handle(input);}count=0;overflow=false;}
        else if(c!='\r'){if(count<sizeof(input)-1)input[count++]=c;else overflow=true;}
    }
    if((digitalRead(0)==LOW || digitalRead(18)==LOW) && millis()-lastButton>400){if(sleeping){wakeDisplay("button");}else details=!details;lastButton=millis();lastInteraction=millis();}
    if(millis()-lastPaint>=FRAME_INTERVAL_MS)draw();
    delay(2);
}
