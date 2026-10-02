"""Build a runtime-only ZIP and optional Crew remote registry tree. No local state."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def package_files():
    source=ROOT/'crew-app'
    app=json.loads((source/'app.json').read_text())
    manifest=json.loads((source/'firmware/firmware.json').read_text())
    files={Path('app.json'),Path('README.md'),Path('CHANGELOG.md'),Path('ui/index.mjs'),Path('ui/custom-faces.mjs'),Path('ui/layouts.mjs'),Path('ui/gallery-screens.mjs'),Path('ui/animated-preview.mjs'),Path('ui/animation-assets.mjs'),Path('ui/icons.mjs'),Path('vendor/checksums.json'),Path('firmware/firmware.json')}
    files.update(p.relative_to(source) for p in (source/'backend').glob('*.py'))
    files.update((Path('ui/firmware-history.mjs'),Path('ui/app-icon.mjs'),Path('ui/art/icon-crew.svg')))
    files.update(p.relative_to(source) for p in (source/'ui/art/icons').iterdir() if p.is_file())
    for key in ('iconPath','iconPathDark','heroImage','heroImageDark','heroImageDetail','heroImageDetailDark'):
        files.add(Path(app[key]))
    files.update(Path(p) for key in ('screenshots','screenshotsDark') for p in app[key])
    files.update(p.relative_to(source) for p in (source/'ui/art').glob('layout-*.png'))
    files.update((Path('ui/art/layout-ghost.svg'),Path('ui/art/layout-usage.svg'),Path('ui/art/SOURCES.md'),Path('ui/art/kiro-official.svg')))
    for image in manifest['images']:
        path=source/'firmware'/image['file']
        if path.parent!=source/'firmware':raise ValueError('Invalid firmware path')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=image['sha256']:raise ValueError(f'Firmware checksum mismatch: {path.name}')
        files.add(path.relative_to(source))
    for name,digest in json.loads((source/'vendor/checksums.json').read_text()).items():
        path=source/'vendor/wheels'/name
        if path.parent!=source/'vendor/wheels':raise ValueError('Invalid wheel path')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError(f'Wheel checksum mismatch: {name}')
        files.add(path.relative_to(source))
    result={}
    for rel in sorted(files):
        path=source/rel
        if '..' in rel.parts or rel.is_absolute() or path.is_symlink():raise ValueError(f'Unsafe package path: {rel}')
        result[rel]=path.read_bytes()
    result[Path('LICENSE')]=(ROOT/'LICENSE').read_bytes()
    result[Path('firmware/FONT-LICENSE.txt')]=(ROOT/'firmware/assets/fonts/OFL.txt').read_bytes()
    result[Path('firmware/FONT-SOURCE.md')]=(ROOT/'firmware/assets/fonts/SOURCES.md').read_bytes()
    result[Path('firmware/ICON-LICENSE.txt')]=(ROOT/'crew-app/ui/art/icons/LUCIDE-LICENSE').read_bytes()
    for name in ('GHOST-LICENSE','GHOST-SOURCE.md'):
        result[Path('firmware')/name]=(ROOT/'firmware'/name).read_bytes()
    return app,manifest,result

def build(output,registry=None,repo=None):
    app,firmware,files=package_files()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path,data in files.items():
            info=zipfile.ZipInfo('kirometer/'+path.as_posix(),(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    if registry:
        if not repo or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
            raise ValueError('--repo must be an HTTPS GitHub repository URL without credentials or query')
        if registry.exists():raise ValueError('Registry destination must be new to prevent stale files')
        for path,data in files.items():
            dest=registry/'apps/kirometer'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        entry=[{'name':'kirometer','gitUrl':repo,'branch':'crew-release','subdirectory':'apps/kirometer'}]
        (registry/'app-registry.json').write_text(json.dumps(entry,indent=2)+'\n')
        (registry/'LICENSE').write_bytes((ROOT/'LICENSE').read_bytes())
        (registry/'README.md').write_text('# Kirometer release channel\n\nAdd this repository as a Crew external registry using branch `crew-release`. Runtime files in `apps/kirometer` are generated from a published release.\n')
    print(f'{output}: app {app["version"]}, firmware {firmware["version"]}, {output.stat().st_size} bytes, {len(files)} files')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'exports/kirometer-crew-app.zip')
    parser.add_argument('--registry-dir',type=Path)
    parser.add_argument('--repo')
    args=parser.parse_args();build(args.output,args.registry_dir,args.repo)
