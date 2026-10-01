import tempfile
from pathlib import Path
import unittest

from kirometer import default_db
from scripts.deploy import firmware_command


class DeploymentTests(unittest.TestCase):
    def test_platform_cache_locations(self):
        self.assertEqual(default_db('darwin', {}, '/home/user'), Path('/home/user/Library/Application Support/Kiro/User/globalStorage/state.vscdb'))
        self.assertEqual(default_db('win32', {'APPDATA': '/roaming/user'}, '/home/user'), Path('/roaming/user/Kiro/User/globalStorage/state.vscdb'))
        self.assertEqual(default_db('win32', {}, '/home/user'), Path('/home/user/AppData/Roaming/Kiro/User/globalStorage/state.vscdb'))

    def test_build_and_flash_are_distinct_and_paths_are_not_shell_strings(self):
        with tempfile.TemporaryDirectory(prefix='firmware project ') as directory:
            project = Path(directory)
            (project / 'platformio.ini').write_text('[env:amoled]\nplatform = espressif32\ntargets = upload\n')
            build = firmware_command('build', project, 'amoled', python='/python')
            self.assertNotIn('upload', build)
            self.assertEqual(build[-2:], ['--target', 'buildprog'])
            self.assertIn(str(project.resolve()), build)
            flash = firmware_command('flash', project, 'amoled', 'COM4', python='/python')
            self.assertEqual(flash[-4:], ['--target', 'upload', '--upload-port', 'COM4'])
            with self.assertRaises(ValueError):
                firmware_command('flash', project, 'amoled')
            with self.assertRaises(ValueError):
                firmware_command('build', project, 'unknown')

    def test_missing_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                firmware_command('build', directory, 'amoled')


if __name__ == '__main__':
    unittest.main()
