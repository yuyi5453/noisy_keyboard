import threading
import logging
from typing import Callable, Optional, Dict, Any
from pynput import keyboard
from pynput.keyboard import Key, Listener, KeyCode

logger = logging.getLogger(__name__)


class KeyboardListener:
    """键盘监听器，负责监听键盘事件并触发相应的音效"""
    
    def __init__(self, key_binding_manager, sound_manager):
        """
        初始化键盘监听器
        
        Args:
            key_binding_manager: 按键绑定管理器
            sound_manager: 音效管理器
        """
        self.key_binding_manager = key_binding_manager
        self.sound_manager = sound_manager
        self.listener: Optional[Listener] = None
        self.is_listening = False
        self.enabled = False
        self.on_key_callback: Optional[Callable[[str], None]] = None
        
    def set_enabled(self, enabled: bool) -> None:
        """设置监听器是否启用"""
        self.enabled = enabled
        logger.info(f"键盘监听器 {'启用' if enabled else '禁用'}")
        
    def start_listening(self) -> None:
        """开始监听键盘事件"""
        if self.is_listening:
            logger.warning("键盘监听器已经在运行")
            return
            
        try:
            self.listener = Listener(
                on_press=self._on_key_press,
                on_release=None,
                suppress=False
            )
            self.listener.start()
            self.is_listening = True
            logger.info("键盘监听器已启动")
        except Exception as e:
            logger.error(f"启动键盘监听器失败: {e}")
            raise
            
    def stop_listening(self) -> None:
        """停止监听键盘事件"""
        if not self.is_listening or not self.listener:
            return
            
        try:
            self.listener.stop()
            self.listener.join(timeout=2)
            self.listener = None
            self.is_listening = False
            logger.info("键盘监听器已停止")
        except Exception as e:
            logger.error(f"停止键盘监听器失败: {e}")
            
    def _normalize_key(self, key) -> str:
        """
        标准化按键名称
        
        Args:
            key: 按键对象
            
        Returns:
            str: 标准化的按键名称
        """
        try:
            if isinstance(key, KeyCode):
                # 字母数字键
                if key.char:
                    return key.char.lower()
                else:
                    return f"key_{key.vk}"
            elif isinstance(key, Key):
                # 特殊键
                key_names = {
                    Key.space: "space",
                    Key.enter: "enter",
                    Key.tab: "tab",
                    Key.backspace: "backspace",
                    Key.delete: "delete",
                    Key.esc: "esc",
                    Key.up: "up",
                    Key.down: "down",
                    Key.left: "left",
                    Key.right: "right",
                    Key.home: "home",
                    Key.end: "end",
                    Key.page_up: "page_up",
                    Key.page_down: "page_down",
                    Key.caps_lock: "caps_lock",
                    Key.shift: "shift",
                    Key.shift_r: "shift_r",
                    Key.ctrl: "ctrl",
                    Key.ctrl_r: "ctrl_r",
                    Key.alt: "alt",
                    Key.alt_r: "alt_r",
                    Key.cmd: "cmd",
                    Key.cmd_r: "cmd_r",
                    Key.f1: "f1",
                    Key.f2: "f2",
                    Key.f3: "f3",
                    Key.f4: "f4",
                    Key.f5: "f5",
                    Key.f6: "f6",
                    Key.f7: "f7",
                    Key.f8: "f8",
                    Key.f9: "f9",
                    Key.f10: "f10",
                    Key.f11: "f11",
                    Key.f12: "f12",
                }
                return key_names.get(key, str(key).replace("Key.", ""))
            else:
                return str(key)
        except Exception as e:
            logger.error(f"标准化按键失败: {e}")
            return str(key)
            
    def _on_key_press(self, key) -> None:
        """
        按键按下事件处理
        
        Args:
            key: 按键对象
        """
        if not self.enabled:
            return
            
        try:
            # 标准化按键名称
            key_name = self._normalize_key(key)
            logger.debug(f"按键按下: {key_name}")
            
            # 调用回调函数（用于UI显示）
            if self.on_key_callback:
                self.on_key_callback(key_name)
                
            # 获取按键绑定的音效
            sound_path = self.key_binding_manager.get_key_sound(key_name)
            if sound_path:
                # 异步播放音效
                threading.Thread(
                    target=self.sound_manager.play_sound,
                    args=(sound_path,),
                    daemon=True
                ).start()
            else:
                logger.debug(f"按键 {key_name} 未绑定音效")
                
        except Exception as e:
            logger.error(f"处理按键事件失败: {e}")
            
    def set_key_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        """
        设置按键回调函数
        
        Args:
            callback: 回调函数，接收按键名称作为参数
        """
        self.on_key_callback = callback
        
    def get_status(self) -> Dict[str, Any]:
        """获取监听器状态"""
        return {
            "is_listening": self.is_listening,
            "enabled": self.enabled,
            "listener_thread": self.listener.is_alive() if self.listener else False
        }