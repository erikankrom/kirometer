#pragma once
#include <cstring>
#include <cstdlib>
#include <stdint.h>
#include "render_timing.h"
inline constexpr const char* FACE_IDS[]={"orbit","sidekick","ticket","big_number"};
inline constexpr const char* FACE_NAMES[]={"Orbit","Sidekick","Credit ticket","The big number"};
inline int faceIndex(const char* id){for(int i=0;i<4;i++)if(!strcmp(id,FACE_IDS[i]))return i;return -1;}
inline constexpr const char* ALL_FACE_IDS[]={"ghost","usage","orbit","sidekick","ticket","big_number"};
inline constexpr const char* ALL_FACE_NAMES[]={"Ghost companion","Usage dashboard","Orbit","Sidekick","Credit ticket","The big number"};
inline int allFaceIndex(const char* id){for(int i=0;i<6;i++)if(!strcmp(id,ALL_FACE_IDS[i]))return i;return -1;}
inline bool validLayout(const char* id){return faceIndex(id)>=0 || !strcmp(id,"ghost") || !strcmp(id,"usage");}
inline const char* nextFace(const char* id,int direction){int i=allFaceIndex(id);return ALL_FACE_IDS[i<0?0:(i+direction+6)%6];}
inline Rect faceRegion(const char* id){
 switch(faceIndex(id)){case 0:return {187,95,108,126};case 1:return {295,113,130,155};case 2:return {316,88,108,130};case 3:return {350,263,84,94};}
 return !strcmp(id,"usage")?MINI_REGION:HERO_REGION;
}
enum class Gesture {None,Tap,Next,Previous};
// Interpret only after release. A drag never triggers the underlying tap target.
class TouchGesture {
 int startX=0,startY=0,lastX=0,lastY=0,maxTravel=0;uint32_t since=0;bool active=false,ignored=false;
public:
 void begin(int x,int y,uint32_t now,bool wakeOnly){startX=lastX=x;startY=lastY=y;since=now;maxTravel=0;active=true;ignored=wakeOnly;}
 void move(int x,int y){if(!active)return;lastX=x;lastY=y;int d=std::abs(x-startX)+std::abs(y-startY);if(d>maxTravel)maxTravel=d;}
 Gesture end(uint32_t now){if(!active)return Gesture::None;active=false;if(ignored)return Gesture::None;
   int dx=lastX-startX,dy=lastY-startY;uint32_t duration=now-since;
   if(duration<=1500 && std::abs(dx)>=64 && std::abs(dx)>std::abs(dy)*2)return dx<0?Gesture::Next:Gesture::Previous;
   if(duration<=800 && maxTravel<=18)return Gesture::Tap;
   return Gesture::None;
 }
 int x()const{return startX;}int y()const{return startY;}
};
