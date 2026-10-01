"""Local Kirometer setup and explicit PlatformIO operations (no automatic flashing)."""
import argparse
import configparser
import json
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.venv'
PLATFORMIO_VERSION = '6.1.18'


def python_path():
    return ENV / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def execute(command, dry_run=False, cwd=ROOT):
    if dry_run:
        print(json.dumps({'cwd': str(cwd), 'argv': [str(v) for v in command]}))
        return 0
    return subprocess.run([str(v) for v in command], cwd=cwd, check=False).returncode


def local_python():
    path = python_path()
    if not path.is_file():
        raise ValueError('Local environment is missing. Run the setup command first.')
    return path


def setup():
    if sys.version_info < (3, 10):
        raise ValueError('Python 3.10 or newer is required.')
    if not python_path().is_file():
        venv.EnvBuilder(with_pip=True).create(ENV)
    code = execute([local_python(), '-m', 'unittest', '-v', 'test_kirometer', 'test_deployment'])
    if code == 0:
        print('Local usage reader is ready. No background service or firmware was installed.')
    return code


def firmware_command(action, project=None, environment=None, port=None, python=None):
    """Return argv; require an existing project and explicit build environment."""
    command = [str(python or python_path()), '-m', 'platformio']
    if action == 'ports':
        return command + ['device', 'list', '--json-output']
    project = Path(project).expanduser().resolve()
    config_path = project / 'platformio.ini'
    if not config_path.is_file():
        raise ValueError('Firmware project must contain platformio.ini; firmware is not included here.')
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read(config_path)
    if f'env:{environment}' not in config:
        raise ValueError(f'Environment {environment!r} is not declared in platformio.ini.')
    command += ['run', '--project-dir', str(project), '--environment', environment]
    if action == 'flash':
        if not port or port.startswith('-'):
            raise ValueError('Flash requires an explicit serial port, such as COM4 or /dev/cu.usbmodem1101.')
        command += ['--target', 'upload', '--upload-port', port]
    else:
        # Override a project's default targets (which could include upload).
        command += ['--target', 'buildprog']
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('setup', help='Create project-local .venv and run reader/deployment tests')
    run = sub.add_parser('run', help='Print one usage snapshot; no device transport')
    run.add_argument('--db', type=Path)
    run.add_argument('--stale-after', type=int, default=300)
    sub.add_parser('install-firmware-tools', help='Explicitly install pinned PlatformIO into .venv')
    ports = sub.add_parser('ports', help='List serial devices without flashing')
    ports.add_argument('--dry-run', action='store_true')
    for name in ('build', 'flash'):
        firmware = sub.add_parser(name, help=f'{name.capitalize()} a supplied PlatformIO firmware project')
        firmware.add_argument('--project', type=Path, required=True)
        firmware.add_argument('--environment', required=True)
        firmware.add_argument('--dry-run', action='store_true')
        if name == 'flash':
            firmware.add_argument('--port', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'setup':
            return setup()
        if args.command == 'run':
            command = [local_python(), ROOT / 'kirometer.py', '--stale-after', str(args.stale_after)]
            if args.db is not None:
                command += ['--db', args.db]
            return execute(command)
        if args.command == 'install-firmware-tools':
            return execute([local_python(), '-m', 'pip', 'install', f'platformio=={PLATFORMIO_VERSION}'])
        command = firmware_command(args.command, getattr(args, 'project', None),
                                   getattr(args, 'environment', None), getattr(args, 'port', None))
        if not args.dry_run:
            python = local_python()
            if execute([python, '-c', 'import platformio']) != 0:
                raise ValueError('PlatformIO is missing. Run install-firmware-tools first.')
        return execute(command, dry_run=args.dry_run)
    except (ValueError, OSError, configparser.Error) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
