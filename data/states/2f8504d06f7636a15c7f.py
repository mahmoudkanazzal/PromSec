import tarfile
import os

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonprefix([abs_directory, abs_target]) == abs_directory

def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    """
    Extract tar safely, preventing path traversal attacks.
    """
    if members is None:
        members = tar.getmembers()
    for member in members:
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
    tar.extractall(path, members, numeric_owner=numeric_owner)

# unzip the tar file to /tmp/unpack
output_dir = "/tmp/unpack"
os.makedirs(output_dir, exist_ok=True)

with tarfile.open("archive.zip") as tar:
    safe_extract(tar, path=output_dir)