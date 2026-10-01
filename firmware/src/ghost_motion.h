#pragma once
#include <stdint.h>
#include <math.h>
enum class GhostState { Ready, Working, Attention, Complete, Error, Unknown };
enum class Facing { South, East, North, West };
struct GhostPose { Facing facing; int x,y; bool blink; };
// Deterministic state-local time also restarts each entrance animation.
inline GhostPose ghostPose(GhostState state,uint32_t elapsed) {
    GhostPose p{Facing::South,162,133,false};
    const float tau=6.283185307f;
    p.y+=lroundf(sinf((elapsed%4000)*tau/4000)*3);
    p.blink=elapsed%5000>=4750;
    switch(state){
        case GhostState::Working:{
            unsigned phase=elapsed%6000;
            p.facing=phase<450?Facing::South:phase<2200?Facing::East:phase<3000?Facing::North:phase<4750?Facing::West:Facing::South;
            p.x+=lroundf(sinf(phase*tau/6000)*10);
            p.y+=lroundf(sinf((elapsed%1200)*tau/1200)*5);
            break;
        }
        case GhostState::Attention:{
            unsigned phase=elapsed%4800;
            p.facing=phase<800?Facing::East:phase<1600?Facing::West:Facing::South;
            p.y-=phase<1600?3:0;
            p.blink=phase>=3800&&phase<4050;
            break;
        }
        case GhostState::Complete:{
            if(elapsed<2000)p.facing=static_cast<Facing>((elapsed/400)%4);
            unsigned phase=elapsed%6000;
            if(phase<1800)p.y-=lroundf(fabsf(sinf(phase*tau/1800))*11);
            break;
        }
        case GhostState::Error:{
            unsigned phase=elapsed%5000;
            if(phase<900){
                p.x+=lroundf(sinf(phase*tau/300)*7);
                p.facing=(phase/300)%2?Facing::East:Facing::West;
            }
            break;
        }
        case GhostState::Unknown:
            p.facing=static_cast<Facing>((elapsed/1600)%4);
            break;
        case GhostState::Ready:{
            unsigned phase=elapsed%16000;
            if(phase>=11000&&phase<12000)p.facing=Facing::East;
            if(phase>=12000&&phase<13000)p.facing=Facing::West;
            break;
        }
    }
    return p;
}
