"""Rebuild the three-plate P1S project from validated STLs on macOS.
Run Blender build_enclosure.py and review_enclosure.py first.
"""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
def run(*args):
 subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
run(sys.executable,ROOT/'cad/verify_stl.py')
run(sys.executable,ROOT/'cad/prepare_bambu_presets.py')
presets=Path('/tmp/kirometer-presets')
with tempfile.TemporaryDirectory(prefix='kirometer-print-') as tmp:
 tmp=Path(tmp);raw=tmp/'raw.3mf';plates=tmp/'plates.3mf'
 # Load both filaments through Bambu so all nozzle-variant arrays are complete.
 run(BAMBU,'--load-settings',f'{presets}/machine.json;{presets}/process.json',
     '--load-filaments',f'{presets}/filament.json;{presets}/filament.json',
     '--load-filament-ids','1,1,2','--orient','0','--arrange','1','--export-3mf',raw,
     ROOT/'exports/kirometer-fit-coupon.stl',ROOT/'exports/kirometer-ghost-body.stl',ROOT/'exports/kirometer-rear-cover.stl')
 run(sys.executable,ROOT/'cad/split_bambu_plates.py',raw,plates)
 run(BAMBU,'--orient','0','--arrange','0','--slice','0','--outputdir',tmp,
     '--export-3mf','kirometer-bambu.3mf',plates)
 result=json.loads((tmp/'result.json').read_text());assert result['return_code']==0
 assert len(result['sliced_plates'])==3
 for plate in result['sliced_plates']:
  assert not plate['warning_message'],plate['warning_message']
  assert not any('support' in k.lower() and v>0 for k,v in plate['feature_type_times'].items())
 shutil.copy2(tmp/'kirometer-bambu.3mf',ROOT/'exports/kirometer-bambu.3mf')
 shutil.copy2(tmp/'result.json',ROOT/'exports/bambu-slice-validation.json')
print('Rebuilt exports/kirometer-bambu.3mf; supports off; three plates sliced.')
