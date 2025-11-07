import sys
import os
import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QCheckBox, QListWidget, QListWidgetItem, 
                             QGroupBox, QMessageBox, QFileDialog, QMenuBar, 
                             QMenu, QStatusBar, QSystemTrayIcon, QStyle)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QPixmap, QFont

from core.config_manager import ConfigManager
from core.sound_manager import SoundManager
from core.key_binding import KeyBindingManager
from core.keyboard_listener import KeyboardListener

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    key_pressed = pyqtSignal(str)
    
    def __init__(self, config_manager, sound_manager, key_binding_manager, keyboard_listener):
        super().__init__()
        self.config_manager = config_manager
        self.sound_manager = sound_manager
        self.key_binding_manager = key_binding_manager
        self.keyboard_listener = keyboard_listener
        
        # 设置键盘监听器回调
        self.keyboard_listener.set_key_callback(self._on_key_pressed)
        
        # 初始化UI
        self.init_ui()
        
        # 启动键盘监听
        self.keyboard_listener.start_listening()
        
        # 设置日志显示定时器
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_status)
        self.log_timer.start(1000)  # 每秒更新一次
        
    def _init_managers(self):
        """初始化各个管理器"""
        try:
            # 加载配置
            config = self.config_manager.load_config()
            
            # 加载按键绑定
            key_bindings = self.config_manager.get_key_bindings()
            self.key_binding_manager.load_bindings(key_bindings)
            
            # 设置音量
            volume = self.config_manager.get_volume()
            self.sound_manager.set_volume(volume)
            
            # 设置启用状态
            enabled = self.config_manager.is_enabled()
            self.keyboard_listener.set_enabled(enabled)
            
        except Exception as e:
            logger.error(f"初始化管理器失败: {e}")
            QMessageBox.critical(self, "错误", f"初始化失败: {e}")
            
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Noisy Keyboard - 机械键盘音效")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置应用图标
        self.set_window_icon()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建系统托盘
        self.create_system_tray()
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        # 应用当前配置到UI
        self.apply_config_to_ui()
        
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 创建简单的图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.blue)
            icon = QIcon(pixmap)
            self.setWindowIcon(icon)
        except Exception as e:
            logger.error(f"设置窗口图标失败: {e}")
            
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 添加音效库文件
        add_sound_action = QAction("添加音效文件", self)
        add_sound_action.triggered.connect(self.add_sound_file)
        file_menu.addAction(add_sound_action)
        
        # 添加自定义音效路径
        add_custom_sound_action = QAction("添加自定义音效路径", self)
        add_custom_sound_action.triggered.connect(self.add_custom_sound_path)
        file_menu.addAction(add_custom_sound_action)
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 按键绑定设置
        key_binding_action = QAction("按键绑定设置", self)
        key_binding_action.triggered.connect(self.open_key_binding_dialog)
        settings_menu.addAction(key_binding_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 添加状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: green; font-size: 16px;")
        self.status_bar.addPermanentWidget(self.status_indicator)
        
    def create_system_tray(self):
        """创建系统托盘图标"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.windowIcon())
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            show_action = QAction("显示主窗口", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_activated)
            self.tray_icon.show()
            
        except Exception as e:
            logger.error(f"创建系统托盘失败: {e}")
            
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 主控制组
        control_group = QGroupBox("主控制")
        control_layout = QVBoxLayout(control_group)
        
        # 启用/禁用开关
        self.enable_checkbox = QCheckBox("启用音效")
        self.enable_checkbox.stateChanged.connect(self.on_enable_changed)
        control_layout.addWidget(self.enable_checkbox)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("50%")
        volume_layout.addWidget(self.volume_label)
        control_layout.addLayout(volume_layout)
        
        layout.addWidget(control_group)
        
        # 统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_keys_label = QLabel("总按键数: 0")
        stats_layout.addWidget(self.total_keys_label)
        
        self.active_keys_label = QLabel("活跃按键: 0")
        stats_layout.addWidget(self.active_keys_label)
        
        self.sounds_loaded_label = QLabel("已加载音效: 0")
        stats_layout.addWidget(self.sounds_loaded_label)
        
        layout.addWidget(stats_group)
        
        # 最近按键组
        recent_group = QGroupBox("最近按键")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_keys_list = QListWidget()
        self.recent_keys_list.setMaximumHeight(150)
        recent_layout.addWidget(self.recent_keys_list)
        
        layout.addWidget(recent_group)
        
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 音效库组
        sound_library_group = QGroupBox("音效库")
        sound_layout = QVBoxLayout(sound_library_group)
        
        # 音效列表
        self.sound_list = QListWidget()
        self.sound_list.itemDoubleClicked.connect(self.on_sound_double_clicked)
        sound_layout.addWidget(self.sound_list)
        
        # 音效控制按钮
        sound_buttons_layout = QHBoxLayout()
        
        # 新增音效按钮
        self.add_sound_btn = QPushButton("新增音效")
        self.add_sound_btn.clicked.connect(self.add_sound_file)
        sound_buttons_layout.addWidget(self.add_sound_btn)
        
        # 删除音效按钮
        self.delete_sound_btn = QPushButton("删除音效")
        self.delete_sound_btn.clicked.connect(self.delete_selected_sound)
        sound_buttons_layout.addWidget(self.delete_sound_btn)
        
        self.play_sound_btn = QPushButton("播放")
        self.play_sound_btn.clicked.connect(self.play_selected_sound)
        sound_buttons_layout.addWidget(self.play_sound_btn)
        
        self.test_key_btn = QPushButton("测试按键")
        self.test_key_btn.clicked.connect(self.test_key_binding)
        sound_buttons_layout.addWidget(self.test_key_btn)
        
        sound_layout.addLayout(sound_buttons_layout)
        
        layout.addWidget(sound_library_group)
        
        # 按键绑定组
        key_binding_group = QGroupBox("按键绑定")
        key_binding_layout = QVBoxLayout(key_binding_group)
        
        # 按键绑定列表
        self.key_binding_list = QListWidget()
        self.key_binding_list.itemDoubleClicked.connect(self.on_key_binding_double_clicked)
        key_binding_layout.addWidget(self.key_binding_list)
        
        # 按键绑定控制按钮
        key_buttons_layout = QHBoxLayout()
        
        self.edit_binding_btn = QPushButton("编辑绑定")
        self.edit_binding_btn.clicked.connect(self.open_key_binding_dialog)
        key_buttons_layout.addWidget(self.edit_binding_btn)
        
        self.refresh_bindings_btn = QPushButton("刷新")
        self.refresh_bindings_btn.clicked.connect(self.refresh_key_bindings)
        key_buttons_layout.addWidget(self.refresh_bindings_btn)
        
        key_binding_layout.addLayout(key_buttons_layout)
        
        layout.addWidget(key_binding_group)
        
        return panel
        
    def apply_config_to_ui(self):
        """将配置应用到UI"""
        try:
            # 启用状态
            enabled = self.config_manager.is_enabled()
            self.enable_checkbox.setChecked(enabled)
            
            # 音量
            volume = self.config_manager.get_volume()
            self.volume_slider.setValue(int(volume * 100))
            self.volume_label.setText(f"{int(volume * 100)}%")
            self.sound_manager.set_volume(volume)
            
            # 刷新音效库和按键绑定显示
            self.refresh_sound_library()
            self.refresh_key_bindings()
            
            # 更新统计信息
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"应用配置到UI失败: {e}")
            
    def on_enable_changed(self, state):
        """启用状态改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.keyboard_listener.set_enabled(enabled)
        self.config_manager.set_enabled(enabled)
        self.config_manager.save_config()
        
        # 更新状态指示器
        if enabled:
            self.status_indicator.setStyleSheet("color: green; font-size: 16px;")
            self.status_label.setText("音效已启用")
        else:
            self.status_indicator.setStyleSheet("color: gray; font-size: 16px;")
            self.status_label.setText("音效已禁用")
            
    def on_volume_changed(self, value):
        """音量改变"""
        volume = value / 100.0
        self.sound_manager.set_volume(volume)
        self.config_manager.set_volume(volume)
        self.volume_label.setText(f"{value}%")
        
    def _on_key_pressed(self, key_name: str):
        """按键按下事件"""
        # 更新最近按键列表
        self.update_recent_keys(key_name)
        
        # 更新统计信息
        self.update_statistics()
        
        # 在状态栏显示
        self.status_label.setText(f"按键: {key_name}")
        
    def update_recent_keys(self, key_name: str):
        """更新最近按键列表"""
        # 添加新按键到列表顶部
        self.recent_keys_list.insertItem(0, f"{key_name}")
        
        # 限制列表长度
        max_items = 10
        while self.recent_keys_list.count() > max_items:
            self.recent_keys_list.takeItem(self.recent_keys_list.count() - 1)
            
    def update_statistics(self):
        """更新统计信息"""
        try:
            # 获取按键绑定统计
            bindings = self.key_binding_manager.get_all_bindings()
            active_keys = len([k for k, v in bindings.items() if v is not None])
            
            self.total_keys_label.setText(f"总按键数: {len(bindings)}")
            self.active_keys_label.setText(f"活跃按键: {active_keys}")
            
            # 获取音效统计
            sounds = self.config_manager.get_sound_library()
            self.sounds_loaded_label.setText(f"已加载音效: {len(sounds)}")
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
            
    def refresh_sound_library(self):
        """刷新音效库显示"""
        try:
            self.sound_list.clear()
            sounds = self.config_manager.get_sound_library()
            
            for sound_name, sound_path in sounds.items():
                item = QListWidgetItem(f"{sound_name} - {sound_path}")
                item.setData(Qt.ItemDataRole.UserRole, sound_path)
                self.sound_list.addItem(item)
                
        except Exception as e:
            logger.error(f"刷新音效库失败: {e}")
            
    def refresh_key_bindings(self):
        """刷新按键绑定显示"""
        try:
            self.key_binding_list.clear()
            bindings = self.key_binding_manager.get_all_bindings()
            
            for key_name, sound_path in bindings.items():
                if sound_path:
                    sound_name = self.config_manager.get_sound_name_by_path(sound_path)
                    display_text = f"{key_name} → {sound_name or '未知音效'}"
                else:
                    display_text = f"{key_name} → 未绑定"
                    
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, key_name)
                self.key_binding_list.addItem(item)
                
            # 更新统计信息
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"刷新按键绑定失败: {e}")
            
    def play_selected_sound(self):
        """播放选中的音效"""
        try:
            current_item = self.sound_list.currentItem()
            if current_item:
                sound_path = current_item.data(Qt.ItemDataRole.UserRole)
                if sound_path:
                    self.sound_manager.play_sound(sound_path)
                    self.status_label.setText("播放音效")
                    
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
            QMessageBox.warning(self, "警告", f"播放音效失败: {e}")
            
    def test_key_binding(self):
        """测试按键绑定"""
        try:
            # 显示输入对话框
            from PyQt6.QtWidgets import QInputDialog
            key, ok = QInputDialog.getText(self, "测试按键", "请输入要测试的按键:")
            
            if ok and key:
                key = key.lower().strip()
                sound_path = self.key_binding_manager.get_key_sound(key)
                
                if sound_path:
                    self.sound_manager.play_sound(sound_path)
                    self.status_label.setText(f"测试按键: {key}")
                else:
                    QMessageBox.information(self, "信息", f"按键 '{key}' 未绑定音效")
                    
        except Exception as e:
            logger.error(f"测试按键绑定失败: {e}")
            
    def on_sound_double_clicked(self, item):
        """音效双击事件"""
        self.play_selected_sound()
        
    def on_key_binding_double_clicked(self, item):
        """按键绑定双击事件"""
        key_name = item.data(Qt.ItemDataRole.UserRole)
        if key_name:
            self.open_key_binding_dialog_with_key(key_name)
            
    def add_sound_file(self):
        """添加音效文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择音效文件",
                "",
                "MP3文件 (*.mp3);;所有文件 (*.*)"
            )
            
            if file_path:
                # 使用配置管理器添加自定义音效路径
                if self.config_manager.add_custom_sound_path(file_path):
                    self.config_manager.save_config()
                    self.refresh_sound_library()
                    self.status_label.setText(f"已添加音效: {os.path.basename(file_path)}")
                else:
                    QMessageBox.warning(
                        self,
                        "添加失败",
                        "无法添加该音效文件。\n可能的原因：\n"
                        "- 文件不存在或不是MP3格式\n"
                        "- 文件已存在于音效库中\n"
                        "- 文件大小超过50MB限制"
                    )
                
        except Exception as e:
            logger.error(f"添加音效文件失败: {e}")
            QMessageBox.warning(self, "警告", f"添加音效文件失败: {e}")

    def add_custom_sound_path(self):
        """添加自定义音效路径"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择MP3音效文件",
                "",
                "MP3文件 (*.mp3);;所有文件 (*.*)"
            )
            
            if file_path:
                # 使用配置管理器添加自定义路径
                if self.config_manager.add_custom_sound_path(file_path):
                    self.config_manager.save_config()
                    self.refresh_sound_library()
                    self.status_label.setText(f"已添加自定义音效: {os.path.basename(file_path)}")
                else:
                    QMessageBox.warning(
                        self,
                        "添加失败",
                        "无法添加该音效文件。\n可能的原因：\n"
                        "- 文件不存在或不是MP3格式\n"
                        "- 文件已存在于音效库中\n"
                        "- 文件大小超过50MB限制"
                    )
                    
        except Exception as e:
            logger.error(f"添加自定义音效路径失败: {e}")
            QMessageBox.warning(self, "警告", f"添加自定义音效路径失败: {e}")
            
    def delete_selected_sound(self):
        """删除选中的音效"""
        try:
            current_item = self.sound_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择一个音效")
                return
                
            sound_path = current_item.data(Qt.ItemDataRole.UserRole)
            if not sound_path:
                QMessageBox.warning(self, "警告", "无法获取音效路径")
                return
                
            # 获取音效名称
            sound_name = os.path.basename(sound_path)
            
            # 确认删除对话框
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除音效 '{sound_name}' 吗？\n\n"
                "注意：\n"
                "- 删除音效将同时移除相关的按键绑定\n"
                "- 自定义路径的音效文件不会被删除\n"
                "- 内置音效文件将保留在系统中",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 删除音效
                if self.config_manager.remove_sound_from_library(sound_path):
                    # 移除相关的按键绑定
                    self.key_binding_manager.remove_sound_bindings(sound_path)
                    
                    # 保存配置
                    self.config_manager.save_config()
                    
                    # 刷新显示
                    self.refresh_sound_library()
                    self.refresh_key_bindings()
                    self.update_statistics()
                    
                    self.status_label.setText(f"已删除音效: {sound_name}")
                    logger.info(f"音效已删除: {sound_name}")
                else:
                    QMessageBox.warning(self, "删除失败", "无法删除该音效")
                    
        except Exception as e:
            logger.error(f"删除音效失败: {e}")
            QMessageBox.warning(self, "警告", f"删除音效失败: {e}")
            
    def open_key_binding_dialog(self):
        """打开按键绑定设置对话框"""
        try:
            from ui.key_binding_dialog import KeyBindingDialog
            dialog = KeyBindingDialog(
                self.key_binding_manager,
                self.config_manager,
                self
            )
            
            if dialog.exec():
                # 刷新按键绑定显示
                self.refresh_key_bindings()
                self.update_statistics()
                
        except Exception as e:
            logger.error(f"打开按键绑定对话框失败: {e}")
            
    def open_key_binding_dialog_with_key(self, key_name: str):
        """打开特定按键的绑定设置对话框"""
        try:
            from ui.key_binding_dialog import KeyBindingDialog
            dialog = KeyBindingDialog(
                self.key_binding_manager,
                self.config_manager,
                self,
                selected_key=key_name
            )
            
            if dialog.exec():
                # 刷新按键绑定显示
                self.refresh_key_bindings()
                self.update_statistics()
                
        except Exception as e:
            logger.error(f"打开按键绑定对话框失败: {e}")
            
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 Noisy Keyboard",
            "Noisy Keyboard v1.0\n\n"
            "机械键盘音效模拟器\n\n"
            "为每个按键绑定独特的音效，\n"
            "让您的打字体验更加有趣！"
        )
        
    def tray_activated(self, reason):
        """系统托盘激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.raise_()
            self.activateWindow()
            
    def update_status(self):
        """更新状态"""
        try:
            # 获取监听器状态
            status = self.keyboard_listener.get_status()
            
            # 更新状态栏
            if status["is_listening"]:
                if status["enabled"]:
                    self.status_label.setText("监听中 - 音效已启用")
                else:
                    self.status_label.setText("监听中 - 音效已禁用")
            else:
                self.status_label.setText("监听器未运行")
                
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
            
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 停止键盘监听
            self.keyboard_listener.stop_listening()
            
            # 保存配置
            self.config_manager.save_config()
            
            # 隐藏系统托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
                
            logger.info("应用已关闭")
            
        except Exception as e:
            logger.error(f"关闭应用时出错: {e}")
            
        event.accept()