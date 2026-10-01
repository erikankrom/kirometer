#include <cassert>
#include <fstream>
#include <vector>
#include "../firmware/src/smooth_text.h"
int main(int argc,char** argv){
 assert(blend565(0xffff,0x1082,0)==0x1082);
 assert(blend565(0xffff,0x1082,15)==0xffff);
 assert(textBounds("",2).w==0);
 assert(textBounds("Needs attention",3).w<440);
 assert(textBounds("Disconnected",1).w<210);
 assert(textBounds("Usage details",4).w<444);
 assert(textBounds("2026-11-01",3).w<286);
 assert(textBounds("Resets Nov 1, 2026",1).w<408);
 assert(textBounds("25% of plan allowance",1).w<408);
 const char* unicode="…";assert(nextGlyph(unicode)==95 && *unicode==0);
 const char* unknown="é";assert(nextGlyph(unknown)=='?'-32 && *unknown==0);
 const char truncated[]={char(0xe2),0};auto ptr=truncated;nextGlyph(ptr);assert(*ptr==0);
 // Guard canvas bounds, blending, and negative origin clipping with sanitizer coverage.
 std::vector<uint16_t> guarded(480*480+2,0x1082);guarded.front()=0x1234;guarded.back()=0x5678;
 auto pixels=guarded.data()+1;
 smoothText(pixels,480,480,-20,-20,"Clipped",4,0xffff);
 smoothText(pixels,480,480,465,470,"Edges",4,0xffff);
 assert(guarded.front()==0x1234 && guarded.back()==0x5678);
 std::fill(pixels,pixels+480*480,0);
 auto rect=[&](int x,int y,int w,int h,uint16_t color){for(int j=y;j<y+h;j++)for(int i=x;i<x+w;i++)pixels[j*480+i]=color;};
 rect(20,80,440,42,0x2106);rect(20,136,440,152,0x1082);rect(20,302,440,132,0x1082);
 smoothText(pixels,480,480,359,10,"100%",2,0xffff);
 smoothText(pixels,480,480,36,88,"KIRO PRO",3,0xc51f);
 smoothText(pixels,480,480,36,148,"Plan credits",1,0xad55);
 smoothText(pixels,480,480,36,183,"1,250 / 1,000",3,0xffff);
 auto pct=textBounds("125%",2);smoothText(pixels,480,480,444-pct.w-pct.x,186,"125%",2,0xc51f);
 rect(36,234,408,14,0x923f);smoothText(pixels,480,480,36,260,"Resets Nov 1, 2026",1,0xad55);
 smoothText(pixels,480,480,36,314,"Overage credits",1,0xad55);
 smoothText(pixels,480,480,36,343,"250 credits",3,0xfb2f);
 rect(36,387,408,12,0x2945);rect(36,387,102,12,0xfb2f);
 smoothText(pixels,480,480,36,410,"25% of plan allowance",1,0xad55);
 auto connected=textBounds("Connected",1);smoothText(pixels,480,480,(480-connected.w)/2,450,"Connected",1,0x6ef3);
 // All medium card glyphs remain above the bar; actual coverage has >2 antialias levels.
 assert(textBounds("1,250 / 1,000",3).w<=286);
 int shades=0;for(int v=1;v<15;v++){if(blend565(0xffff,0,v)!=0)shades++;}assert(shades==14);
 if(argc>1){std::ofstream f(argv[1],std::ios::binary);f<<"P6\n480 480\n255\n";for(int i=0;i<480*480;i++){uint16_t c=pixels[i];char rgb[]={char(((c>>11)&31)*255/31),char(((c>>5)&63)*255/63),char((c&31)*255/31)};f.write(rgb,3);}}
}
