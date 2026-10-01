#include "../firmware/src/notification_sound.h"
#include "../firmware/src/response_alert.h"
#include <cassert>
#include <algorithm>
#include <cstdlib>
int main(){
    ResponseAlert alert;
    assert(!alert.observe("old",true,true,true));
    assert(!alert.observe("old",false,true,true));
    assert(alert.observe("new",false,true,true));
    assert(!alert.observe("new",false,true,true));
    assert(!alert.observe("muted",false,false,true));
    assert(!alert.observe("muted",false,true,true));
    assert(!alert.observe("completed",false,true,false));
    assert(!alert.observe("reconnect",true,true,true));
    assert(alert.observe("another",false,true,true));
    assert(NotificationSound::index("invalid")==-1);
    for(int p=0;p<5;p++){
        assert(NotificationSound::index(NotificationSound::presets[p].name)==p);
        int frames=int(NotificationSound::duration(p)*NotificationSound::sampleRate),peak=0;
        assert(frames>0 && frames<=11200);
        assert(NotificationSound::sample(p,0)==0);
        for(int f=0;f<frames;f++)peak=std::max(peak,std::abs(int(NotificationSound::sample(p,f))));
        assert(peak>100 && peak<16000); // audible nonzero PCM with ample headroom
        assert(NotificationSound::sample(p,frames+1)==0);
    }
}
