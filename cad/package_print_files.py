"""Package this enclosure revision, excluding old models and software bundles."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
files=[*ROOT.glob('exports/*.stl'),ROOT/'exports/kirometer-bambu.3mf',*ROOT.glob('exports/*validation.json'),ROOT/'cad/kirometer-enclosure.blend']
files += [ROOT/'cad'/n for n in ['build_enclosure.py','review_enclosure.py','build_print_project.py','prepare_bambu_presets.py','split_bambu_plates.py','verify_stl.py','verify_3mf.py','package_print_files.py']]
files += [ROOT/'docs'/n for n in ['printing-and-fit.md','enclosure-revision-plan.md','makerworld-draft.md']]
files += [ROOT/'previews'/n for n in ['kirometer-enclosure.png','kirometer-rear.png','kirometer-button-access.png','kirometer-exploded.png']]
files += [ROOT/'previews/assets/kiro-ghost'/n for n in ['south.png','LICENSE','SOURCE.md']]
revision=json.loads((ROOT/'exports/geometry-validation.json').read_text())['parameters_mm'].get('revision','v7')
manifest={'revision':revision,'files':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'physical_fit_verified':False}
with zipfile.ZipFile(ROOT/'exports/kirometer-print-package.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,str(f.relative_to(ROOT)))
 z.writestr('manifest.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(ROOT/'exports/kirometer-print-package.zip') as z:
 assert z.testzip() is None
 assert not any('top-button' in n for n in z.namelist())
print('Packaged',revision)
