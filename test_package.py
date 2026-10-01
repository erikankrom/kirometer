import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.package_crew_app import build,package_files

class PackageTests(unittest.TestCase):
    def test_clean_runtime_and_registry_are_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/'app.zip',root/'registry','https://github.com/example/kirometer')
            entries=json.loads((root/'registry/app-registry.json').read_text())
            app_root=root/'registry'/entries[0]['subdirectory']
            self.assertEqual(json.loads((app_root/'app.json').read_text())['name'],entries[0]['name'])
            with zipfile.ZipFile(root/'app.zip') as z:
                names=z.namelist()
                self.assertTrue(all(not any(p in n for p in ('__pycache__','.app_secret','installed.json','/data/')) for n in names))
                self.assertIn('kirometer/firmware/GHOST-LICENSE',names)
                self.assertIn('kirometer/ui/layouts.mjs',names)
                self.assertNotIn('kirometer/ui/art/banner-light.svg',names)
                for n in names:self.assertEqual(z.read(n),(app_root/n.removeprefix('kirometer/')).read_bytes())
            build(root/'second.zip')
            self.assertEqual((root/'app.zip').read_bytes(),(root/'second.zip').read_bytes())

    def test_registry_rejects_credentialed_or_invalid_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):build(root/'app.zip',root/'registry','https://user:password@github.com/example/repo')
