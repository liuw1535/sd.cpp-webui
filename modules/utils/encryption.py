"""sd.cpp-webui - Image encryption module"""


class ImageEncryption:
    """处理图片的加密和解密（兼容 sd-cli 的 XOR 加密）"""
    
    def __init__(self, password="123"):
        self.password = password
    
    def _generate_key(self):
        """生成 256 字节密钥（与 decrypt.js 相同算法）"""
        key = bytearray(256)
        password_bytes = self.password.encode('utf-8')
        for i in range(256):
            key[i] = password_bytes[i % len(password_bytes)] ^ (i & 0xFF)
        return bytes(key)

    def _xor_bytes(self, data: bytes, offset: int = 0) -> bytes:
        key = self._generate_key()
        return bytes(
            value ^ key[(offset + index) % len(key)]
            for index, value in enumerate(data)
        )

    def encrypt_file_in_place(self, path):
        """对文件原地执行 XOR 加密。"""
        with open(path, 'rb') as f:
            data = f.read()

        with open(path, 'wb') as f:
            f.write(self._xor_bytes(data))

    def decrypt_image_bytes(self, encrypted_path):
        """解密图片文件并返回原始图片字节，不写入磁盘。"""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()

        return self._xor_bytes(encrypted_data)

    def decrypt_file_prefix(self, encrypted_path, size=64):
        """只解密文件开头，用于判断文件是否是加密图片。"""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read(size)

        return self._xor_bytes(encrypted_data)
    
    def decrypt_image_file(self, encrypted_path):
        """解密图片文件并返回 PIL Image 对象"""
        import io
        from PIL import Image

        decrypted_data = self.decrypt_image_bytes(encrypted_path)

        # 转换为 PIL Image，并加载到内存，避免底层 BytesIO 生命周期影响 UI 显示。
        image = Image.open(io.BytesIO(decrypted_data))
        image.load()
        return image
