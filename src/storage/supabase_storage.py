import io
import uuid
from typing import Optional

import requests
from PIL import Image

from src.config import get_config


class SupabaseStorageService:
    """Service for uploading images to Supabase Storage."""

    def __init__(self) -> None:
        self._config = get_config()

    def _get_upload_url(self, file_path: str) -> str:
        base_url = self._config.supabase_url
        bucket = self._config.supabase_bucket_name
        return f"{base_url}/storage/v1/object/{bucket}/{file_path}"

    def upload_image(
        self,
        image: Image.Image,
        folder: str = "diagrams",
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload a PIL Image to Supabase Storage.

        Args:
            image: PIL Image to upload
            folder: Folder within the bucket (e.g., "diagrams")
            filename: Optional filename. If not provided, generates UUID

        Returns:
            Public URL of the uploaded image

        Raises:
            RuntimeError: If Supabase is not configured or upload fails
        """
        if not self._config.has_supabase:
            raise RuntimeError(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
            )

        if filename is None:
            filename = f"{uuid.uuid4()}.png"

        file_path = f"{folder}/{filename}"

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        image_bytes = buffer.getvalue()

        upload_url = self._get_upload_url(file_path)
        headers = {
            "Authorization": f"Bearer {self._config.supabase_anon_key}",
            "Content-Type": "image/png",
        }

        response = requests.post(upload_url, headers=headers, data=image_bytes)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to upload image: {response.status_code} {response.text}"
            )

        bucket = self._config.supabase_bucket_name
        public_url = (
            f"{self._config.supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        )
        return public_url


_storage_service: Optional[SupabaseStorageService] = None


def get_storage_service() -> SupabaseStorageService:
    """Get the singleton storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = SupabaseStorageService()
    return _storage_service
