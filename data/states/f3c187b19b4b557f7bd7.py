import tarfile
import os

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return abs_target.startswith(abs_directory + os.sep)

def _safe_members(tar, extract_path):
    safe = []
    for member in tar.getmembers():
        member_path = os.path.join(extract_path, member.name)
        if _is_within_directory(extract_path, member_path):
            safe.append(member)
    return safe

# unzip the tar file to /tmp/unpack
with tarfile.open("archive.zip") as tar:
    extract_path = "unpack"
    tar.extractall(path=extract_path, members=_safe_members(tar, extract_path))