"""Host-render the actual firmware face functions for gallery previews and visual QA.
Uses the firmware's baked glyphs, icon coverage, and sprites with a small software canvas.
Only rounded-rectangle edges use the host canvas approximation; metrics/layout code is shared.
"""
from pathlib import Path
import re,subprocess,tempfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'firmware/src/main.cpp').read_text()
names=['label','centered','rightLabel','fittedLabel','lucide','powerIcons','faceFooter','faceBar','faceGauge','compactFaceGhost','paintFace','paintSessionDetails']
functions=[]
for name in names:
 match=re.search(r'void '+name+r'\([^;{}]*\)\s*\{',source)
 if not match:raise ValueError(name)
 start=match.start();pos=match.end();depth=1
 while depth:
  if source[pos]=='{':depth+=1
  elif source[pos]=='}':depth-=1
  pos+=1
 functions.append(source[start:pos])
main=r'''
int main(int argc,char** argv){
 for(int scenario=0;scenario<5;scenario++){
  sessionStats=SessionActivity{};sessionStats.available=scenario!=2;sessionStats.stale=scenario==1;sessionStats.incomplete=scenario==3;
  sessionStats.today=scenario==4?2147483647:19;sessionStats.messages=scenario==4?2147483647:22;sessionStats.tools=scenario==4?2147483647:6;sessionStats.week=scenario==4?2147483647:23;sessionStats.month=scenario==4?2147483647:19;
  screen.fillRect(0,0,480,480,0);paintSessionDetails();
  std::ofstream out(std::string(argv[1])+"/session-activity-"+std::to_string(scenario)+".ppm",std::ios::binary);out<<"P6\n480 480\n255\n";
  for(auto color:screen.pixels){char rgb[]={char(((color>>11)&31)*255/31),char(((color>>5)&63)*255/63),char((color&31)*255/31)};out.write(rgb,3);}
 }

 for(int scenario=0;scenario<4;scenario++)for(auto face:FACE_IDS){
  available=scenario!=2;used=scenario==1?1250:scenario==3?0:126;overage=scenario==1?250:0;screenLayout=face;
  screen.fillRect(0,0,480,480,0);paintFace(scenario!=2);compactFaceGhost();
  std::string path=std::string(argv[1])+"/"+face+"-"+std::to_string(scenario)+".ppm";
  std::ofstream out(path,std::ios::binary);out<<"P6\n480 480\n255\n";
  for(auto color:screen.pixels){char rgb[]={char(((color>>11)&31)*255/31),char(((color>>5)&63)*255/63),char((color&31)*255/31)};out.write(rgb,3);}
 }
}
'''
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'Arduino.h').write_text('#pragma once\n#include <stdint.h>\n#define PROGMEM\n');cpp=tmp/'render.cpp';cpp.write_text('#include "face_preview_support.h"\n'+'\n'.join(functions)+main)
 subprocess.run(['c++','-std=c++17','-I'+temp,'-I'+str(ROOT/'tests'),'-I'+str(ROOT/'firmware/src'),str(cpp),'-o',str(tmp/'render')],check=True)
 subprocess.run([str(tmp/'render'),temp],check=True)
 outdir=ROOT/'previews/firmware-faces';outdir.mkdir(exist_ok=True)
 for file in tmp.glob('*.ppm'):
  im=Image.open(file);im.save(outdir/(file.stem+'.png'))
  if file.stem.endswith('-0') and not file.stem.startswith('session-activity'):im.save(ROOT/'crew-app/ui/art'/('layout-'+file.stem[:-2]+'.png'))
 print('Rendered firmware faces, gallery thumbnails, and five Session Activity cases')
