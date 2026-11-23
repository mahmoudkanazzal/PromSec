import tarfile
import os

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

def _safe_members(tar, path):
    safe = []
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if _is_within_directory(path, member_path):
            safe.append(member)
    return safe

with tarfile.open("archive.zip") as tar:
    tar.extractall("unpack", members=_safe_members(tar, "unpack"))