#pragma once
#include <stdint.h>
struct SessionActivity {
    bool available=false, stale=true, incomplete=false;
    int32_t today=0, messages=0, tools=0, week=0, month=0;
};
