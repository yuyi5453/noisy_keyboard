import string
from typing import Dict, Optional, List
from pathlib import Path
import logging


class KeyBindingManager:
    """按键绑定管理器，管理按键与音效的映射关系"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 默认音效ID
        self.default_sound_id = "default_sound_001"
        
        # 标准键盘按键列表
        self.standard_keys = self._get_standard_keys()
        
        # 初始化按键绑定
        self.initialize_key_bindings()
        
        self.logger.info("按键绑定管理器初始化完成")
    
    def _get_standard_keys(self) -> List[str]:
        """获取标准键盘按键列表"""
        keys = []
        
        # 字母键 a-z
        keys.extend(list(string.ascii_lowercase))
        
        # 数字键 0-9
        keys.extend([str(i) for i in range(10)])
        
        # 功能键 F1-F12
        keys.extend([f"f{i}" for i in range(1, 13)])
        
        # 特殊按键
        special_keys = [
            "space", "enter", "backspace", "tab", "escape",
            "shift", "ctrl", "alt", "cmd", "caps_lock",
            "left", "right", "up", "down",
            "home", "end", "page_up", "page_down",
            "insert", "delete", "print_screen", "scroll_lock", "pause",
            "num_lock", "num_0", "num_1", "num_2", "num_3", "num_4",
            "num_5", "num_6", "num_7", "num_8", "num_9",
            "num_add", "num_subtract", "num_multiply", "num_divide", "num_decimal",
            "`", "-", "=", "[", "]", "\\", ";", "'", ",", ".", "/"
        ]
        keys.extend(special_keys)
        
        return keys
    
    def initialize_key_bindings(self):
        """初始化按键绑定，将所有按键绑定到默认音效"""
        current_bindings = self.config_manager.get_all_key_bindings()
        
        # 如果还没有按键绑定，创建默认绑定
        if not current_bindings:
            default_bindings = {}
            
            # 获取默认音效
            sounds = self.config_manager.get_sound_library()
            if not sounds:
                # 如果没有音效，返回空绑定
                return
                
            # 使用第一个可用的音效作为默认音效
            default_sound_path = next(iter(sounds.values()))
            
            # 所有按键都绑定到默认音效
            for key in self.standard_keys:
                default_bindings[key] = default_sound_path
            
            # 保存默认绑定
            for key, sound_path in default_bindings.items():
                self.config_manager.set_key_sound(key, sound_path)
            
            self.logger.info(f"初始化 {len(default_bindings)} 个按键的默认绑定")
    
    def get_key_sound(self, key: str) -> Optional[str]:
        """获取按键绑定的音效ID"""
        # 标准化按键名称
        normalized_key = self._normalize_key(key)
        
        # 从配置中获取绑定
        sound_id = self.config_manager.get_key_binding(normalized_key)
        
        # 如果没有绑定，使用默认音效
        if not sound_id:
            sound_id = self.default_sound_id
        
        return sound_id
    
    def set_key_sound(self, key: str, sound_path: str) -> bool:
        """设置按键绑定的音效"""
        try:
            # 标准化按键名称
            normalized_key = self._normalize_key(key)
            
            # 设置按键绑定
            self.config_manager.set_key_sound(normalized_key, sound_path)
            self.logger.info(f"按键 {normalized_key} 绑定到音效 {sound_path or '无'}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置按键绑定失败: {e}")
            return False
    
    def set_all_keys_sound(self, sound_id: str) -> bool:
        """为所有按键设置同一个音效"""
        try:
            # 验证音效ID是否存在
            sound_info = self.config_manager.get_sound_info(sound_id)
            if not sound_info:
                self.logger.warning(f"音效ID {sound_id} 不存在")
                return False
            
            # 为所有标准按键设置绑定
            for key in self.standard_keys:
                self.config_manager.set_key_sound(key, sound_id)
            
            self.logger.info(f"所有按键绑定到音效 {sound_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"批量设置按键绑定失败: {e}")
            return False
    
    def reset_key_to_default(self, key: str) -> bool:
        """重置按键到默认音效"""
        return self.set_key_sound(key, self.default_sound_id)
    
    def reset_all_keys_to_default(self) -> bool:
        """重置所有按键到默认音效"""
        try:
            for key in self.standard_keys:
                self.config_manager.set_key_sound(key, self.default_sound_id)
            
            self.logger.info("所有按键重置为默认音效")
            return True
            
        except Exception as e:
            self.logger.error(f"重置所有按键绑定失败: {e}")
            return False
    
    def get_key_binding_info(self, key: str) -> Dict[str, str]:
        """获取按键绑定信息"""
        normalized_key = self._normalize_key(key)
        sound_id = self.get_key_sound(normalized_key)
        
        sound_info = self.config_manager.get_sound_info(sound_id)
        sound_name = sound_info.get("filename", "Unknown") if sound_info else "Unknown"
        
        return {
            "key": normalized_key,
            "sound_id": sound_id,
            "sound_name": sound_name
        }
    
    def get_all_key_bindings(self) -> Dict[str, Dict[str, str]]:
        """获取所有按键绑定信息"""
        bindings = {}
        
        for key in self.standard_keys:
            binding_info = self.get_key_binding_info(key)
            bindings[key] = binding_info
        
        return bindings
    
    def get_all_bindings(self) -> Dict[str, str]:
        """获取所有按键绑定信息（按键到音效路径的映射）"""
        # 直接返回按键到音效路径的映射
        return self.config_manager.get_key_bindings()
    
    def remove_sound_bindings(self, sound_path: str):
        """移除指定音效的所有按键绑定"""
        try:
            # 获取当前所有绑定
            bindings = self.config_manager.get_key_bindings()
            
            # 移除使用该音效的所有绑定
            keys_to_remove = [key for key, sound in bindings.items() if sound == sound_path]
            
            for key in keys_to_remove:
                # 重置为默认音效
                self.config_manager.set_key_sound(key, self.default_sound_id)
            
            if keys_to_remove:
                self.logger.info(f"移除了 {len(keys_to_remove)} 个按键的音效绑定")
                
        except Exception as e:
            self.logger.error(f"移除音效绑定失败: {e}")
    
    def _normalize_key(self, key: str) -> str:
        """标准化按键名称"""
        if not key:
            return "unknown"
        
        key = str(key).lower().strip()
        
        # 处理特殊按键名称
        key_mapping = {
            " ": "space",
            "space_bar": "space",
            "return": "enter",
            "back_space": "backspace",
            "del": "delete",
            "esc": "escape",
            "command": "cmd",
            "windows": "cmd",
            "win": "cmd",
            "option": "alt",
            "capslock": "caps_lock",
            "caps": "caps_lock",
            "pgup": "page_up",
            "pgdn": "page_down",
            "scrolllock": "scroll_lock",
            "scroll": "scroll_lock",
            "prtsc": "print_screen",
            "prtscr": "print_screen",
            "snapshot": "print_screen"
        }
        
        # 如果按键在映射表中，返回映射后的名称
        if key in key_mapping:
            return key_mapping[key]
        
        # 检查是否是数字键盘按键
        if key.startswith("numpad_") or key.startswith("num_"):
            num_key = key.replace("numpad_", "").replace("num_", "")
            if num_key.isdigit():
                return f"num_{num_key}"
            elif num_key in ["add", "subtract", "multiply", "divide", "decimal"]:
                return f"num_{num_key}"
        
        # 检查是否是功能键
        if key.startswith("f") and key[1:].isdigit():
            num = int(key[1:])
            if 1 <= num <= 12:
                return key
        
        # 返回原始按键名称（小写）
        return key
    
    def is_valid_key(self, key: str) -> bool:
        """检查是否为有效的按键"""
        normalized_key = self._normalize_key(key)
        return normalized_key in self.standard_keys
    
    def get_key_display_name(self, key: str) -> str:
        """获取按键的显示名称"""
        normalized_key = self._normalize_key(key)
        
        # 显示名称映射
        display_names = {
            "space": "Space",
            "enter": "Enter",
            "backspace": "Backspace",
            "tab": "Tab",
            "escape": "Esc",
            "shift": "Shift",
            "ctrl": "Ctrl",
            "alt": "Alt",
            "cmd": "Cmd",
            "caps_lock": "Caps Lock",
            "left": "←",
            "right": "→",
            "up": "↑",
            "down": "↓",
            "home": "Home",
            "end": "End",
            "page_up": "Page Up",
            "page_down": "Page Down",
            "insert": "Insert",
            "delete": "Delete",
            "print_screen": "PrtSc",
            "scroll_lock": "Scroll Lock",
            "pause": "Pause",
            "num_lock": "Num Lock"
        }
        
        # 如果是功能键
        if normalized_key.startswith("f") and normalized_key[1:].isdigit():
            return normalized_key.upper()
        
        # 如果是数字键盘按键
        if normalized_key.startswith("num_"):
            num_part = normalized_key.replace("num_", "")
            if num_part.isdigit():
                return f"Num {num_part}"
            else:
                num_symbols = {
                    "add": "Num +",
                    "subtract": "Num -",
                    "multiply": "Num *",
                    "divide": "Num /",
                    "decimal": "Num ."
                }
                return num_symbols.get(num_part, normalized_key)
        
        # 返回显示名称或原始名称
        return display_names.get(normalized_key, normalized_key.upper())