import threading
import datetime
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import httpx
from PIL import Image
from modules.req import HTTPThreadingClient

session = HTTPThreadingClient()

class Api:
    _avatar_executor = ThreadPoolExecutor(max_workers=8)

    @staticmethod
    def EmailLogin(email: str, password: str, deviceId: str = "yunhu-device-id-winui3-app", platform: str = "windows"):
        json_data = {
            "email": email,
            "password": password,
            "deviceId": deviceId,
            "platform": platform
        }
        
        response_result = {"response": None, "error": None}
        
        def success_callback(response):
            response_result["response"] = response
        
        def error_callback(error):
            response_result["error"] = error
        
        session.post(
            "https://chat-go.jwzhd.com/v1/user/email-login", 
            json=json_data,
            callback=success_callback,
            error_callback=error_callback
        )
        
        session.wait_completion()
        
        if response_result["error"]:
            print(f"[Api.EmailLogin] request error: {response_result['error']}")
            raise Exception(f"请求失败: {response_result['error']}")
        
        return response_result["response"]

    @staticmethod
    def _import_user_pb2():
        from google.protobuf import json_format
        from modules.proto import user_pb2
        return user_pb2, json_format

    @staticmethod
    def UserInfo(token: str):
        headers = {"token": token}
        response_result = {"response": None, "error": None}

        def success_callback(response):
            response_result["response"] = response

        def error_callback(error):
            response_result["error"] = error

        session.get(
            "https://chat-go.jwzhd.com/v1/user/info",
            headers=headers,
            callback=success_callback,
            error_callback=error_callback,
        )

        session.wait_completion()

        if response_result["error"]:
            print(f"[Api.UserInfo] request error: {response_result['error']}")
            raise Exception(f"请求失败: {response_result['error']}")

        resp = response_result["response"]
        if resp is None:
            print("[Api.UserInfo] empty response")
            raise Exception("请求失败: 空响应")

        if resp.status_code != 200:
            print(f"[Api.UserInfo] bad status: {resp.status_code}")
            raise Exception(f"网络请求失败: {resp.status_code}")

        user_pb2, json_format = Api._import_user_pb2()
        msg = user_pb2.info()
        msg.ParseFromString(resp.content)
        data = json_format.MessageToDict(msg)
        avatar = data.get("data", {}).get("avatarUrl") or data.get("data", {}).get("avatar_url")
        print(f"[Api.UserInfo] parsed ok, has avatar_url={bool(avatar)}")
        return data

    @staticmethod
    def GetAvatarUrl(token: str) -> str:
        info = Api.UserInfo(token)
        return (
            info.get("data", {}).get("avatarUrl")
            or info.get("data", {}).get("avatar_url")
            or ""
        )

    @staticmethod
    def UserInfoFromConfig():
        from modules.config import Config
        token = Config().get("token")
        if not token:
            raise Exception("未登录: token 为空")
        return Api.UserInfo(token)

    @staticmethod
    def AvatarUrlFromConfig() -> str:
        from modules.config import Config
        token = Config().get("token")
        if not token:
            return ""
        return Api.GetAvatarUrl(token)

    @staticmethod
    def DownloadAvatarToCache(avatar_url: str) -> str:
        if not avatar_url:
            return ""

        from modules.config import CONFIG_FILE

        cache_dir = CONFIG_FILE.parent / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / "avatar"

        headers = {
            "Referer": "https://myapp.jwznb.com",
            "User-Agent": "yhchat-winui3-app",
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(avatar_url, headers=headers)
            resp.raise_for_status()

        content_type = (resp.headers.get("content-type") or "").lower()
        ext = ".img"
        if "png" in content_type:
            ext = ".png"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "webp" in content_type:
            ext = ".webp"

        file_path = target.with_suffix(ext)
        file_path.write_bytes(resp.content)
        print(f"[Api.DownloadAvatarToCache] saved: {file_path}")
        return str(file_path)

    @staticmethod
    def _import_conversation_pb2():
        from google.protobuf import json_format
        from modules.proto import conversation_pb2
        return conversation_pb2, json_format

    @staticmethod
    def ConversationList(token: str):
        headers = {"token": token}
        response_result = {"response": None, "error": None}

        def success_callback(response):
            response_result["response"] = response

        def error_callback(error):
            response_result["error"] = error

        session.post(
            "https://chat-go.jwzhd.com/v1/conversation/list",
            headers=headers,
            data=b"",
            callback=success_callback,
            error_callback=error_callback,
        )

        session.wait_completion()

        if response_result["error"]:
            print(f"[Api.ConversationList] request error: {response_result['error']}")
            raise Exception(f"请求失败: {response_result['error']}")

        resp = response_result["response"]
        if resp is None:
            print("[Api.ConversationList] empty response")
            raise Exception("请求失败: 空响应")

        content_type = (resp.headers.get("content-type") or "").lower()
        if resp.status_code != 200:
            raise Exception(f"网络请求失败: {resp.status_code}")

        if "json" in content_type or (resp.content or b"").lstrip().startswith(b"{"):
            try:
                data = resp.json()
                print(f"[Api.ConversationList] json ok keys={list(data.keys())}")
                return data
            except Exception:
                pass

        conversation_pb2, json_format = Api._import_conversation_pb2()
        msg = conversation_pb2.ConversationList()
        msg.ParseFromString(resp.content)
        data = json_format.MessageToDict(msg)
        status = data.get("status") or {}
        print(
            "[Api.ConversationList] parsed ok, "
            f"status.code={status.get('code')} status.msg={status.get('msg')} "
            f"total={data.get('total')} count={len(data.get('data', []) or [])}"
        )
        return data

    @staticmethod
    def ConversationListFromConfig():
        from modules.config import Config
        token = Config().get("token")
        if not token:
            raise Exception("未登录: token 为空")
        return Api.ConversationList(token)

    @staticmethod
    def _import_msg_pb2():
        from google.protobuf import json_format
        from modules.proto import msg_pb2
        return msg_pb2, json_format

    @staticmethod
    def MessageList(token: str, chat_id: str, chat_type: int, msg_count: int = 50, msg_id: str = ""):
        headers = {"token": token}
        msg_pb2, json_format = Api._import_msg_pb2()
        req = msg_pb2.list_message_send()
        req.chat_id = chat_id
        req.chat_type = chat_type
        req.msg_count = msg_count
        if msg_id:
            req.msg_id = msg_id
            
        data_bytes = req.SerializeToString()
        response_result = {"response": None, "error": None}

        def success_callback(response):
            response_result["response"] = response

        def error_callback(error):
            response_result["error"] = error

        session.post(
            "https://chat-go.jwzhd.com/v1/msg/list-message",
            headers=headers,
            data=data_bytes,
            callback=success_callback,
            error_callback=error_callback,
        )

        session.wait_completion()

        if response_result["error"]:
            raise Exception(f"请求失败: {response_result['error']}")

        resp = response_result["response"]
        if resp is None:
            raise Exception("请求失败: 空响应")

        if resp.status_code != 200:
            raise Exception(f"网络请求失败: {resp.status_code}")

        msg_pb2, json_format = Api._import_msg_pb2()
        msg_resp = msg_pb2.list_message()
        msg_resp.ParseFromString(resp.content)
        data = json_format.MessageToDict(msg_resp)
        print(f"[Api.MessageList] parsed ok, count={len(data.get('msg', []) or [])}")
        return data

    @staticmethod
    def MessageListFromConfig(chat_id: str, chat_type: int, msg_count: int = 50, msg_id: str = ""):
        from modules.config import Config
        token = Config().get("token")
        if not token:
            raise Exception("未登录: token 为空")
        return Api.MessageList(token, chat_id, chat_type, msg_count, msg_id)

    @staticmethod
    def SendMessage(token: str, chat_id: str, chat_type: int, text: str):
        headers = {"token": token}
        msg_pb2, json_format = Api._import_msg_pb2()
        req = msg_pb2.send_message_send()
        req.chat_id = chat_id
        req.chat_type = chat_type
        req.data.text = text
        req.content_type = 1  # Text

        req.msg_id = str(uuid.uuid4()).replace("-", "")

        data_bytes = req.SerializeToString()
        response_result = {"response": None, "error": None}

        def success_callback(response):
            response_result["response"] = response

        def error_callback(error):
            response_result["error"] = error

        session.post(
            "https://chat-go.jwzhd.com/v1/msg/send-message",
            headers=headers,
            data=data_bytes,
            callback=success_callback,
            error_callback=error_callback,
        )

        session.wait_completion()

        if response_result["error"]:
            raise Exception(f"请求失败: {response_result['error']}")

        resp = response_result["response"]
        if resp is None:
            raise Exception("请求失败: 空响应")

        if resp.status_code != 200:
            raise Exception(f"网络请求失败: {resp.status_code}")

        msg_pb2, json_format = Api._import_msg_pb2()
        msg_resp = msg_pb2.send_message()
        msg_resp.ParseFromString(resp.content)
        data = json_format.MessageToDict(msg_resp)
        print(f"[Api.SendMessage] status={data.get('status', {}).get('code')}")
        return data

    @staticmethod
    def SendMessageFromConfig(chat_id: str, chat_type: int, text: str):
        from modules.config import Config
        token = Config().get("token")
        if not token:
            raise Exception("未登录: token 为空")
        return Api.SendMessage(token, chat_id, chat_type, text)

    @staticmethod
    def _get_qiniu_upload_token(token: str):
        headers = {"token": token}
        response_result = {"response": None, "error": None}
        def success_callback(response):
            response_result["response"] = response
        def error_callback(error):
            response_result["error"] = error

        session.get(
            "https://chat-go.jwzhd.com/v1/misc/qiniu-token",
            headers=headers,
            callback=success_callback,
            error_callback=error_callback
        )
        session.wait_completion()
        if response_result["error"]:
            raise Exception(f"获取七牛Token失败: {response_result['error']}")
        
        resp = response_result["response"]
        if not resp or resp.status_code != 200:
            raise Exception(f"获取七牛Token失败, status: {resp.status_code if resp else 'None'}")
        
        data = resp.json()
        if data.get("code") != 1:
            raise Exception(f"获取七牛Token接口返回错误: {data}")
        return data.get("data", {}).get("token")

    @staticmethod
    def UploadImage(token: str, image_bytes: bytes, filename: str):
        if token is None:
            from modules.config import Config
            token = Config().get("token")
            if not token:
                raise Exception("未登录: token 为空")

        # 1. 获取上传 Token
        qiniu_token = Api._get_qiniu_upload_token(token)

        # 2. 处理图片 (获取尺寸)
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        
        # 3. 准备上传
        md5 = hashlib.md5(image_bytes).hexdigest()
        ext = os.path.splitext(filename)[1].lstrip('.') or "jpg"
        key = f"{md5}.{ext}"
        mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

        # 4. 上传到七牛
        upload_url = "https://upload-z2.qiniup.com"
        files = {"file": (key, image_bytes, mime_type)}
        data = {"token": qiniu_token, "key": key}

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(upload_url, data=data, files=files)
            if resp.status_code != 200:
                raise Exception(f"七牛上传失败: {resp.text}")
            
            result = resp.json()
            return {
                "file_key": result.get("key"),
                "file_hash": result.get("hash"),
                "file_size": len(image_bytes),
                "file_type": mime_type,
                "image_width": width,
                "image_height": height,
                "file_suffix": ext
            }

    @staticmethod
    def SendImageMessage(token: str, chat_id: str, chat_type: int, img_meta: dict):
        headers = {"token": token}
        msg_pb2, json_format = Api._import_msg_pb2()
        req = msg_pb2.send_message_send()
        
        req.msg_id = str(uuid.uuid4()).replace("-", "")
        req.chat_id = chat_id
        req.chat_type = chat_type
        req.content_type = 2 # Image

        req.data.image = f"{img_meta['file_key']}"

        req.media.file_key = img_meta['file_key']
        req.media.file_hash = img_meta['file_hash']
        req.media.file_type = img_meta['file_type']
        req.media.image_height = img_meta['image_height']
        req.media.image_width = img_meta['image_width']
        req.media.file_size = img_meta['file_size']
        req.media.file_key2 = img_meta['file_key']
        req.media.file_suffix = img_meta['file_suffix']

        data_bytes = req.SerializeToString()
        response_result = {"response": None, "error": None}

        def success_callback(response):
            response_result["response"] = response
        def error_callback(error):
            response_result["error"] = error

        session.post(
            "https://chat-go.jwzhd.com/v1/msg/send-message",
            headers=headers,
            data=data_bytes,
            callback=success_callback,
            error_callback=error_callback,
        )
        session.wait_completion()

        if response_result["error"]:
            raise Exception(f"发送图片消息失败: {response_result['error']}")
        return response_result["response"]

    @staticmethod
    def SendImageMessageFromConfig(chat_id: str, chat_type: int, img_meta: dict):
        from modules.config import Config
        token = Config().get("token")
        if not token:
            raise Exception("未登录")
        return Api.SendImageMessage(token, chat_id, chat_type, img_meta)

    @staticmethod
    def GetCachedImage(url: str) -> str:
        if not url:
            return ""

        from modules.config import CONFIG_FILE

        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_dir = CONFIG_FILE.parent / "cache" / "images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        ext = ".img"
        lower_url = url.lower()
        if ".png" in lower_url: ext = ".png"
        elif ".jpg" in lower_url or ".jpeg" in lower_url: ext = ".jpg"
        elif ".webp" in lower_url: ext = ".webp"
        
        target = cache_dir / f"{url_hash}{ext}"
        
        if target.exists():
            return str(target)

        headers = {
            "Referer": "https://myapp.jwznb.com",
            "User-Agent": "yhchat-winui3-app",
        }

        try:
            print(f"[Api.GetCachedImage] downloading {url} ...")
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                target.write_bytes(resp.content)
                return str(target)
        except Exception as e:
            print(f"[Api.GetCachedImage] failed for {url}: {e}")
            return ""
