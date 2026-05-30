"""sd.cpp-webui - Encrypted image display utilities"""

import os
from PIL import Image, UnidentifiedImageError

from modules.utils.encryption import ImageEncryption
from modules.utils.decrypted_image_server import (
    can_decrypt_image,
    create_decrypted_image_url,
    detect_image_media_type,
    get_request_base_url,
)
from modules.shared_instance import config


def _is_plain_image_file(path):
    try:
        with open(path, "rb") as image_file:
            return detect_image_media_type(image_file.read(64)) is not None
    except OSError:
        return False


def load_preview_image(path):
    """Return a PIL image for an intermediate preview without writing plaintext.

    Preview files are short-lived and can be overwritten while generation is
    running, so they should not be exposed through the signed HTTP image route.
    This helper loads the current bytes into memory and detaches the PIL image
    from the underlying file handle before Gradio receives it.
    """
    if not path or not os.path.exists(path):
        return None

    enable_encryption = config.get('enable_encryption', False)

    try:
        if _is_plain_image_file(path):
            image = Image.open(path)
            image.load()
            return image

        if not enable_encryption:
            return None

        password = config.get('encryption_password', '123')
        return ImageEncryption(password).decrypt_image_file(path)
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        print(f"Failed to load preview image {path}: {exc}")
        return None


def decrypt_and_display(image_paths, request=None):
    """
    解密图片列表并返回可显示的 HTTP 图片链接。
    
    Args:
        image_paths: 图片路径列表或单个路径
        request: Gradio request，用于生成浏览器可访问的完整 HTTP URL
    
    Returns:
        解密后的 HTTP 图片链接、普通图片路径或列表
    """
    enable_encryption = config.get('enable_encryption', False)
    
    if not enable_encryption:
        return image_paths
    
    password = config.get('encryption_password', '123')
    encryptor = ImageEncryption(password)
    
    is_single = isinstance(image_paths, str)
    if is_single:
        image_paths = [image_paths]
    
    decrypted_images = []
    base_url = get_request_base_url(request)
    for path in image_paths:
        if path and os.path.exists(path):
            if _is_plain_image_file(path):
                decrypted_images.append(path)
            elif can_decrypt_image(path, encryptor):
                decrypted_images.append(create_decrypted_image_url(path, base_url))
            else:
                print(f"Failed to decrypt or open image: {path}")
        else:
            print(f"Path does not exist: {path}")
    
    if not decrypted_images:
        return None if is_single else []
    
    return decrypted_images[0] if is_single else decrypted_images
