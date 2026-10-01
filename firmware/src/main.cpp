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
#include "render_timing.h"
#include "fonts/FreeSans12pt7b.h"
#include "fonts/FreeSans10pt7b.h"
#include "fonts/FreeSans18pt7b.h"
#include "fonts/FreeSans24pt7b.h"

static constexpr char VERSION[] = "0.5.8";
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
String pairingToken,deviceName,sleepMode="auto";
int brightness=180,sleepAfter=120;
bool sleeping=false;
uint32_t controlSeq=0;
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
    doc["controls_supported"]=true;doc["brightness"]=brightness;doc["sleep_mode"]=sleepMode;doc["sleeping"]=sleeping;doc["sleep_after"]=sleepAfter;doc["control_seq"]=controlSeq;
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
        if(controls["brightness"].is<int>()){brightness=constrain(controls["brightness"].as<int>(),5,255);panel->setBrightness(brightness);preferences.putInt("brightness",brightness);}
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
    gfx->setFont(size>=4?&FreeSans24pt7b:size==3?&FreeSans18pt7b:size==1?&FreeSans10pt7b:&FreeSans12pt7b);
    gfx->setTextSize(1);gfx->setTextColor(color);
    gfx->setCursor(x,y+(size>=4?36:size==3?27:size==1?15:18));gfx->print(text);
}
String number(float n){return String(n,n==floor(n)?0:1);}

void centered(int y,const String &text,int size,uint16_t color=WHITE){
    label(0,0,"",size,color);int16_t x1,y1;uint16_t w,h;
    gfx->getTextBounds(text,0,0,&x1,&y1,&w,&h);
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
    label(0,0,"",size,color);int16_t x1,y1;uint16_t w,h;
    gfx->getTextBounds(text,0,0,&x1,&y1,&w,&h);
    label(right-w-x1,y,text,size,color);
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
    String key=sleeping?"sleep":String(details)+"|"+linked+"|"+bleConnected+"|"+powerBattery+"|"+powerUSB+"|"+powerCharging+"|"+powerPercent+"|"+activity+"|"+plan+"|"+reset+"|"+available+"|"+stale+"|"+String(used,4)+"|"+String(limit,4)+"|"+String(overage,4);
    static String paintedKey;
    static bool oldPeekVisible=false;
    static unsigned oldEdge=0;
    bool full=key!=paintedKey;
    uint32_t started=micros();
    if(full){
        paintedKey=key;
        gfx->fillScreen(BG);
        if(!sleeping)paintStatic(linked);
        paintAnimation();gfx->flush();fullFrames++;
    }else if(frameNow-lastPaint>=FRAME_INTERVAL_MS){
        bool visible=sleeping && frameNow%20000<5500;
        unsigned edge=(frameNow/20000)%4;
        if(!sleeping && !details){
            gfx->fillRect(HERO_REGION.x,HERO_REGION.y,HERO_REGION.w,HERO_REGION.h,BG);
            paintAnimation();flushRegion(HERO_REGION);
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

void paintStatic(bool linked) {
    gfx->fillScreen(BG);
    gfx->fillCircle(24,24,5,linked?GREEN:RED);
    label(38,13,linked?"Connected":"Disconnected",1);
    bool battery=powerBattery;
    bool usb=powerUSB;
    if(usb){ // Plug icon: distinguish USB power from battery charging.
        gfx->drawFastVLine(289,14,6,GREEN);gfx->drawFastVLine(299,14,6,GREEN);
        gfx->drawRoundRect(287,20,15,10,3,GREEN);gfx->drawFastVLine(294,30,5,GREEN);
    }
    if(bleConnected){
        gfx->drawLine(250,12,250,36,WHITE);gfx->drawLine(250,12,258,20,WHITE);gfx->drawLine(258,20,242,32,WHITE);
        gfx->drawLine(242,16,258,28,WHITE);gfx->drawLine(258,28,250,36,WHITE);
    }
    if(battery){
        int pct=powerPercent;
        gfx->drawRoundRect(316,16,28,16,3,WHITE);gfx->fillRect(344,21,3,6,WHITE);
        gfx->fillRect(319,19,max(0,min(22,pct*22/100)),10,powerCharging?GREEN:WHITE);
        label(359,10,String(pct)+"%",2);
        if(powerCharging){gfx->fillTriangle(327,13,321,25,327,25,PURPLE);gfx->fillTriangle(326,24,332,24,326,35,PURPLE);}
    }else label(319,13,usb?"USB power":"Power unknown",1);
    if(!details){
        uint16_t stateColor=activity=="Error"?RED:activity=="Complete"?GREEN:0xBB5F;
        centered(65,activity,activity=="Needs attention"?3:4,stateColor);
        // A single compact usage section; supporting metrics live behind its touch target.
        gfx->fillRoundRect(30,364,150,29,8,0x3108);
        String badge=plan; if(badge.length()>12)badge=badge.substring(0,11)+"…";
        label(39,370,badge,1,0xC51F);
        String value=available?number(used)+" / "+number(limit):"-- / --";
        label(0,0,"",3);int16_t bx,by;uint16_t bw,bh;gfx->getTextBounds(value,0,0,&bx,&by,&bw,&bh);
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
            int16_t x1,y1;uint16_t w,h;
            // Preserve a readable gap if a large account total needs a smaller font.
            do{label(0,0,"",valueSize);gfx->getTextBounds(values[i],0,0,&x1,&y1,&w,&h);if(w<=286 || valueSize==2)break;valueSize--;}while(true);
            rightLabel(462,ys[i],values[i],valueSize,i==3?RED:WHITE);
            gfx->drawFastHLine(18,ys[i]+43,444,0x39A7);
        }
        label(18,392,stale?"Usage cache stale":"Usage cache fresh",2,MUTED);
        gfx->drawRoundRect(18,425,444,42,9,PURPLE);
        centered(436,"Back to ghost",2);
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
    brightness=constrain(preferences.getInt("brightness",180),5,255);
    sleepMode=preferences.getString("sleep_mode","auto");sleepAfter=preferences.getInt("sleep_after",120);
    panel->setBrightness(brightness);
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
    static unsigned long lastTouchPoll=0;
    if(touchOK && (touchPending || touchDown) && millis()-lastTouchPoll>=40){
        touchPending=false;lastTouchPoll=millis();int16_t tx[5],ty[5];
        bool pressed=touch.getPoint(tx,ty,5)>0;
        if(pressed && !touchDown){
            touchEvents++;lastInteraction=millis();
            if(sleeping)wakeDisplay("touch");
            else if(tx[0]>=18 && tx[0]<=462){
                if(!details && ty[0]>=354 && ty[0]<=461){details=true;draw();}
                else if(details && ty[0]>=425){details=false;draw();}
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
