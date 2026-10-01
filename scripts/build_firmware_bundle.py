"""Package explicit PlatformIO flash regions, preserving the NVS partition."""
from pathlib import Path
import hashlib
import json
import shutil
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'firmware/.pio/build/waveshare_amoled_216'
target=ROOT/'crew-app/firmware';target.mkdir(parents=True,exist_ok=True)
version='0.7.0';images=[]
for offset,name in ((0,'bootloader.bin'),(0x8000,'partitions.bin'),(0xe000,'boot_app0.bin'),(0x10000,'firmware.bin')):
    file=target/f'kirometer-{version}-{name}'
    if name=='boot_app0.bin':file.write_bytes((source/'firmware.factory.bin').read_bytes()[0xe000:0x10000])
    else:shutil.copyfile(source/name,file)
    images.append({'offset':hex(offset),'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(target/'firmware.json').write_text(json.dumps({'board':'waveshare-esp32-s3-touch-amoled-2.16','chip':'esp32s3','version':version,'images':images},indent=2)+'\n')
print(f'Packaged {sum((target/i["file"]).stat().st_size for i in images)} bytes in four regions; NVS excluded')
