import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """配置管理器，负责管理应用设置和配置文件"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.logger = logging.getLogger(__name__)
        
        # 配置目录
        self.config_dir = Path.home() / ".noisy_keyboard"
        self.config_dir.mkdir(exist_ok=True)
        
        # 音效目录
        self.sounds_dir = self.config_dir / "sounds"
        self.sounds_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.settings_file = self.config_dir / "settings.json"
        self.key_bindings_file = self.config_dir / "key_bindings.json"
        self.sound_library_file = self.config_dir / "sound_library.json"
        
        # 默认配置
        self.default_settings = {
            "enabled": True,
            "volume": 80,
            "minimize_to_tray": True,
            "auto_start": False
        }
        
        # 加载配置
        self.settings = self.load_config(self.settings_file, self.default_settings)
        self.key_bindings = self.load_config(self.key_bindings_file, {})
        self.sound_library = self.load_config(self.sound_library_file, [])
        
        # 如果音效库为空，创建默认音效
        if not self.sound_library:
            self._create_default_sounds()
        
        # 如果配置中缺少 allow_custom_sound_paths，默认设为 True
        if "allow_custom_sound_paths" not in self.settings:
            self.settings["allow_custom_sound_paths"] = True
            self.save_config(self.settings_file, self.settings)
    
    def load_all_configs(self):
        """加载所有配置文件"""
        self.settings = self.load_config(self.settings_file, self.default_settings)
        self.key_bindings = self.load_config(self.key_bindings_file, {})
        self.sound_library = self.load_config(self.sound_library_file, [])
        
        # 如果音效库为空，创建默认音效
        if not self.sound_library:
            self._create_default_sounds()
    
    def load_config(self, file_path: Path, default_config: Any) -> Any:
        """加载单个配置文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return default_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件失败 {file_path}: {e}")
            return default_config
    
    def save_all_configs(self):
        """保存所有配置"""
        self.save_config(self.settings_file, self.settings)
        self.save_config(self.key_bindings_file, self.key_bindings)
        self.save_config(self.sound_library_file, self.sound_library)
    
    def save_config(self, file_path: Path, config: Any):
        """保存单个配置文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件失败 {file_path}: {e}")
    
    def _create_default_sounds(self):
        """创建默认音效"""
        try:
            # 复制资源文件到音效目录
            resource_dir = Path(__file__).parent.parent / "resource"
            default_sound_file = resource_dir / "space-animal-104986.mp3"
            
            if default_sound_file.exists():
                # 复制到音效目录
                target_file = self.sounds_dir / "default_sound_001.mp3"
                if not target_file.exists():
                    import shutil
                    shutil.copy2(default_sound_file, target_file)
                
                # 添加到音效库
                sound_info = {
                    "id": "default_sound_001",
                    "filename": "default_sound_001.mp3",
                    "path": str(target_file),
                    "size": target_file.stat().st_size,
                    "upload_time": "2024-01-01 12:00:00"
                }
                self.sound_library.append(sound_info)
                self.save_config(self.sound_library_file, self.sound_library)
                self.logger.info("默认音效创建完成")
            else:
                self.logger.warning("默认音效资源文件不存在")
                
        except Exception as e:
            self.logger.error(f"创建默认音效失败: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置项"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """设置配置项"""
        self.settings[key] = value
        self.save_config(self.settings_file, self.settings)
    
    def get_key_sound(self, key: str) -> Optional[str]:
        """获取按键绑定的音效路径"""
        sound_id = self.key_bindings.get(key)
        if sound_id:
            sound_info = self.get_sound_info(sound_id)
            return sound_info.get("path") if sound_info else sound_id  # 直接返回路径如果存在
        return None
    
    def set_key_sound(self, key: str, sound_path: str):
        """设置按键绑定"""
        if sound_path:  # 有音效路径
            self.key_bindings[key] = sound_path  # 直接使用路径作为ID
        else:  # 清除绑定
            if key in self.key_bindings:
                del self.key_bindings[key]
        
        self.save_config(self.key_bindings_file, self.key_bindings)
    
    def get_sound_info(self, sound_path: str) -> Optional[Dict[str, Any]]:
        """获取音效信息"""
        # 现在直接使用路径作为ID，所以查找路径匹配
        for sound in self.sound_library:
            if sound.get("path") == sound_path:
                return sound
        # 如果路径不存在但在文件系统中存在，创建一个基本信息
        if sound_path and os.path.exists(sound_path):
            return {
                "id": sound_path,
                "filename": os.path.basename(sound_path),
                "path": sound_path,
                "size": os.path.getsize(sound_path),
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_custom_path": True  # 标记为自定义路径
            }
        return None
    
    def add_sound_to_library(self, sound_info: Dict[str, Any]):
        """添加音效到音效库"""
        # 确保有必要的字段
        if "is_custom_path" not in sound_info:
            sound_info["is_custom_path"] = False
        
        self.sound_library.append(sound_info)
        self.save_config(self.sound_library_file, self.sound_library)
    
    def remove_sound_from_library(self, sound_id: str) -> bool:
        """从音效库移除音效"""
        for i, sound in enumerate(self.sound_library):
            if sound.get("id") == sound_id or sound.get("path") == sound_id:
                # 只有非自定义路径的音效文件才删除物理文件
                if not sound.get("is_custom_path", False):
                    sound_path = Path(sound.get("path", ""))
                    if sound_path.exists() and sound_path.name != "space-animal-104986.mp3":
                        try:
                            sound_path.unlink()
                        except OSError:
                            pass
                
                # 从音效库移除
                del self.sound_library[i]
                
                # 更新按键绑定
                keys_to_remove = [k for k, v in self.key_bindings.items() if v == sound_id]
                for key in keys_to_remove:
                    del self.key_bindings[key]
                
                self.save_all_configs()
                return True
        return False
    
    def get_all_key_bindings(self) -> Dict[str, str]:
        """获取所有按键绑定"""
        return self.key_bindings.copy()
    
    def get_sound_library(self) -> Dict[str, str]:
        """获取音效库（名称到路径的映射）"""
        library = {}
        # 添加默认音效
        for sound in self.sound_library:
            name = sound.get("filename", "")
            path = sound.get("path", "")
            if name and path and os.path.exists(path):
                # 如果是自定义路径，在名称前加标记
                if sound.get("is_custom_path", False):
                    name = f"📁 {name}"
                library[name] = path
        return library

    def add_custom_sound_path(self, file_path: str) -> bool:
        """添加自定义音效路径"""
        if not self.settings.get("allow_custom_sound_paths", True):
            return False
            
        if not os.path.exists(file_path):
            return False
            
        # 检查文件类型
        if not file_path.lower().endswith('.mp3'):
            return False
            
        # 创建音效信息
        sound_info = {
            "id": file_path,  # 使用路径作为ID
            "filename": os.path.basename(file_path),
            "path": file_path,
            "size": os.path.getsize(file_path),
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_custom_path": True
        }
        
        # 检查是否已存在
        for sound in self.sound_library:
            if sound.get("path") == file_path:
                return False
            
        self.add_sound_to_library(sound_info)
        return True
    
    def get_key_binding(self, key: str) -> Optional[str]:
        """获取按键绑定的音效ID"""
        return self.key_bindings.get(key)
    
    def get_key_bindings(self) -> Dict[str, str]:
        """获取所有按键绑定（按键到音效路径的映射）"""
        # 直接返回按键到路径的映射
        return self.key_bindings.copy()
    
    def set_key_bindings(self, bindings: Dict[str, str]):
        """设置所有按键绑定"""
        for key, sound_path in bindings.items():
            self.set_key_sound(key, sound_path)
    
    def get_sound_name_by_path(self, sound_path: str) -> Optional[str]:
        """根据音效路径获取音效名称"""
        if not sound_path:
            return None
        # 如果传入的是字典，提取路径
        if isinstance(sound_path, dict):
            sound_path = sound_path.get("path", "")
            if not sound_path:
                return None
        # 直接从路径获取文件名
        return os.path.basename(sound_path)
    
    def is_enabled(self) -> bool:
        """检查应用是否启用"""
        return self.settings.get("enabled", True)
    
    def set_enabled(self, enabled: bool):
        """设置应用启用状态"""
        self.settings["enabled"] = enabled
        self.save_config(self.settings_file, self.settings)
    
    def get_volume(self) -> float:
        """获取音量设置"""
        return self.settings.get("volume", 0.8)
    
    def set_volume(self, volume: float):
        """设置音量"""
        self.settings["volume"] = max(0.0, min(1.0, volume))
        self.save_config(self.settings_file, self.settings)
    
    def save_config(self, file_path: Path = None, config: Any = None):
        """保存配置（兼容主程序调用）"""
        if file_path is None and config is None:
            self.save_all_configs()
        elif file_path and config is not None:
            self._save_config_file(file_path, config)
        else:
            self.save_all_configs()
    
    def _save_config_file(self, file_path: Path, config: Any):
        """保存单个配置文件（内部方法）"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件失败 {file_path}: {e}")