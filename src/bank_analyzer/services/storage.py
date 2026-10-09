import hashlib
import uuid
from pathlib import Path

from bank_analyzer.core.config import settings


def save_file(contents: bytes, user_id: str) -> str:
    relative_path = Path(user_id) / f"{uuid.uuid4()}.pdf"

    destination = Path(settings.STORAGE_DIR) / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(contents)

    return relative_path.as_posix()


def read_file(file_path: str) -> bytes:
    return (Path(settings.STORAGE_DIR) / file_path).read_bytes()


def calculate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
