#pragma once
#include <string>
#include <vector>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <fstream>
#include "smooth_text.h"
#include "face_navigation.h"
#include "ghost_poses.h"
#include "ghost_motion.h"
#include "usage_layout.h"
#include "lucide_icons.h"
using std::min;using std::max;
constexpr float PI=3.14159265358979323846f;
template<typename T>T constrain(T x,T lo,T hi){return min(hi,max(lo,x));}
struct String:std::string{
 using std::string::string;String(const std::string& s):std::string(s){}
 String(int value):std::string(std::to_string(value)){}
 String(float value,int decimals){char b[64];snprintf(b,sizeof(b),"%.*f",decimals,value);assign(b);}
};
struct PreviewCanvas{
 std::vector<uint16_t> pixels=std::vector<uint16_t>(480*480);
 uint16_t* getFramebuffer(){return pixels.data();}
 void drawPixel(int x,int y,uint16_t color){if(x>=0&&x<480&&y>=0&&y<480)pixels[y*480+x]=color;}
 void fillRect(int x,int y,int w,int h,uint16_t c){for(int j=y;j<y+h;j++)for(int i=x;i<x+w;i++)drawPixel(i,j,c);}
 void fillCircle(int x,int y,int r,uint16_t c){for(int j=-r;j<=r;j++)for(int i=-r;i<=r;i++)if(i*i+j*j<=r*r)drawPixel(x+i,y+j,c);}
 void fillRoundRect(int x,int y,int w,int h,int r,uint16_t c){for(int j=0;j<h;j++)for(int i=0;i<w;i++){int dx=max(0,max(r-i,i-(w-1-r))),dy=max(0,max(r-j,j-(h-1-r)));if(dx*dx+dy*dy<=r*r)drawPixel(x+i,y+j,c);}}
 void drawFastVLine(int x,int y,int h,uint16_t c){fillRect(x,y,1,h,c);}
 void drawFastHLine(int x,int y,int w,uint16_t c){fillRect(x,y,w,1,c);}
};
static constexpr uint16_t BG=0,WHITE=0xffff,PURPLE=0x923f,RED=0xfb2f,MUTED=0xad55,GREEN=0x6ef3;
PreviewCanvas screen;auto gfx=&screen;
bool powerUSB=false,powerBattery=true,powerCharging=false,bleConnected=true,available=true,stale=false;
int powerPercent=85;uint32_t frameNow=1000,stateSince=0;
float used=126,limit=1000,overage=0;
String screenLayout="orbit",activity="Ready",plan="KIRO PRO";
String number(float n){return String(n,n==floor(n)?0:1);}
String resetLabel(){return available?"Resets Nov 1, 2026":"Reset date unavailable";}
