"""sd.cpp-webui - Encrypted image display utilities"""

import os

from PIL import Image

from modules.shared_instance import config
from modules.utils.encryption import ImageEncryption


IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')


def decrypt_and_display(image_paths):
    """
    解密图片列表并返回可显示的图片对象
    
    Args:
        image_paths: 图片路径列表或单个路径
    
    Returns:
        解密后的 PIL Image 对象或列表
    """
    if not isinstance(image_paths, (str, list, tuple)):
        return image_paths

    enable_encryption = config.get('enable_encryption', False)
    
    if not enable_encryption:
        return image_paths
    
    password = config.get('encryption_password', '123')
    encryptor = ImageEncryption(password)
    
    is_single = isinstance(image_paths, str)
    if is_single:
        image_paths = [image_paths]
    else:
        image_paths = list(image_paths)
    
    decrypted_images = []
    for path in image_paths:
        if (
            path and os.path.exists(path)
            and str(path).lower().endswith(IMAGE_EXTENSIONS)
        ):
            try:
                img = encryptor.decrypt_image_file(path)
                decrypted_images.append(img)
            except Exception as e:
                print(f"Failed to decrypt {path}: {e}")
                try:
                    decrypted_images.append(Image.open(path))
                except Exception:
                    decrypted_images.append(path)
        else:
            decrypted_images.append(path)
    
    return decrypted_images[0] if is_single else decrypted_images
