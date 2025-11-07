#!/usr/bin/env python3
"""
Noisy Keyboard - 机械键盘音效模拟器

一个macOS应用程序，通过监听键盘事件来播放相应的音效，
模拟机械键盘的声音体验。
"""

import sys
import os
import logging
import signal
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 导入核心模块
from core.config_manager import ConfigManager
from core.sound_manager import SoundManager
from core.key_binding import KeyBindingManager
from core.keyboard_listener import KeyboardListener
from ui.main_window import MainWindow


def setup_logging():
    """设置日志配置"""
    log_dir = Path.home() / ".noisy_keyboard" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "noisy_keyboard.log"
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 设置日志级别和输出
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 设置PyQt日志级别
    logging.getLogger('PyQt6').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("=== Noisy Keyboard 启动 ===")
    logger.info(f"日志文件: {log_file}")
    
    return logger


def check_dependencies():
    """检查依赖项"""
    logger = logging.getLogger(__name__)
    
    try:
        import PyQt6
        logger.info(f"PyQt6 版本: {PyQt6.QtCore.PYQT_VERSION_STR}")
    except ImportError as e:
        logger.error(f"PyQt6 导入失败: {e}")
        return False
        
    try:
        import pynput
        version = getattr(pynput, '__version__', '未知版本')
        logger.info(f"pynput 版本: {version}")
    except ImportError as e:
        logger.error(f"pynput 导入失败: {e}")
        return False
        
    # pydub已移除，跳过检查
    logger.info("音频处理库: playsound (已移除pydub)")
        
    return True


def setup_signal_handlers(app: QApplication):
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"收到信号 {signum}，正在关闭应用...")
        app.quit()
        
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def create_default_sound():
    """创建默认音效文件"""
    logger = logging.getLogger(__name__)
    
    # 默认音效文件路径
    default_sound_path = Path("resources/space-animal-104986.mp3")
    
    if not default_sound_path.exists():
        logger.warning(f"默认音效文件不存在: {default_sound_path}")
        
        # 检查用户指定的路径
        user_path = Path("/Users/bytedance/Code/Python/noisy_keyboard/resource/space-animal-104986.mp3")
        if user_path.exists():
            logger.info(f"使用用户指定路径: {user_path}")
            return str(user_path)
        else:
            logger.warning("默认音效文件不存在，需要用户手动添加音效")
            return None
            
    return str(default_sound_path)


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，请确保已安装所有必需的依赖包")
        print("错误：缺少依赖包，请运行: uv pip install -r requirements.txt")
        sys.exit(1)
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("Noisy Keyboard")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NoisyKeyboard")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 设置信号处理器
    setup_signal_handlers(app)
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        logger.info("配置管理器初始化完成")
        
        # 创建默认音效
        default_sound_path = create_default_sound()
        if default_sound_path:
            # 添加默认音效到音效库
            default_sound_info = {
                "id": "default_sound_001",
                "filename": "space-animal-104986.mp3",
                "path": default_sound_path,
                "size": os.path.getsize(default_sound_path),
                "upload_time": "2024-01-01 12:00:00"
            }
            config_manager.add_sound_to_library(default_sound_info)
            logger.info("默认音效已添加到音效库")
        
        # 初始化音效管理器
        sound_manager = SoundManager()
        logger.info("音效管理器初始化完成")
        
        # 初始化按键绑定管理器
        key_binding_manager = KeyBindingManager(config_manager)
        
        # 加载配置中的绑定
        key_bindings = config_manager.get_key_bindings()
        if key_bindings:
            for key_name, sound_path in key_bindings.items():
                key_binding_manager.set_key_sound(key_name, sound_path)
            logger.info(f"已加载 {len(key_bindings)} 个按键绑定")
        else:
            # 如果没有绑定，设置默认绑定
            if default_sound_path:
                # 为常用按键设置默认绑定
                common_keys = ["space", "enter", "backspace", "tab", "a", "s", "d", "w"]
                for key in common_keys:
                    key_binding_manager.set_key_sound(key, default_sound_path)
                logger.info("已为常用按键设置默认音效绑定")
        
        logger.info("按键绑定管理器初始化完成")
        
        # 初始化键盘监听器
        keyboard_listener = KeyboardListener(key_binding_manager, sound_manager)
        logger.info("键盘监听器初始化完成")
        
        # 创建主窗口
        main_window = MainWindow(
            config_manager,
            sound_manager,
            key_binding_manager,
            keyboard_listener
        )
        
        # 显示主窗口
        main_window.show()
        
        logger.info("Noisy Keyboard 应用启动成功")
        
        # 运行应用
        exit_code = app.exec()
        
        # 清理资源
        logger.info("正在清理资源...")
        keyboard_listener.stop_listening()
        config_manager.save_config()
        
        logger.info("=== Noisy Keyboard 关闭 ===")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("用户中断应用")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        print(f"错误: 应用启动失败 - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()