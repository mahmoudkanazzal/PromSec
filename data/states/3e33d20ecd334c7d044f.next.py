from __future__ import print_function
import os
import sys
import argparse
import hashlib
import shutil
import datetime
import tempfile
import re
import tarfile
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    parser.add_argument('--src', required=True, help='Source directory to back up')
    parser.add_argument('--dest', required=True, help='Destination path (local or remote, e.g. user@host:/path)')
    parser.add_argument('--compress', action='store_true', help='Compress the archive')
    parser.add_argument('--keep-temp', action='store_true', help='Do not delete temporary files')
    return parser.parse_args()

def make_temp_path(compress):
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    ext = '.tar.gz' if compress else '.tar'
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    path = tf.name
    tf.close()
    return path

def create_archive(src, temp_path, compress):
    mode = 'w:gz' if compress else 'w'
    try:
        with tarfile.open(temp_path, mode) as tar:
            tar.add(src, arcname='.')
    except Exception as e:
        print('Error creating archive:', e, file=sys.stderr)
        sys.exit(1)

def compute_checksum(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def _is_safe_destination(dest):
    # Allow alphanumerics, underscore, hyphen, dot, at, colon, slash
    return bool(re.fullmatch(r'[A-Za-z0-9_.@:/-]+', dest))

def copy_to_destination(temp_path, dest):
    if not _is_safe_destination(dest):
        print('Invalid destination path:', dest, file=sys.stderr)
        sys.exit(1)

    if ':' in dest:
        # remote copy via scp
        cmd = ['scp', temp_path, dest]
    else:
        # local copy
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            shutil.copy2(temp_path, dest)
            return
        except OSError as e:
            print('Error copying to destination:', e, file=sys.stderr)
            sys.exit(1)

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print('Error copying to destination:', e.stderr.decode() if e.stderr else str(e), file=sys.stderr)
        sys.exit(1)

def cleanup_temp(temp_path):
    try:
        os.remove(temp_path)
    except OSError:
        pass

def main():
    args = parse_args()
    src = os.path.abspath(args.src)
    if not os.path.isdir(src):
        print('Source directory does not exist:', src, file=sys.stderr)
        sys.exit(1)
    temp_path = make_temp_path(args.compress)
    create_archive(src, temp_path, args.compress)
    checksum = compute_checksum(temp_path)
    print('Archive created at:', temp_path)
    print('SHA256 checksum:', checksum)
    copy_to_destination(temp_path, args.dest)
    print('Backup copied to:', args.dest)
    if not args.keep_temp:
        cleanup_temp(temp_path)
        print('Temporary file removed.')

if __name__ == '__main__':
    main()