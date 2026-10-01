#include "../firmware/src/render_timing.h"
#include <cassert>
#include "../firmware/src/ghost_motion.h"
#include <set>
#include <limits>
#include "../firmware/src/usage_layout.h"
#include <string>
#include <cmath>
int main(){
    ReplyQueue<64> queue;uint8_t chunk[20];std::string received;
    for(int pass=0;pass<100;pass++){
        assert(queue.push("ack",3));assert(queue.push("status",6));
        while(queue.size()){size_t n=queue.pop(chunk,5);received.append((char*)chunk,n);}
    }
    std::string expected;for(int i=0;i<100;i++)expected+="ack\nstatus\n";
    assert(received==expected);
    assert(!queue.push(std::string(64,'x').data(),64));assert(queue.size()==0);
    assert(queue.push(std::string(63,'x').data(),63));assert(!queue.push("a",1));
    queue.clear();assert(queue.size()==0);assert(queue.free()==64);
    assert(FRAME_INTERVAL_MS==50);
    // All visible rotated sprite pixels are inside their transferable black region.
    for(unsigned edge=0;edge<4;edge++)for(int reveal=0;reveal<=105;reveal++){
        Rect r=peekRegion(edge);
        assert(r.x>=0&&r.y>=0&&r.x+r.w<=480&&r.y+r.h<=480);
        assert(r.w*r.h<=HERO_REGION.w*HERO_REGION.h);
        for(int gy=0;gy<150;gy++)for(int gx=0;gx<123;gx++){
            int x,y;
            if(edge==0){x=-150+reveal+149-gy;y=178+gx;}
            else if(edge==1){x=480-reveal+gy;y=178+122-gx;}
            else if(edge==2){x=178+gx;y=480-reveal+gy;}
            else{x=178+122-gx;y=-150+reveal+149-gy;}
            if(x>=0&&x<480&&y>=0&&y<480)assert(x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h);
        }
    }
    assert(HERO_REGION.y<=122-3 && HERO_REGION.y+HERO_REGION.h>343+5);
    assert(HERO_REGION.y>=118 && HERO_REGION.y+HERO_REGION.h<354);
    // Every status, complete cycles and entrance animations fit the same clear/flush area.
    for(int state=0;state<6;state++){
        std::set<int> poses;std::set<int> heights;bool blink=false;
        for(uint32_t t=0;t<32000;t+=50){
            GhostPose p=ghostPose(static_cast<GhostState>(state),t);
            assert(p.x>=HERO_REGION.x && p.x+156<=HERO_REGION.x+HERO_REGION.w);
            assert(p.y>=HERO_REGION.y && p.y+190<=HERO_REGION.y+HERO_REGION.h);
            poses.insert(static_cast<int>(p.facing));heights.insert(p.y);blink|=p.blink;
        }
        assert(poses.size()>1);assert(heights.size()>1);assert(blink);
    }
    assert(ghostPose(GhostState::Working,2500).facing==Facing::North);
    assert(ghostPose(GhostState::Attention,0).facing==Facing::East);
    assert(ghostPose(GhostState::Error,0).facing==Facing::West);
    assert(ghostPose(GhostState::Complete,2400).facing==Facing::South);
    auto normal=usageBars(true,126,1000,0);
    assert(normal.comparable && normal.includedWidth==51 && normal.overageWidth==0);
    auto extra=usageBars(true,1250,1000,250);
    assert(extra.usedPercent==125 && extra.overagePercent==25);
    assert(extra.includedWidth==408 && extra.overageWidth==102);
    assert(usageBars(true,2500,1000,1500).overageWidth==408);
    assert(!usageBars(true,10,0,10).comparable);
    assert(!usageBars(false,10,100,0).comparable);
    assert(!usageBars(true,std::numeric_limits<float>::quiet_NaN(),100,0).comparable);
    assert(MINI_REGION.x<=25 && MINI_REGION.x+MINI_REGION.w>=25+46);
    assert(MINI_REGION.y<=12 && MINI_REGION.y+MINI_REGION.h>=16+56);
    assert(MINI_REGION.y+MINI_REGION.h<80); // Never touches the plan header.
}
