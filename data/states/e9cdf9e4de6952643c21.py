#copilot mean_prob: 0.7191881264274596
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
import tarfile
import os

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonprefix([abs_directory, abs_target]) == abs_directory

def _safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    for member in tar.getmembers() if members is None else members:
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            # Discard dangerous member
            continue
        tar.extract(member, path, set_attrs=numeric_owner)

# Unzip the tar file to /tmp/unpack
extract_path = "/tmp/unpack"
os.makedirs(extract_path, exist_ok=True)

with tarfile.open("archive.zip") as tar:
    _safe_extract(tar, path=extract_path)