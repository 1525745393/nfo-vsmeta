#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的彩色日志组件
支持过滤、搜索、导出和更多功能
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QTextEdit, QLineEdit, QComboBox, QCheckBox, QFileDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


if PYQT6_AVAILABLE:
    class EnhancedLogWidget(QWidget):
        """增强的日志组件"""
        
        # 自定义信号
        log_cleared = pyqtSignal()
        log_exported = pyqtSignal(str)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self._logs = []
            self._setup_ui()
        
        def _setup_ui(self):
            """设置UI"""
            layout = QVBoxLayout(self)
            
            # 工具栏
            toolbar = QHBoxLayout()
            
            # 日志级别过滤
            self.level_combo = QComboBox()
            self.level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"])
            self.level_combo.currentTextChanged.connect(self._filter_logs)
            toolbar.addWidget(QLabel("级别:"))
            toolbar.addWidget(self.level_combo)
            
            # 搜索框
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("搜索日志...")
            self.search_input.textChanged.connect(self._filter_logs)
            toolbar.addWidget(self.search_input)
            
            # 导出按钮
            self.export_btn = QPushButton("导出日志")
            self.export_btn.clicked.connect(self._export_logs)
            toolbar.addWidget(self.export_btn)
            
            # 清除按钮
            self.clear_btn = QPushButton("清空")
            self.clear_btn.clicked.connect(self.clear)
            toolbar.addWidget(self.clear_btn)
            
            layout.addLayout(toolbar)
            
            # 日志文本框
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            layout.addWidget(self.log_text)
        
        def _format_log(self, level: str, message: str) -> str:
            """格式化日志"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp}] [{level}] {message}"
        
        def _get_color_for_level(self, level: str) -> QColor:
            """获取日志级别的颜色"""
            colors = {
                "DEBUG": QColor(128, 128, 128),
                "INFO": QColor(0, 0, 0),
                "WARNING": QColor(255, 165, 0),
                "ERROR": QColor(255, 0, 0),
                "SUCCESS": QColor(0, 128, 0)
            }
            return colors.get(level, QColor(0, 0, 0))
        
        def add_log(self, level: LogLevel, message: str):
            """添加日志"""
            self._logs.append({"level": level.value, "message": message})
            self._update_display()
        
        def _filter_logs(self):
            """过滤日志"""
            self._update_display()
        
        def _update_display(self):
            """更新显示"""
            level_filter = self.level_combo.currentText()
            search_text = self.search_input.text().lower()
            
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            
            self.log_text.clear()
            
            for log in self._logs:
                level = log["level"]
                message = log["message"]
                
                # 应用过滤
                if level_filter != "全部" and level != level_filter:
                    continue
                if search_text and search_text not in message.lower():
                    continue
                
                # 格式化
                text = self._format_log(level, message) + "\n"
                
                # 设置颜色
                char_format = QTextCharFormat()
                char_format.setForeground(self._get_color_for_level(level))
                
                cursor.insertText(text, char_format)
        
        def clear(self):
            """清空日志"""
            self._logs.clear()
            self.log_text.clear()
            self.log_cleared.emit()
        
        def _export_logs(self):
            """导出日志"""
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出日志", "", "文本文件 (*.txt);;所有文件 (*)"
            )
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    for log in self._logs:
                        f.write(self._format_log(log["level"], log["message"]) + "\n")
                self.log_exported.emit(filename)
        
        def get_logs(self) -> List[dict]:
            """获取所有日志"""
            return self._logs.copy()
else:
    class EnhancedLogWidget:
        """PyQt6不可用时的空实现"""
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is not available")
