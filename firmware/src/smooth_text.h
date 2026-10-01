#pragma once
#include <algorithm>
#include <cstring>
#include "fonts/space_grotesk.h"

inline const SmoothFont& screenFont(int size){return size>=4?space48:size==3?space36:size==1?space20:space24;}
// ASCII UI labels plus an ellipsis; unsupported UTF-8 becomes one '?' per codepoint.
inline unsigned nextGlyph(const char*& p){
    unsigned char c=*p++;
    if(c>=32 && c<=126)return c-32;
    if(c==0xE2 && static_cast<unsigned char>(p[0])==0x80 && static_cast<unsigned char>(p[1])==0xA6){p+=2;return 95;}
    while((static_cast<unsigned char>(*p)&0xC0)==0x80)++p;
    return '?'-32;
}
struct TextBounds {int x=0,y=0,w=0,h=0;};
inline TextBounds textBounds(const char* text,int size){
    const auto& font=screenFont(size); int pen=0,left=0,right=0,top=0,bottom=0;bool ink=false;
    while(*text){const auto& g=font.glyphs[nextGlyph(text)];
        if(g.width && g.height){int x=pen+g.left;
            if(!ink){left=x;right=x+g.width;top=g.top;bottom=g.top+g.height;ink=true;}
            else{left=std::min(left,x);right=std::max(right,x+g.width);top=std::min(top,int(g.top));bottom=std::max(bottom,g.top+g.height);}}
        pen+=g.advance;
    }
    return {left,top,right-left,bottom-top};
}
inline uint16_t blend565(uint16_t fg,uint16_t bg,unsigned coverage){
    unsigned inverse=15-coverage;
    unsigned r=(((fg>>11)&31)*coverage+((bg>>11)&31)*inverse+7)/15;
    unsigned g=(((fg>>5)&63)*coverage+((bg>>5)&63)*inverse+7)/15;
    unsigned b=((fg&31)*coverage+(bg&31)*inverse+7)/15;
    return (r<<11)|(g<<5)|b;
}
// Blend onto the existing canvas, so glyph edges match black and tinted card surfaces.
inline void smoothText(uint16_t* canvas,int width,int height,int x,int y,const char* text,int size,uint16_t color){
    const auto& font=screenFont(size);int baseline=y+font.baseline;
    while(*text){const auto& g=font.glyphs[nextGlyph(text)];
        for(int row=0;row<g.height;row++)for(int col=0;col<g.width;col++){
            int px=x+g.left+col,py=baseline+g.top+row;
            if(px<0 || py<0 || px>=width || py>=height)continue;
            unsigned index=row*g.width+col,packed=font.pixels[g.offset+index/2];
            unsigned alpha=(index&1)?packed&15:packed>>4;
            if(alpha){auto& pixel=canvas[py*width+px];pixel=blend565(color,pixel,alpha);}
        }
        x+=g.advance;
    }
}
