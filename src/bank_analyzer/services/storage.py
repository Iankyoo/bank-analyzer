import hashlib
import io
import uuid

import boto3
from fastapi import UploadFile

from bank_analyzer.core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


async def upload_file(file: UploadFile, user_id: str) -> str:
    key = f"{user_id}/{uuid.uuid4()}.pdf"

    contents = await file.read()
    file_obj = io.BytesIO(contents)

    s3_client.upload_fileobj(file_obj, settings.AWS_BUCKET_NAME, key)

    return key


def calculate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
