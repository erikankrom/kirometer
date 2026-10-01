#include <Arduino.h>
#include <ESP_I2S.h>
#include "es8311.h"
#include "notification_sound.h"
#include "notification_audio.h"

static I2SClass audio;
static QueueHandle_t sounds=nullptr;
static void audioTask(void*){
    int preset;
    int16_t pcm[256*2];
    for(;;){
        if(xQueueReceive(sounds,&preset,portMAX_DELAY)!=pdTRUE)continue;
        digitalWrite(46,HIGH);
        int frames=int(NotificationSound::duration(preset)*NotificationSound::sampleRate);
        bool ok=true;
        for(int start=0;start<frames && ok;start+=256){
            int count=min(256,frames-start);
            for(int i=0;i<count;i++)pcm[i*2]=pcm[i*2+1]=NotificationSound::sample(preset,start+i);
            size_t bytes=count*2*sizeof(int16_t);
            ok=audio.write((uint8_t*)pcm,bytes)==bytes;
        }
        // Flush DMA with silence before shutting down the amplifier.
        memset(pcm,0,sizeof(pcm));
        for(int i=0;i<8;i++)audio.write((uint8_t*)pcm,sizeof(pcm));
        digitalWrite(46,LOW);
    }
}
bool beginNotificationAudio(){
    pinMode(46,OUTPUT);digitalWrite(46,LOW);
    audio.setPins(9,45,8,-1,42); // TX only; microphones remain unused.
    if(!audio.begin(I2S_MODE_STD,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO,I2S_STD_SLOT_BOTH))return false;
    auto codec=es8311_create(0,ES8311_ADDRESS_0);
    const es8311_clock_config_t clock={false,false,true,16000*256,16000};
    bool ok=codec && es8311_init(codec,&clock,ES8311_RESOLUTION_16,ES8311_RESOLUTION_16)==ESP_OK
        && es8311_sample_frequency_config(codec,clock.mclk_frequency,clock.sample_frequency)==ESP_OK
        && es8311_microphone_config(codec,false)==ESP_OK
        && es8311_voice_volume_set(codec,65,nullptr)==ESP_OK;
    if(codec)es8311_delete(codec);
    if(!ok){audio.end();return false;}
    sounds=xQueueCreate(1,sizeof(int));
    if(!sounds || xTaskCreate(audioTask,"notification-audio",4096,nullptr,1,nullptr)!=pdPASS){
        if(sounds)vQueueDelete(sounds);sounds=nullptr;audio.end();return false;
    }
    return true;
}
void playNotificationSound(int preset){if(sounds && preset>=0 && preset<5)xQueueOverwrite(sounds,&preset);}
