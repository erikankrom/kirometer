#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

constexpr uint32_t FRAME_INTERVAL_MS = 50;
struct Rect { int x,y,w,h; };
// Fixed animation bounds never intersect the status text or the usage controls.
constexpr Rect HERO_REGION{152,118,176,234};
inline Rect peekRegion(unsigned edge) {
    switch(edge%4) {
        case 0:return {0,176,106,128};
        case 1:return {374,176,106,128};
        case 2:return {176,374,128,106};
        default:return {176,0,128,106};
    }
}
// Main-loop-owned byte queue. Enqueue atomically, retaining newline frame boundaries.
// Notifications consume at most 20 bytes per service call; no reply sleeps the loop.
template<size_t N> class ReplyQueue {
    char bytes[N];size_t head=0,count=0;
public:
    size_t size()const{return count;}
    size_t free()const{return N-count;}
    void clear(){head=count=0;}
    bool push(const char* message,size_t length){
        if(length+1>free())return false;
        for(size_t i=0;i<length;i++)bytes[(head+count+i)%N]=message[i];
        bytes[(head+count+length)%N]='\n';count+=length+1;return true;
    }
    size_t pop(uint8_t* output,size_t capacity){
        size_t n=count<capacity?count:capacity;
        for(size_t i=0;i<n;i++)output[i]=bytes[(head+i)%N];
        head=(head+n)%N;count-=n;return n;
    }
};
