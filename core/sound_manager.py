import os
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from playsound import playsound
import logging


class SoundManager:
    """音效管理器，负责音效的播放和管理"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 音效缓存，避免重复加载
        self.sound_cache = {}
        self.cache_lock = threading.Lock()
        
        # 当前播放状态
        self.is_playing = False
        self.current_volume = 0.8
        
        # 播放线程
        self.play_thread = None
        
        self.logger.info("音效管理器初始化完成")
    
    def play_sound(self, sound_path: str, volume: float = 1.0) -> bool:
        """播放音效"""
        try:
            if not sound_path or not os.path.exists(sound_path):
                self.logger.warning(f"音效文件不存在: {sound_path}")
                return False
            
            # 异步播放音效
            self._play_sound_async(sound_path, volume)
            return True
            
        except Exception as e:
            self.logger.error(f"播放音效失败: {e}")
            return False
    
    def add_custom_sound(self, file_path: str) -> bool:
        """添加自定义音效文件"""
        try:
            # 验证文件
            if not self.validate_sound_file(file_path):
                return False
            
            # 如果启用了缓存，将文件添加到缓存
            if hasattr(self, 'use_cache') and self.use_cache:
                self._cache_sound_file(file_path)
            
            return True
        except Exception as e:
            self.logger.error(f"添加自定义音效失败: {e}")
            return False
    
    def _play_sound_async(self, sound_path: str, volume: float):
        """异步播放音效"""
        try:
            self.is_playing = True
            
            # 使用playsound播放音效
            # 注意：playsound不支持音量控制，这里直接播放
            playsound(sound_path)
            
            self.is_playing = False
            
        except Exception as e:
            self.logger.error(f"异步播放音效失败: {e}")
            self.is_playing = False
    
    def stop_sound(self):
        """停止当前播放的音效"""
        # playsound库没有停止功能，这里只是标记状态
        self.is_playing = False
    
    def set_volume(self, volume: int) -> bool:
        """设置音量 (0-100)"""
        try:
            # 将0-100的范围转换为0.0-1.0
            self.current_volume = max(0, min(100, volume)) / 100.0
            self.logger.info(f"音量设置为 {volume}%")
            return True
            
        except Exception as e:
            self.logger.error(f"设置音量失败: {e}")
            return False
    
    def get_volume(self) -> float:
        """获取当前音量"""
        return self.current_volume
    
    def preload_sound(self, sound_id: str) -> bool:
        """预加载音效到缓存"""
        try:
            sound_info = self.config_manager.get_sound_info(sound_id)
            if not sound_info:
                return False
            
            sound_path = sound_info.get("path")
            if not sound_path or not os.path.exists(sound_path):
                return False
            
            # 由于playsound不支持预加载，这里只验证文件存在
            return True
            
        except Exception as e:
            self.logger.error(f"预加载音效失败 {sound_id}: {e}")
            return False
    
    def clear_cache(self):
        """清空音效缓存"""
        with self.cache_lock:
            self.sound_cache.clear()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        with self.cache_lock:
            return len(self.sound_cache)
    
    def validate_sound_file(self, file_path: str) -> bool:
        """验证音效文件是否有效"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.mp3'):
                return False
            
            # 检查文件大小（限制最大50MB）
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 50 * 1024 * 1024:  # 50MB
                    return False
            except OSError:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"音效文件验证失败 {file_path}: {e}")
            return False
    
    def get_sound_info(self, sound_path: str) -> Optional[Dict[str, Any]]:
        """获取音效文件信息"""
        try:
            if not os.path.exists(sound_path):
                return None
            
            info = {
                "path": sound_path,
                "filename": os.path.basename(sound_path),
                "size": os.path.getsize(sound_path),
                "duration": 0,  # playsound不支持获取音频信息
                "channels": 0,
                "sample_width": 0,
                "frame_rate": 0,
                "frame_count": 0
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取音效信息失败 {sound_path}: {e}")
            return None