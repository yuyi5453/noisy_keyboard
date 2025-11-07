# Noisy Keyboard

一个可以为键盘按键添加自定义音效的桌面应用。

## 功能特点
- 🎵 自定义按键音效
- 🎹 支持多种音效文件（MP3）
- ⌨️ 灵活的按键绑定设置
- 🗂️ 音效库管理（添加/删除）
- 🔔 系统托盘支持
- 🔊 音量控制

## 运行环境
- Python 3.8+
- 支持 Windows/macOS/Linux

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python main.py
```

## 使用说明
1. 启动应用后，点击「按键绑定」设置按键音效
2. 使用「音效库」管理音效文件
3. 通过系统托盘图标快速控制应用

## 项目结构
```
noisy_keyboard/
├── main.py              # 主程序入口
├── core/                # 核心模块
│   ├── config_manager.py
│   ├── key_binding.py
│   ├── keyboard_listener.py
│   └── sound_manager.py
├── ui/                  # 用户界面
│   ├── main_window.py
│   ├── key_binding_dialog.py
│   └── sound_library.py
├── resource/            # 资源文件
└── config/              # 配置文件
```

## 注意事项
- 首次运行会自动创建默认配置
- 音效文件支持MP3格式
- 自定义音效文件路径会被保存