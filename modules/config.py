import json
from pathlib import Path

CONFIG_FILE = Path.home() / 'AppData' / 'Roaming' / 'yhchat-winui3' / "config.json"


class Config:
    def __init__(self):
        """初始化配置，确保配置文件存在"""
        try:
            # 确保配置目录存在
            config_dir = CONFIG_FILE.parent
            if not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果配置文件不存在，创建空的配置文件
            if not CONFIG_FILE.exists():
                with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                    json.dump({}, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"初始化配置文件失败: {e}")
            # 可以选择重新抛出异常或者进行其他错误处理

    def set(self, key: str, content):
        """设置配置项"""
        try:
            json_content = self.get("*")
            json_content[key] = content
            
            # 使用json.dump来确保正确的JSON格式
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(json_content, file, ensure_ascii=False, indent=4)
                
        except PermissionError:
            print(f"没有权限写入配置文件: {CONFIG_FILE}")
        except Exception as e:
            print(f"设置配置项 '{key}' 失败: {e}")

    def get(self, key: str, default=None):
        """获取配置项"""
        try:
            # 检查文件是否存在
            if not CONFIG_FILE.exists():
                return default
                
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                json_content = json.load(file)  # 使用json.load替代json.loads(file.read())
                
            if key == "*":
                return json_content
            elif key in json_content:
                return json_content[key]
            else:
                return default
                
        except json.JSONDecodeError:
            print(f"配置文件格式错误: {CONFIG_FILE}")
            return default
        except PermissionError:
            print(f"没有权限读取配置文件: {CONFIG_FILE}")
            return default
        except Exception as e:
            print(f"获取配置项 '{key}' 失败: {e}")
            return default

    def delete(self, key: str):
        """删除配置项"""
        try:
            json_content = self.get("*")
            if key in json_content:
                del json_content[key]
                with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                    json.dump(json_content, file, ensure_ascii=False, indent=4)
                return True
            return False
        except Exception as e:
            print(f"删除配置项 '{key}' 失败: {e}")
            return False

    def clear(self):
        """清空所有配置"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"清空配置失败: {e}")