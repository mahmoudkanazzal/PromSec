import os
import tarfile
import tempfile

# Ensure the base extraction directory exists
BASE_EXTRACT_DIR = "/tmp/unpack"
os.makedirs(BASE_EXTRACT_DIR, exist_ok=True)

def _is_within_directory(directory: str, target: str) -> bool:
    """
    Return True if the target path is located within the given directory.
    """
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return abs_target.startswith(abs_directory + os.sep)

def safe_extract(tar: tarfile.TarFile, path: str) -> None:
    """
    Extract members from a tar archive safely, discarding any that would
    result in path traversal or absolute paths.
    """
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            # Skip unsafe member
            continue
        tar.extract(member, path=path)

# Unzip the tar file to a securely created temporary subdirectory under /tmp/unpack
with tarfile.open("archive.zip") as tar:
    temp_dir = tempfile.mkdtemp(dir=BASE_EXTRACT_DIR)
    safe_extract(tar, temp_dir)