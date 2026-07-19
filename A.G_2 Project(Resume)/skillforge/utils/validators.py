"""File validators for uploads."""
import os

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.avi']
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB


def validate_image(file):
    """Validate image file type and size."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Invalid image format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    if file.size > MAX_IMAGE_SIZE:
        raise ValueError(f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB")
    return True


def validate_video(file):
    """Validate video file type and size."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(f"Invalid video format. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}")
    if file.size > MAX_VIDEO_SIZE:
        raise ValueError(f"Video too large. Maximum size: {MAX_VIDEO_SIZE // (1024*1024)}MB")
    return True
