#pragma once
#include <cmath>
struct UsageBars { float usedPercent, overagePercent; int includedWidth, overageWidth; bool comparable; };
inline UsageBars usageBars(bool available,float used,float limit,float overage,int width=408){
    if(!available || !std::isfinite(used) || !std::isfinite(limit) || !std::isfinite(overage) || limit<=0)return {0,0,0,0,false};
    float included=used<0?0:used/limit,extra=overage<0?0:overage/limit;
    return {included*100,extra*100,int((included>1?1:included)*width),int((extra>1?1:extra)*width),true};
}
