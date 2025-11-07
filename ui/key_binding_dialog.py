import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QListWidget, 
                             QListWidgetItem, QGroupBox, QLineEdit, 
                             QSplitter, QMessageBox, QCheckBox, QScrollArea,
                             QFrame, QGridLayout, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

logger = logging.getLogger(__name__)


class KeyBindingWidget(QWidget):
    """按键绑定设置组件"""
    
    # 信号定义
    binding_changed = pyqtSignal(str, str)  # key_name, sound_path
    bindings_updated = pyqtSignal()  # 批量更新完成
    
    def __init__(self, key_binding_manager, config_manager, parent=None):
        super().__init__(parent)
        self.key_binding_manager = key_binding_manager
        self.config_manager = config_manager
        self.selected_key = None
        self.init_ui()
        self.refresh_bindings()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 顶部控制区
        control_layout = QHBoxLayout()
        
        # 快速搜索
        control_layout.addWidget(QLabel("搜索按键:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入按键名称...")
        self.search_edit.textChanged.connect(self.filter_keys)
        control_layout.addWidget(self.search_edit)
        
        control_layout.addStretch()
        
        # 批量操作
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_keys)
        control_layout.addWidget(self.select_all_btn)
        
        self.clear_all_btn = QPushButton("清除所有绑定")
        self.clear_all_btn.clicked.connect(self.clear_all_bindings)
        control_layout.addWidget(self.clear_all_btn)
        
        self.apply_to_all_btn = QPushButton("应用到所有按键")
        self.apply_to_all_btn.clicked.connect(self.apply_to_all_keys)
        control_layout.addWidget(self.apply_to_all_btn)
        
        layout.addLayout(control_layout)
        
        # 主内容区 - 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧按键列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 按键分类标签
        self.key_categories = QTabWidget()
        self.create_key_categories()
        left_layout.addWidget(self.key_categories)
        
        splitter.addWidget(left_widget)
        
        # 右侧绑定设置区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 当前选中按键信息
        self.selected_key_group = QGroupBox("当前按键")
        selected_key_layout = QVBoxLayout(self.selected_key_group)
        
        self.selected_key_label = QLabel("未选择按键")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.selected_key_label.setFont(font)
        selected_key_layout.addWidget(self.selected_key_label)
        
        self.key_description_label = QLabel("请从左侧选择一个按键")
        self.key_description_label.setStyleSheet("color: gray;")
        selected_key_layout.addWidget(self.key_description_label)
        
        right_layout.addWidget(self.selected_key_group)
        
        # 音效选择区
        sound_group = QGroupBox("音效绑定")
        sound_layout = QVBoxLayout(sound_group)
        
        # 音效选择下拉框
        sound_select_layout = QHBoxLayout()
        sound_select_layout.addWidget(QLabel("选择音效:"))
        self.sound_combo = QComboBox()
        self.sound_combo.currentTextChanged.connect(self.on_sound_selected)
        sound_select_layout.addWidget(self.sound_combo)
        
        self.play_sound_btn = QPushButton("测试播放")
        self.play_sound_btn.clicked.connect(self.test_play_sound)
        sound_select_layout.addWidget(self.play_sound_btn)
        
        sound_layout.addLayout(sound_select_layout)
        
        # 当前绑定显示
        self.current_binding_label = QLabel("当前绑定: 无")
        self.current_binding_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        sound_layout.addWidget(self.current_binding_label)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.apply_binding_btn = QPushButton("应用绑定")
        self.apply_binding_btn.clicked.connect(self.apply_current_binding)
        self.apply_binding_btn.setEnabled(False)
        button_layout.addWidget(self.apply_binding_btn)
        
        self.clear_binding_btn = QPushButton("清除绑定")
        self.clear_binding_btn.clicked.connect(self.clear_current_binding)
        self.clear_binding_btn.setEnabled(False)
        button_layout.addWidget(self.clear_binding_btn)
        
        button_layout.addStretch()
        
        sound_layout.addLayout(button_layout)
        
        right_layout.addWidget(sound_group)
        
        # 快速设置区
        quick_set_group = QGroupBox("快速设置")
        quick_set_layout = QVBoxLayout(quick_set_group)
        
        # 预设方案
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设方案:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["自定义", "机械键盘", "薄膜键盘", "游戏键盘"])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        
        quick_set_layout.addLayout(preset_layout)
        
        # 常用音效快速分配
        common_sounds_layout = QGridLayout()
        
        common_sounds = [
            ("空格键", "space"),
            ("回车键", "enter"),
            ("退格键", "backspace"),
            ("字母键", "a"),
            ("数字键", "1"),
            ("功能键", "f1")
        ]
        
        for i, (label, key) in enumerate(common_sounds):
            row = i // 2
            col = i % 2
            
            btn = QPushButton(f"设置{label}")
            btn.clicked.connect(lambda checked, k=key: self.quick_set_key(k))
            common_sounds_layout.addWidget(btn, row, col)
            
        quick_set_layout.addLayout(common_sounds_layout)
        
        right_layout.addWidget(quick_set_group)
        
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        
        # 初始化音效列表
        self.refresh_sound_list()
        
    def create_key_categories(self):
        """创建按键分类"""
        # 字母键
        letter_widget = QWidget()
        letter_layout = QVBoxLayout(letter_widget)
        
        letter_scroll = QScrollArea()
        letter_scroll.setWidgetResizable(True)
        
        letter_content = QWidget()
        letter_grid = QGridLayout(letter_content)
        
        letters = "abcdefghijklmnopqrstuvwxyz"
        for i, letter in enumerate(letters):
            row = i // 6
            col = i % 6
            btn = self.create_key_button(letter)
            letter_grid.addWidget(btn, row, col)
            
        letter_scroll.setWidget(letter_content)
        letter_layout.addWidget(letter_scroll)
        
        self.key_categories.addTab(letter_widget, "字母键")
        
        # 数字键
        number_widget = QWidget()
        number_layout = QVBoxLayout(number_widget)
        
        number_scroll = QScrollArea()
        number_scroll.setWidgetResizable(True)
        
        number_content = QWidget()
        number_grid = QGridLayout(number_content)
        
        numbers = "0123456789"
        for i, number in enumerate(numbers):
            row = i // 5
            col = i % 5
            btn = self.create_key_button(number)
            number_grid.addWidget(btn, row, col)
            
        number_scroll.setWidget(number_content)
        number_layout.addWidget(number_scroll)
        
        self.key_categories.addTab(number_widget, "数字键")
        
        # 功能键
        func_widget = QWidget()
        func_layout = QVBoxLayout(func_widget)
        
        func_scroll = QScrollArea()
        func_scroll.setWidgetResizable(True)
        
        func_content = QWidget()
        func_grid = QGridLayout(func_content)
        
        func_keys = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]
        for i, func_key in enumerate(func_keys):
            row = i // 4
            col = i % 4
            btn = self.create_key_button(func_key)
            func_grid.addWidget(btn, row, col)
            
        func_scroll.setWidget(func_content)
        func_layout.addWidget(func_scroll)
        
        self.key_categories.addTab(func_widget, "功能键")
        
        # 特殊键
        special_widget = QWidget()
        special_layout = QVBoxLayout(special_widget)
        
        special_scroll = QScrollArea()
        special_scroll.setWidgetResizable(True)
        
        special_content = QWidget()
        special_grid = QGridLayout(special_content)
        
        special_keys = ["space", "enter", "tab", "backspace", "delete", "esc", 
                       "shift", "ctrl", "alt", "cmd", "caps_lock"]
        for i, special_key in enumerate(special_keys):
            row = i // 4
            col = i % 4
            btn = self.create_key_button(special_key)
            special_grid.addWidget(btn, row, col)
            
        special_scroll.setWidget(special_content)
        special_layout.addWidget(special_scroll)
        
        self.key_categories.addTab(special_widget, "特殊键")
        
        # 方向键
        arrow_widget = QWidget()
        arrow_layout = QVBoxLayout(arrow_widget)
        
        arrow_scroll = QScrollArea()
        arrow_scroll.setWidgetResizable(True)
        
        arrow_content = QWidget()
        arrow_grid = QGridLayout(arrow_content)
        
        arrow_keys = ["up", "down", "left", "right", "home", "end", "page_up", "page_down"]
        for i, arrow_key in enumerate(arrow_keys):
            row = i // 4
            col = i % 4
            btn = self.create_key_button(arrow_key)
            arrow_grid.addWidget(btn, row, col)
            
        arrow_scroll.setWidget(arrow_content)
        arrow_layout.addWidget(arrow_scroll)
        
        self.key_categories.addTab(arrow_widget, "方向键")
        
    def create_key_button(self, key_name: str) -> QPushButton:
        """创建按键按钮"""
        btn = QPushButton(key_name.upper())
        btn.setCheckable(True)
        btn.setFixedSize(50, 40)
        btn.clicked.connect(lambda: self.select_key(key_name))
        
        # 设置按键样式
        self.update_key_button_style(btn, key_name)
        
        return btn
        
    def update_key_button_style(self, button: QPushButton, key_name: str):
        """更新按键按钮样式"""
        # 检查是否有绑定
        binding = self.key_binding_manager.get_key_sound(key_name)
        
        if binding:
            # 有绑定 - 绿色
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #45a049;
                    border-color: #4CAF50;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            # 无绑定 - 灰色
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #e0e0e0;
                    border: 2px solid #999;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            
    def select_key(self, key_name: str):
        """选择按键"""
        # 取消之前的选中状态
        if self.selected_key:
            self.update_key_selection(self.selected_key, False)
            
        # 设置新的选中状态
        self.selected_key = key_name
        self.update_key_selection(key_name, True)
        
        # 更新右侧信息
        self.update_selected_key_info(key_name)
        
        # 启用绑定按钮
        self.apply_binding_btn.setEnabled(True)
        self.clear_binding_btn.setEnabled(True)
        
    def update_key_selection(self, key_name: str, selected: bool):
        """更新按键选中状态"""
        # 在分类标签页中查找按钮
        for i in range(self.key_categories.count()):
            tab = self.key_categories.widget(i)
            buttons = tab.findChildren(QPushButton)
            for btn in buttons:
                if btn.text().lower() == key_name.lower():
                    btn.setChecked(selected)
                    break
                    
    def update_selected_key_info(self, key_name: str):
        """更新选中按键信息"""
        self.selected_key_label.setText(f"按键: {key_name.upper()}")
        
        # 获取当前绑定
        current_sound = self.key_binding_manager.get_key_sound(key_name)
        if current_sound:
            sound_name = self.config_manager.get_sound_name_by_path(current_sound)
            self.current_binding_label.setText(f"当前绑定: {sound_name or '未知音效'}")
            self.key_description_label.setText(f"已绑定到音效: {sound_name or '未知音效'}")
        else:
            self.current_binding_label.setText("当前绑定: 无")
            self.key_description_label.setText("此按键未绑定任何音效")
            
    def refresh_sound_list(self):
        """刷新音效列表"""
        self.sound_combo.clear()
        self.sound_combo.addItem("无音效", None)
        
        sounds = self.config_manager.get_sound_library()
        for sound_name, sound_path in sounds.items():
            self.sound_combo.addItem(sound_name, sound_path)
            
    def on_sound_selected(self, text: str):
        """音效选择事件"""
        # 音效选择在下拉框变化时处理
        pass
        
    def test_play_sound(self):
        """测试播放音效"""
        try:
            current_index = self.sound_combo.currentIndex()
            if current_index > 0:  # 不是"无音效"
                sound_path = self.sound_combo.currentData()
                if sound_path:
                    # 这里需要集成SoundManager
                    logger.info(f"测试播放音效: {sound_path}")
                    
        except Exception as e:
            logger.error(f"测试播放音效失败: {e}")
            
    def apply_current_binding(self):
        """应用当前绑定"""
        if not self.selected_key:
            return
            
        try:
            current_index = self.sound_combo.currentIndex()
            if current_index == 0:  # "无音效"
                sound_path = None
            else:
                sound_path = self.sound_combo.currentData()
                
            # 应用绑定 - 确保传递正确的路径字符串
            if sound_path:
                self.key_binding_manager.set_key_sound(self.selected_key, sound_path)
            else:
                self.key_binding_manager.set_key_sound(self.selected_key, None)
            
            # 更新UI
            self.update_selected_key_info(self.selected_key)
            self.update_key_button_style(
                self.find_key_button(self.selected_key), 
                self.selected_key
            )
            
            # 发送信号
            self.binding_changed.emit(self.selected_key, sound_path or "")
            
            logger.info(f"已绑定按键 {self.selected_key} 到音效 {sound_path}")
            
        except Exception as e:
            logger.error(f"应用绑定失败: {e}")
            
    def clear_current_binding(self):
        """清除当前绑定"""
        if not self.selected_key:
            return
            
        try:
            self.key_binding_manager.set_key_sound(self.selected_key, None)
            
            # 更新UI
            self.update_selected_key_info(self.selected_key)
            self.update_key_button_style(
                self.find_key_button(self.selected_key), 
                self.selected_key
            )
            
            # 发送信号
            self.binding_changed.emit(self.selected_key, "")
            
            logger.info(f"已清除按键 {self.selected_key} 的绑定")
            
        except Exception as e:
            logger.error(f"清除绑定失败: {e}")
            
    def find_key_button(self, key_name: str) -> Optional[QPushButton]:
        """查找按键按钮"""
        for i in range(self.key_categories.count()):
            tab = self.key_categories.widget(i)
            buttons = tab.findChildren(QPushButton)
            for btn in buttons:
                if btn.text().lower() == key_name.lower():
                    return btn
        return None
        
    def filter_keys(self, text: str):
        """过滤按键"""
        search_text = text.lower()
        
        for i in range(self.key_categories.count()):
            tab = self.key_categories.widget(i)
            buttons = tab.findChildren(QPushButton)
            
            for btn in buttons:
                key_name = btn.text().lower()
                if search_text in key_name:
                    btn.setVisible(True)
                else:
                    btn.setVisible(False)
                    
    def select_all_keys(self):
        """全选按键"""
        # 这里可以实现批量选择逻辑
        pass
        
    def clear_all_bindings(self):
        """清除所有绑定"""
        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除所有按键的音效绑定吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取所有按键
                all_keys = self.key_binding_manager.get_all_bindings().keys()
                
                # 清除所有绑定
                for key_name in all_keys:
                    self.key_binding_manager.set_key_sound(key_name, None)
                    
                # 刷新显示
                self.refresh_bindings()
                self.update_selected_key_info(self.selected_key or "")
                
                self.bindings_updated.emit()
                
                logger.info("已清除所有按键绑定")
                
            except Exception as e:
                logger.error(f"清除所有绑定失败: {e}")
                
    def apply_to_all_keys(self):
        """应用到所有按键"""
        current_index = self.sound_combo.currentIndex()
        if current_index <= 0:
            QMessageBox.information(self, "提示", "请先选择一个音效")
            return
            
        sound_path = self.sound_combo.currentData()
        sound_name = self.sound_combo.currentText()
        
        reply = QMessageBox.question(
            self,
            "确认应用",
            f"确定要将音效 '{sound_name}' 应用到所有按键吗？\n"
            "这将覆盖所有现有的按键绑定。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取所有按键
                all_keys = self.key_binding_manager.get_all_bindings().keys()
                
                # 应用到所有按键
                for key_name in all_keys:
                    self.key_binding_manager.set_key_sound(key_name, sound_path)
                    
                # 刷新显示
                self.refresh_bindings()
                self.update_selected_key_info(self.selected_key or "")
                
                self.bindings_updated.emit()
                
                logger.info(f"已将音效 {sound_name} 应用到所有按键")
                
            except Exception as e:
                logger.error(f"批量应用绑定失败: {e}")
                
    def apply_preset(self, preset_name: str):
        """应用预设方案"""
        if preset_name == "自定义":
            return
            
        # 这里可以实现预设方案的逻辑
        logger.info(f"应用预设方案: {preset_name}")
        
    def quick_set_key(self, key_name: str):
        """快速设置按键"""
        self.select_key(key_name)
        
    def refresh_bindings(self):
        """刷新绑定显示"""
        # 刷新所有按键按钮的样式
        for i in range(self.key_categories.count()):
            tab = self.key_categories.widget(i)
            buttons = tab.findChildren(QPushButton)
            for btn in buttons:
                key_name = btn.text().lower()
                self.update_key_button_style(btn, key_name)
                
    def log_message(self, message: str):
        """记录日志消息"""
        logger.info(message)


class KeyBindingDialog(QDialog):
    """按键绑定设置对话框"""
    
    def __init__(self, key_binding_manager, config_manager, parent=None, selected_key: Optional[str] = None):
        super().__init__(parent)
        self.key_binding_manager = key_binding_manager
        self.config_manager = config_manager
        self.selected_key = selected_key
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("按键绑定设置")
        self.setModal(True)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # 创建按键绑定组件
        self.key_binding_widget = KeyBindingWidget(
            self.key_binding_manager,
            self.config_manager,
            self
        )
        
        # 连接信号
        self.key_binding_widget.binding_changed.connect(self.on_binding_changed)
        self.key_binding_widget.bindings_updated.connect(self.on_bindings_updated)
        
        layout.addWidget(self.key_binding_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_bindings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 如果指定了选中按键，选择它
        if self.selected_key:
            self.key_binding_widget.select_key(self.selected_key)
            
    def on_binding_changed(self, key_name: str, sound_path: str):
        """绑定改变事件"""
        logger.info(f"绑定改变: {key_name} -> {sound_path}")
        
    def on_bindings_updated(self):
        """批量更新完成事件"""
        logger.info("按键绑定批量更新完成")
        
    def accept(self):
        """确认按钮点击事件"""
        try:
            # 获取当前绑定
            bindings = self.key_binding_manager.get_all_bindings()
            
            # 保存到配置
            self.config_manager.set_key_bindings(bindings)
            self.config_manager.save_config()
            
            logger.info("按键绑定已保存")
            super().accept()
            
        except Exception as e:
            logger.error(f"保存按键绑定失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
            
    def save_bindings(self):
        """保存绑定"""
        self.accept()
            
    def closeEvent(self, event):
        """关闭事件"""
        # 如果点击了保存按钮，不询问
        if self.result() == QDialog.DialogCode.Accepted:
            event.accept()
            return
            
        # 检查是否有未保存的更改
        try:
            current_bindings = self.key_binding_manager.get_all_bindings()
            saved_bindings = self.config_manager.get_key_bindings()
            
            if current_bindings != saved_bindings:
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "有未保存的更改，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                    
        except Exception as e:
            logger.error(f"检查绑定更改失败: {e}")
            
        event.accept()