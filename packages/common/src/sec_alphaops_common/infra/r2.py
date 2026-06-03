from __future__ import annotations

import os
from typing import Any


class R2Client:
    """Cloudflare R2 (S3-compatible) client."""

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> None:
        import boto3

        self.bucket = bucket
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    @classmethod
    def from_env(cls) -> R2Client | None:
        endpoint = os.environ.get("R2_ENDPOINT")
        bucket = os.environ.get("R2_BUCKET")
        key_id = os.environ.get("R2_ACCESS_KEY_ID")
        secret = os.environ.get("R2_SECRET_ACCESS_KEY")
        if not all([endpoint, bucket, key_id, secret]):
            return None
        return cls(endpoint, bucket, key_id, secret)

    def cache_key(self, filing_type: str, ticker: str, year: int, accession: str) -> str:
        safe = accession.replace("/", "-")
        return f"cache/{filing_type}/{ticker.upper()}/{year}/{safe}.txt"

    def get_text(self, key: str) -> str | None:
        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read().decode("utf-8", errors="replace")
        except self._client.exceptions.NoSuchKey:
            return None
        except Exception:
            return None

    def put_text(self, key: str, body: str) -> None:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="text/plain",
        )

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
