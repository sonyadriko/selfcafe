import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles

from app.config import settings

# Allowed image types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# Upload limits
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSION = 2000  # pixels


class UploadService:
    """Service for handling image uploads with validation."""

    def __init__(self):
        self.upload_dir = Path("app/static/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()

    def _generate_filename(self, original_filename: str) -> str:
        """Generate unique filename preserving extension."""
        ext = self._get_file_extension(original_filename)
        unique_name = str(uuid.uuid4())
        return f"{unique_name}{ext}"

    def _validate_file(self, file: UploadFile) -> None:
        """Validate file type and size."""
        # Check extension
        ext = self._get_file_extension(file.filename or "")
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check content type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )

    async def _validate_and_process_image(self, file_path: Path) -> None:
        """Validate image dimensions and optimize if needed."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size

                # Check dimensions
                if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                    # Resize if too large
                    img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
                    img.save(file_path, optimize=True, quality=85)

        except Exception as e:
            # Not a valid image
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail="Invalid image file")

    async def upload_image(self, file: UploadFile) -> str:
        """
        Upload and validate image file.

        Returns:
            str: Relative URL path for the uploaded image
        """
        self._validate_file(file)

        # Generate unique filename
        filename = self._generate_filename(file.filename or "image.jpg")
        file_path = self.upload_dir / filename

        # Read and validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Write file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Validate and process image
        await self._validate_and_process_image(file_path)

        # Return relative URL path
        return f"/static/uploads/{filename}"

    def delete_image(self, image_url: str) -> bool:
        """
        Delete image file from filesystem.

        Args:
            image_url: URL path of the image

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            # Extract filename from URL
            if image_url.startswith("/static/uploads/"):
                filename = image_url.split("/")[-1]
                file_path = self.upload_dir / filename

                if file_path.exists():
                    file_path.unlink()
                    return True
        except Exception:
            pass

        return False


# Singleton instance
upload_service = UploadService()
