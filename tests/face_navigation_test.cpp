#include <cassert>
#include <cstring>
#include "../firmware/src/face_navigation.h"
#include "../firmware/src/smooth_text.h"
int main(){
 assert(!strcmp(nextFace("orbit",-1),"usage"));
 assert(!strcmp(nextFace("big_number",1),"ghost"));
 assert(!strcmp(nextFace("usage",1),"orbit"));
 assert(!strcmp(nextFace("ghost",-1),"big_number"));
 for(auto id:ALL_FACE_IDS){assert(validLayout(id));auto r=faceRegion(id);assert(r.x>=0&&r.y>=0&&r.x+r.w<=480&&r.y+r.h<=480);assert(r.w*r.h<=HERO_REGION.w*HERO_REGION.h);}
 assert(!validLayout("unknown-face"));
 TouchGesture g;
 g.begin(300,200,100,false);g.move(100,215);assert(g.end(600)==Gesture::Next);
 g.begin(100,200,100,false);g.move(300,205);assert(g.end(600)==Gesture::Previous);
 g.begin(100,200,100,false);g.move(109,205);assert(g.end(300)==Gesture::Tap);
 g.begin(100,200,100,false);g.move(105,400);assert(g.end(600)==Gesture::None);
 g.begin(100,200,100,false);g.move(300,205);g.move(100,200);assert(g.end(600)==Gesture::None);
 g.begin(300,200,100,true);g.move(100,215);assert(g.end(600)==Gesture::None);
 g.begin(100,200,100,false);assert(g.end(2000)==Gesture::None);
 assert(g.end(2001)==Gesture::None);
 g.begin(300,200,0xfffffff0,false);g.move(100,215);assert(g.end(100)==Gesture::Next);
 assert(textBounds("874",7).w<424);
 assert(textBounds("125%",5).w<400);
 assert(textBounds("1,250",6).w<222);
 assert(textBounds("Connected - stale",1).w<260);
}
