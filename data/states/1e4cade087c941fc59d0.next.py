import os
import tarfile
import tempfile

def _is_within_directory(directory: str, target: str) -> bool:
    """Return True if target is inside directory."""
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory, abs_target]) == abs_directory

def _safe_extract(tar: tarfile.TarFile, path: str) -> None:
    """Extract members from tar safely, discarding unsafe paths."""
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            # Skip members that would escape the extraction directory
            continue
        tar.extract(member, path=path)

# Use a securely created temporary directory for extraction
with tarfile.open("archive.zip") as tar:
    with tempfile.TemporaryDirectory() as extract_dir:
        _safe_extract(tar, extract_dir)