#pragma once
#include <cmath>
#include <cstring>
#include <cstdint>

// Crew sine presets and envelope; provenance in docs/notification-sounds.md.
namespace NotificationSound {
constexpr int sampleRate=16000;
struct Note {float hz,start,duration,gain;};
struct Preset {const char* name; Note notes[4];int count;float gain;};
constexpr Preset presets[]={
    {"chime",{{1047,0,.3,1},{1319,.15,.35,1},{1568,.3,.4,.85}},3,.89},
    {"ding",{{1760,0,.45,1}},1,.98},
    {"blip",{{880,0,.08,1}},1,.98},
    {"pop",{{220,0,.12,.9}},1,.98},
    {"pulse",{{660,0,.12,1},{880,.15,.12,1},{660,.3,.12,.9},{880,.45,.12,.9}},4,.98}
};
inline int index(const char* name){for(int i=0;i<5;i++)if(!strcmp(name,presets[i].name))return i;return -1;}
inline float duration(int p){float end=0;for(int n=0;n<presets[p].count;n++)end=fmaxf(end,presets[p].notes[n].start+presets[p].notes[n].duration);return end;}
inline int16_t sample(int p,int frame){
    float t=float(frame)/sampleRate,value=0;
    for(int i=0;i<presets[p].count;i++){
        const auto& n=presets[p].notes[i];float age=t-n.start;
        if(age<0 || age>=n.duration)continue;
        float envelope;
        if(age<.005f){float x=age/.005f;envelope=x*x*(3-2*x);}
        else if(age>n.duration-.005f){float x=(age-(n.duration-.005f))/.005f;envelope=.01f*(1-x*x*(3-2*x));}
        else envelope=expf(logf(.01f)*(age-.005f)/(n.duration-.01f));
        value+=sinf(6.28318530718f*n.hz*age)*envelope*n.gain*presets[p].gain;
    }
    // Crew's default 35% volume curve, with headroom for overlapping notes.
    value*=powf(.35f,1.5f)*.5f;
    return int16_t(fmaxf(-1,fminf(1,value))*32767);
}
}
