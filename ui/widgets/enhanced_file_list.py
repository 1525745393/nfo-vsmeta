#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的文件列表组件
支持自定义信号、拖放视觉反馈和更好的用户体验
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
        QFileDialog, QMenu
    )
    from PyQt6.QtCore import (
        Qt, pyqtSignal, QPoint
    )
    from PyQt6.QtGui import (
        QDragEnterEvent, QDropEvent, QDragLeaveEvent,
        QColor, QAction
    )
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None


@dataclass
class FileItem:
    """文件项数据类"""
    path: str
    status: str = "待处理"
    progress: int = 0
    error: Optional[str] = None


if PYQT6_AVAILABLE:
    class EnhancedFileListWidget(QWidget):
        """增强的文件列表组件"""
        
        # 自定义信号
        file_added = pyqtSignal(str)          # 文件添加
        file_removed = pyqtSignal(str)        # 文件移除
        files_cleared = pyqtSignal()          # 清空列表
        selection_changed = pyqtSignal(list)  # 选择变化
        files_dropped = pyqtSignal(list)      # 文件拖放
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setup_ui()
        
        def setup_ui(self):
            """设置UI"""
            self.setAcceptDrops(True)
            
            # 主布局
            layout = QVBoxLayout(self)
            
            # 工具栏
            toolbar = QHBoxLayout()
            
            # 添加文件按钮
            self.add_btn = QPushButton("添加文件")
            self.add_btn.clicked.connect(self.add_files)
            toolbar.addWidget(self.add_btn)
            
            # 添加文件夹按钮
            self.add_folder_btn = QPushButton("添加文件夹")
            self.add_folder_btn.clicked.connect(self.add_folder)
            toolbar.addWidget(self.add_folder_btn)
            
            # 清除按钮
            self.clear_btn = QPushButton("清空列表")
            self.clear_btn.clicked.connect(self.clear_list)
            toolbar.addWidget(self.clear_btn)
            
            layout.addLayout(toolbar)
            
            # 文件表格
            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["文件名", "状态", "进度", "错误"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.MultiSelection)
            self.table.itemSelectionChanged.connect(self.on_selection_changed)
            
            layout.addWidget(self.table)
            
            # 文件列表
            self.files: List[FileItem] = []
        
        def add_files(self):
            """添加文件"""
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择视频文件", "", "视频文件 (*.mp4 *.mkv *.avi *.ts *.mov);;所有文件 (*)"
            )
            for file in files:
                self.add_file(file)
        
        def add_folder(self):
            """添加文件夹"""
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder:
                self.scan_folder(folder)
        
        def scan_folder(self, folder_path: str):
            """扫描文件夹中的视频文件"""
            video_extensions = {'.mp4', '.mkv', '.avi', '.ts', '.mov'}
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in video_extensions:
                        self.add_file(os.path.join(root, file))
        
        def add_file(self, file_path: str):
            """添加文件到列表"""
            if any(f.path == file_path for f in self.files):
                return
            
            file_item = FileItem(path=file_path)
            self.files.append(file_item)
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
            self.table.setItem(row, 1, QTableWidgetItem("待处理"))
            self.table.setItem(row, 2, QTableWidgetItem("0%"))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            
            self.file_added.emit(file_path)
        
        def remove_selected(self):
            """移除选中的文件"""
            selected_rows = set(item.row() for item in self.table.selectedItems())
            for row in sorted(selected_rows, reverse=True):
                file_path = self.files[row].path
                self.table.removeRow(row)
                self.files.pop(row)
                self.file_removed.emit(file_path)
        
        def clear_list(self):
            """清空列表"""
            self.table.setRowCount(0)
            self.files.clear()
            self.files_cleared.emit()
        
        def on_selection_changed(self):
            """选择变化"""
            selected = [self.files[item.row()].path for item in self.table.selectedItems()]
            self.selection_changed.emit(selected)
        
        def update_file_status(self, file_path: str, status: str, progress: int = 0, error: str = None):
            """更新文件状态"""
            for i, file in enumerate(self.files):
                if file.path == file_path:
                    file.status = status
                    file.progress = progress
                    file.error = error
                    
                    self.table.item(i, 1).setText(status)
                    self.table.item(i, 2).setText(f"{progress}%")
                    self.table.item(i, 3).setText(error or "")
                    break
        
        def dragEnterEvent(self, event: QDragEnterEvent):
            """拖放进入"""
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
        
        def dropEvent(self, event: QDropEvent):
            """拖放放下"""
            files = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    files.append(path)
                elif os.path.isdir(path):
                    self.scan_folder(path)
            
            if files:
                self.files_dropped.emit(files)
            
            event.acceptProposedAction()
else:
    class EnhancedFileListWidget:
        """PyQt6不可用时的空实现"""
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is not available")
