import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QFileDialog, QMessageBox, QGroupBox, QLineEdit,
                             QSplitter, QTextEdit, QProgressBar, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent

logger = logging.getLogger(__name__)


class SoundLibraryWidget(QWidget):
    """音效库管理组件"""
    
    # 信号定义
    sound_added = pyqtSignal(str, str)  # sound_name, sound_path
    sound_removed = pyqtSignal(str)  # sound_name
    sound_selected = pyqtSignal(str, str)  # sound_name, sound_path
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
        self.refresh_sound_library()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 顶部控制区
        control_layout = QHBoxLayout()
        
        self.add_sound_btn = QPushButton("添加音效文件")
        self.add_sound_btn.clicked.connect(self.add_sound_file)
        control_layout.addWidget(self.add_sound_btn)
        
        self.add_custom_path_btn = QPushButton("选择文件路径")
        self.add_custom_path_btn.clicked.connect(self.add_custom_sound_path)
        control_layout.addWidget(self.add_custom_path_btn)
        
        self.remove_sound_btn = QPushButton("移除选中音效")
        self.remove_sound_btn.clicked.connect(self.remove_selected_sound)
        control_layout.addWidget(self.remove_sound_btn)
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_sound_library)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索音效...")
        self.search_edit.textChanged.connect(self.filter_sounds)
        control_layout.addWidget(self.search_edit)
        
        layout.addLayout(control_layout)
        
        # 主内容区 - 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧音效列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.sound_list = QListWidget()
        self.sound_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.sound_list.itemSelectionChanged.connect(self.on_sound_selected)
        self.sound_list.itemDoubleClicked.connect(self.on_sound_double_clicked)
        self.sound_list.setAcceptDrops(True)
        self.sound_list.dragEnterEvent = self.drag_enter_event
        self.sound_list.dragMoveEvent = self.drag_move_event
        self.sound_list.dropEvent = self.drop_event
        
        left_layout.addWidget(QLabel("音效列表:"))
        left_layout.addWidget(self.sound_list)
        
        splitter.addWidget(left_widget)
        
        # 右侧详情区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 音效信息组
        info_group = QGroupBox("音效信息")
        info_layout = QVBoxLayout(info_group)
        
        self.sound_name_label = QLabel("名称: 未选择")
        info_layout.addWidget(self.sound_name_label)
        
        self.sound_path_label = QLabel("路径: 未选择")
        info_layout.addWidget(self.sound_path_label)
        
        self.sound_size_label = QLabel("文件大小: 未知")
        info_layout.addWidget(self.sound_size_label)
        
        self.sound_format_label = QLabel("格式: 未知")
        info_layout.addWidget(self.sound_format_label)
        
        info_layout.addStretch()
        right_layout.addWidget(info_group)
        
        # 预览控制组
        preview_group = QGroupBox("预览控制")
        preview_layout = QVBoxLayout(preview_group)
        
        self.play_btn = QPushButton("播放音效")
        self.play_btn.clicked.connect(self.play_selected_sound)
        preview_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("停止播放")
        self.stop_btn.clicked.connect(self.stop_playback)
        preview_layout.addWidget(self.stop_btn)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("预览音量:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.on_preview_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("80%")
        volume_layout.addWidget(self.volume_label)
        preview_layout.addLayout(volume_layout)
        
        # 播放进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        preview_layout.addWidget(self.progress_bar)
        
        preview_layout.addStretch()
        right_layout.addWidget(preview_group)
        
        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        right_layout.addWidget(log_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 400])
        
        layout.addWidget(splitter)
        
    def drag_enter_event(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def drag_move_event(self, event: QDragMoveEvent):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def drop_event(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self._is_valid_audio_file(file_path):
                files.append(file_path)
                
        if files:
            self._add_sound_files(files)
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def _is_valid_audio_file(self, file_path: str) -> bool:
        """检查是否为有效的音频文件"""
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext in valid_extensions
        
    def add_sound_file(self):
        """添加音效文件"""
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "选择音效文件",
                "",
                "音频文件 (*.mp3 *.wav *.ogg *.m4a *.flac);;所有文件 (*.*)"
            )
            
            if file_paths:
                self._add_sound_files(file_paths)
                
        except Exception as e:
            logger.error(f"添加音效文件失败: {e}")
            self.log_message(f"错误: 添加音效文件失败 - {e}")

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
                    self.log_message(f"已添加自定义音效: {os.path.basename(file_path)}")
                    
                    # 发送添加信号
                    sound_name = os.path.splitext(os.path.basename(file_path))[0]
                    self.sound_added.emit(sound_name, file_path)
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
            self.log_message(f"错误: 添加自定义音效路径失败 - {e}")
            
    def _add_sound_files(self, file_paths: List[str]):
        """批量添加音效文件"""
        try:
            added_count = 0
            for file_path in file_paths:
                try:
                    # 获取文件名（不含扩展名）
                    import os
                    sound_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 检查是否已存在
                    existing_sounds = self.config_manager.get_sound_library()
                    if sound_name in existing_sounds:
                        # 生成唯一名称
                        counter = 1
                        base_name = sound_name
                        while f"{base_name}_{counter}" in existing_sounds:
                            counter += 1
                        sound_name = f"{base_name}_{counter}"
                    
                    # 添加到音效库
                    self.config_manager.add_sound_to_library(sound_name, file_path)
                    added_count += 1
                    
                    self.log_message(f"已添加音效: {sound_name}")
                    
                except Exception as e:
                    logger.error(f"添加音效文件 {file_path} 失败: {e}")
                    self.log_message(f"错误: 添加 {os.path.basename(file_path)} 失败 - {e}")
            
            if added_count > 0:
                self.config_manager.save_config()
                self.refresh_sound_library()
                self.log_message(f"成功添加 {added_count} 个音效文件")
                
        except Exception as e:
            logger.error(f"批量添加音效文件失败: {e}")
            self.log_message(f"错误: 批量添加音效文件失败 - {e}")
            
    def remove_selected_sound(self):
        """移除选中的音效"""
        try:
            current_item = self.sound_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "信息", "请先选择要移除的音效")
                return
                
            sound_path = current_item.data(Qt.ItemDataRole.UserRole)
            sound_name = self._get_sound_name_from_path(sound_path)
            
            reply = QMessageBox.question(
                self,
                "确认移除",
                f"确定要移除音效 '{sound_name}' 吗？\n"
                "这将同时移除所有绑定到此音效的按键设置。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 从配置中移除
                self.config_manager.remove_sound_from_library(sound_name)
                self.config_manager.save_config()
                
                # 刷新显示
                self.refresh_sound_library()
                self.clear_sound_info()
                
                self.log_message(f"已移除音效: {sound_name}")
                self.sound_removed.emit(sound_name)
                
        except Exception as e:
            logger.error(f"移除音效失败: {e}")
            self.log_message(f"错误: 移除音效失败 - {e}")
            
    def refresh_sound_library(self):
        """刷新音效库"""
        try:
            self.sound_list.clear()
            sounds = self.config_manager.get_sound_library()
            
            for sound_name, sound_path in sounds.items():
                try:
                    # 获取文件信息
                    import os
                    file_size = os.path.getsize(sound_path) if os.path.exists(sound_path) else 0
                    file_size_str = self._format_file_size(file_size)
                    
                    # 获取文件格式
                    file_ext = os.path.splitext(sound_path)[1].upper()
                    
                    # 检查是否为自定义路径
                    is_custom = "📁" in sound_name
                    
                    # 创建列表项
                    display_text = f"{sound_name} [{file_ext}] ({file_size_str})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, sound_path)
                    
                    # 检查文件是否存在
                    if not os.path.exists(sound_path):
                        item.setForeground(Qt.GlobalColor.red)
                        item.setToolTip("文件不存在")
                    elif is_custom:
                        item.setForeground(Qt.GlobalColor.blue)
                        item.setToolTip("自定义路径音效")
                    
                    self.sound_list.addItem(item)
                    
                except Exception as e:
                    logger.error(f"加载音效 {sound_name} 失败: {e}")
                    
            self.log_message(f"已加载 {len(sounds)} 个音效")
            
        except Exception as e:
            logger.error(f"刷新音效库失败: {e}")
            self.log_message(f"错误: 刷新音效库失败 - {e}")
            
    def filter_sounds(self, text: str):
        """过滤音效列表"""
        try:
            search_text = text.lower()
            
            for i in range(self.sound_list.count()):
                item = self.sound_list.item(i)
                item_text = item.text().lower()
                
                if search_text in item_text:
                    item.setHidden(False)
                else:
                    item.setHidden(True)
                    
        except Exception as e:
            logger.error(f"过滤音效失败: {e}")
            
    def on_sound_selected(self):
        """音效选择事件"""
        try:
            current_item = self.sound_list.currentItem()
            if current_item:
                sound_path = current_item.data(Qt.ItemDataRole.UserRole)
                sound_name = self._get_sound_name_from_path(sound_path)
                
                # 更新详情信息
                self.update_sound_info(sound_name, sound_path)
                
                # 发送选择信号
                self.sound_selected.emit(sound_name, sound_path)
                
        except Exception as e:
            logger.error(f"选择音效失败: {e}")
            
    def on_sound_double_clicked(self, item):
        """音效双击事件"""
        self.play_selected_sound()
        
    def update_sound_info(self, sound_name: str, sound_path: str):
        """更新音效信息"""
        try:
            import os
            
            # 基本信息
            self.sound_name_label.setText(f"名称: {sound_name}")
            self.sound_path_label.setText(f"路径: {sound_path}")
            
            # 文件信息
            if os.path.exists(sound_path):
                file_size = os.path.getsize(sound_path)
                self.sound_size_label.setText(f"文件大小: {self._format_file_size(file_size)}")
                
                file_ext = os.path.splitext(sound_path)[1].upper()
                self.sound_format_label.setText(f"格式: {file_ext}")
            else:
                self.sound_size_label.setText("文件大小: 文件不存在")
                self.sound_format_label.setText("格式: 未知")
                
        except Exception as e:
            logger.error(f"更新音效信息失败: {e}")
            
    def clear_sound_info(self):
        """清空音效信息"""
        self.sound_name_label.setText("名称: 未选择")
        self.sound_path_label.setText("路径: 未选择")
        self.sound_size_label.setText("文件大小: 未知")
        self.sound_format_label.setText("格式: 未知")
        
    def play_selected_sound(self):
        """播放选中的音效"""
        try:
            current_item = self.sound_list.currentItem()
            if current_item:
                sound_path = current_item.data(Qt.ItemDataRole.UserRole)
                if sound_path and os.path.exists(sound_path):
                    # 获取预览音量
                    preview_volume = self.volume_slider.value() / 100.0
                    
                    # 这里需要集成SoundManager来播放音效
                    # 暂时使用日志记录
                    self.log_message(f"播放音效: {os.path.basename(sound_path)} (音量: {preview_volume})")
                    
                    # 显示进度条
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setRange(0, 0)  # 不确定模式
                    
                    # 模拟播放完成
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(2000, self._on_playback_finished)
                    
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
            self.log_message(f"错误: 播放音效失败 - {e}")
            
    def stop_playback(self):
        """停止播放"""
        self.log_message("停止播放")
        self._on_playback_finished()
        
    def _on_playback_finished(self):
        """播放完成回调"""
        self.progress_bar.setVisible(False)
        
    def on_preview_volume_changed(self, value: int):
        """预览音量改变"""
        self.volume_label.setText(f"{value}%")
        
    def _get_sound_name_from_path(self, sound_path: str) -> str:
        """从路径获取音效名称"""
        try:
            sounds = self.config_manager.get_sound_library()
            for name, path in sounds.items():
                if path == sound_path:
                    return name
            return "未知音效"
        except Exception:
            return "未知音效"
            
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
            
        return f"{size_bytes:.1f} TB"
        
    def log_message(self, message: str):
        """记录日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 限制日志长度
        max_lines = 100
        if self.log_text.document().lineCount() > max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, 
                               self.log_text.document().lineCount() - max_lines)
            cursor.movePosition(cursor.MoveOperation.Start, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()


class SoundLibraryDialog(QDialog):
    """音效库管理对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("音效库管理")
        self.setModal(False)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 创建音效库组件
        self.sound_library_widget = SoundLibraryWidget(self.config_manager, self)
        layout.addWidget(self.sound_library_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 保存配置
        self.config_manager.save_config()
        event.accept()