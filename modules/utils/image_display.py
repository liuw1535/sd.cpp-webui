"""sd.cpp-webui - Encrypted image display utilities"""

import os
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
