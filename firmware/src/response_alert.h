#pragma once
#include <cstring>
#include <cstdio>
// Boot/reconnect establishes a silent baseline; no notification history in NVS.
struct ResponseAlert {
    char seen[65]={};
    bool observe(const char* event,bool baseline,bool enabled,bool needsResponse){
        if(!event || strlen(event)>64)return false;
        bool changed=strcmp(seen,event)!=0;
        snprintf(seen,sizeof(seen),"%s",event);
        return changed && event[0] && !baseline && enabled && needsResponse;
    }
};
