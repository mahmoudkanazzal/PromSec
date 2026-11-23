import os
import tarfile
import tempfile

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

def _main() -> None:
    with tarfile.open("archive.zip") as tar:
        # Create a securely generated temporary directory for extraction
        with tempfile.TemporaryDirectory(prefix="unpack_") as temp_dir:
            safe_extract(tar, temp_dir)

if __name__ == "__main__":
    _main()