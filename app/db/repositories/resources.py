from app.core.config import settings
import os
import time
from ulid import ULID
import base64
def encrypt_str(data: str) -> str:
    return base64.b64encode(data.encode("utf-8")).decode()

def decrypt_str(data: str) -> str:
    return base64.b64decode(data.encode("utf-8")).decode("utf-8")

class ResourcesManager():
    def __init__(self):
        self.upload_dir = settings.PICTURE_UPLOAD_DIR


    def register_picture(self,extension:str):
        timestamp_ulid = ULID.from_timestamp(time.time())
        return encrypt_str(str(timestamp_ulid) + f".{extension}")
     
    def get_extension(self,uid:str):
        decrypted_str = decrypt_str(uid)
        return decrypted_str.split(".")[-1]

    def get_picture_path(self,uid:str,extension:str):
        file_name = f"{uid}.{extension}"
        file_path = self.upload_dir + "/" + file_name
        return file_path

resourcesManager = ResourcesManager();