import os
import tarfile
import tempfile

def _is_within_directory(directory: str, target: str) -> bool:
    """
    Ensure that the target path is within the given directory to prevent path traversal.
    """
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return abs_target.startswith(abs_directory + os.sep) or abs_target == abs_directory

def _safe_extract(tar: tarfile.TarFile, path: str = ".") -> None:
    """
    Extract members from a tar archive safely, discarding any that would escape the destination directory.
    """
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            # Skip unsafe member
            continue
        tar.extract(member, path=path)

# Use a securely created temporary directory for extraction
with tarfile.open("archive.zip") as tar:
    with tempfile.TemporaryDirectory() as tmp_dir:
        _safe_extract(tar, path=tmp_dir)