import os
import tarfile
import tempfile

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory, abs_target]) == abs_directory

def _safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    # Determine which members to extract safely
    if members is None:
        candidate_members = tar.getmembers()
    else:
        candidate_members = members
    safe_members = []
    for member in candidate_members:
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
        safe_members.append(member)
    tar.extractall(path, members=safe_members, numeric_owner=numeric_owner)

# Create a secure temporary directory for extraction
temp_dir = tempfile.mkdtemp()

with tarfile.open("archive.zip") as tar:
    _safe_extract(tar, path=temp_dir)