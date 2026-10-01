#include "../firmware/src/ghost_motion.h"
#include <cstdio>
int main(){printf("[");for(int state=0;state<6;state++){if(state)printf(",");printf("[");for(unsigned t=0;t<16000;t+=50){auto p=ghostPose(static_cast<GhostState>(state),t);if(t)printf(",");printf("[%d,%d,%d,%d]",int(p.facing),p.x,p.y,int(p.blink));}printf("]");}printf("]");}
