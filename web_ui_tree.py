#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI 树形结构版
===============================================
✨ 新增功能：
1. 暗色/浅色主题切换
2. 拖拽上传功能
3. 实时搜索和筛选
4. 文件夹树形结构（展开/折叠）
"""

import os
import sys
import subprocess
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template_string, jsonify, request, send_file
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

app = None
if HAS_FLASK:
    app = Flask(__name__)

_state = {
    "is_running": False,
    "progress": {"total": 0, "completed": 0, "success": 0, "failed": 0, "current_file": ""},
    "scan_results": [],
    "logs": []
}


def _add_log(level, message):
    _state["logs"].append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    })
    if len(_state["logs"]) > 1000:
        _state["logs"] = _state["logs"][-1000:]


INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFO转VSMETA转换器 - 树形结构版</title>
    <style>
        :root {
            --primary: #667eea;
            --primary-dark: #764ba2;
            --success: #38ef7d;
            --warning: #f093fb;
            --danger: #f45c43;
            --bg-main: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bg-card: rgba(255, 255, 255, 0.95);
            --text-primary: #333;
            --text-secondary: #666;
            --border-color: #ddd;
        }
        
        [data-theme="dark"] {
            --primary: #667eea;
            --primary-dark: #764ba2;
            --success: #38ef7d;
            --warning: #f093fb;
            --danger: #f45c43;
            --bg-main: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            --bg-card: rgba(30, 30, 50, 0.95);
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border-color: #444;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: var(--bg-main); 
            min-height: 100vh; 
            color: var(--text-primary); 
            transition: all 0.3s ease;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header { 
            background: var(--bg-card); 
            padding: 30px; 
            border-radius: 15px; 
            margin-bottom: 20px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { 
            font-size: 2.5em; 
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            margin-bottom: 10px; 
        }
        .header p { color: var(--text-secondary); font-size: 1.1em; }
        
        .theme-toggle {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .theme-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            background: var(--bg-card); 
            padding: 15px; 
            border-radius: 15px; 
            box-shadow: 0 5px 20px rgba(0,0,0,0.1); 
        }
        .nav button { 
            flex: 1; 
            padding: 15px 20px; 
            border: none; 
            background: rgba(102, 126, 234, 0.1); 
            cursor: pointer; 
            border-radius: 10px; 
            font-size: 16px; 
            font-weight: 600; 
            transition: all 0.3s;
            color: var(--text-primary);
        }
        .nav button:hover { 
            background: rgba(102, 126, 234, 0.2); 
            transform: translateY(-2px); 
        }
        .nav button.active { 
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); 
            color: white; 
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); 
        }
        
        .page { display: none; }
        .page.active { display: block; }
        
        .card { 
            background: var(--bg-card); 
            padding: 25px; 
            border-radius: 15px; 
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            color: var(--text-primary);
        }
        .card h2 { 
            color: var(--primary); 
            margin-bottom: 20px;
            font-size: 1.8em; 
            border-bottom: 3px solid var(--primary); 
            padding-bottom: 10px; 
        }
        .card h3 { 
            color: var(--primary); 
            margin: 15px 0 10px 0; 
            font-size: 1.2em; 
        }
        
        .drop-zone {
            border: 3px dashed var(--primary);
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background: rgba(102, 126, 234, 0.05);
            transition: all 0.3s;
            cursor: pointer;
        }
        .drop-zone:hover, .drop-zone.drag-over {
            background: rgba(102, 126, 234, 0.15);
            border-color: var(--primary-dark);
            transform: scale(1.02);
        }
        .drop-zone-icon { font-size: 3em; margin-bottom: 15px; }
        .drop-zone-text { font-size: 1.2em; color: var(--text-secondary); }
        
        .search-container {
            position: relative;
            margin: 15px 0;
        }
        .search-input {
            width: 100%;
            padding: 15px 50px 15px 20px;
            border: 2px solid var(--primary);
            border-radius: 25px;
            font-size: 16px;
            background: rgba(102, 126, 234, 0.05);
            color: var(--text-primary);
            transition: all 0.3s;
        }
        .search-input:focus {
            outline: none;
            border-color: var(--primary-dark);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .search-icon {
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.3em;
        }
        
        /* 树形结构样式 */
        .tree-view {
            margin: 15px 0;
            font-family: 'Courier New', monospace;
        }
        .tree-node {
            padding: 8px 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tree-node:hover {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 5px;
        }
        .tree-toggle {
            display: inline-block;
            width: 20px;
            margin-right: 5px;
            cursor: pointer;
            user-select: none;
            font-weight: bold;
            color: var(--primary);
        }
        .tree-toggle:hover {
            color: var(--primary-dark);
        }
        .tree-icon {
            margin-right: 8px;
        }
        .tree-folder {
            color: #f0ad4e;
            font-weight: 600;
        }
        .tree-file {
            color: var(--text-primary);
        }
        .tree-children {
            margin-left: 30px;
            border-left: 1px dashed var(--border-color);
            padding-left: 15px;
        }
        .tree-children.collapsed {
            display: none;
        }
        .tree-node.selected {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-radius: 5px;
            padding: 8px 15px;
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin: 20px 0; 
        }
        .stat-card { 
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); 
            color: white; 
            padding: 25px; 
            border-radius: 15px; 
            text-align: center; 
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3); 
            transition: transform 0.3s; 
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card.success { background: linear-gradient(135deg, #11998e 0%, var(--success) 100%); }
        .stat-card.warning { background: linear-gradient(135deg, var(--warning) 0%, var(--danger) 100%); }
        .stat-card.danger { background: linear-gradient(135deg, var(--danger) 0%, #f45c43 100%); }
        .stat-value { font-size: 3em; font-weight: 700; }
        .stat-label { font-size: 1.1em; opacity: 0.9; }
        
        .progress-container { 
            background: rgba(102, 126, 234, 0.1); 
            border-radius: 15px; 
            padding: 20px; 
            margin: 20px 0; 
        }
        .progress-bar { 
            height: 40px; 
            background: rgba(102, 126, 234, 0.2); 
            border-radius: 20px; 
            overflow: hidden; 
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, var(--primary), var(--primary-dark)); 
            width: 0%; 
            transition: width 0.5s; 
            border-radius: 20px; 
            position: relative; 
        }
        .progress-text { 
            position: absolute; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%); 
            font-weight: 700; 
            color: white; 
            font-size: 1.1em; 
        }
        
        .btn { 
            padding: 12px 24px; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 14px; 
            margin: 5px; 
            font-weight: 600; 
            transition: all 0.3s; 
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn-primary { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color: white; }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, var(--success) 100%); color: white; }
        .btn-danger { background: linear-gradient(135deg, var(--danger) 0%, #f45c43 100%); color: white; }
        .btn-secondary { background: rgba(102, 126, 234, 0.1); color: var(--primary); }
        
        input, select { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid var(--primary); 
            border-radius: 10px; 
            margin: 10px 0; 
            font-size: 14px; 
            background: rgba(102, 126, 234, 0.05); 
            color: var(--text-primary);
        }
        input:focus, select:focus { 
            outline: none; 
            border-color: var(--primary-dark); 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); 
        }
        
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin: 10px 0; }
        .checkbox-group input[type="checkbox"] { width: auto; transform: scale(1.3); }
        
        .tabs { display: flex; gap: 10px; margin: 15px 0; flex-wrap: wrap; }
        .tab { 
            padding: 12px 24px; 
            background: rgba(102, 126, 234, 0.1); 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 600; 
            transition: all 0.3s;
            color: var(--text-primary);
        }
        .tab:hover { background: rgba(102, 126, 234, 0.2); }
        .tab.active { 
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); 
            color: white; 
        }
        
        .tab-content { 
            display: none; 
            padding: 20px; 
            background: rgba(102, 126, 234, 0.05); 
            border-radius: 10px; 
            margin: 10px 0; 
        }
        .tab-content.active { display: block; }
        
        .code-block { 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            max-height: 400px; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            word-break: break-all; 
        }
        
        .compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .compare-grid { grid-template-columns: 1fr; } }
        
        .image-container { text-align: center; padding: 20px; }
        .image-container img { 
            max-width: 100%; 
            max-height: 400px; 
            border-radius: 10px; 
            box-shadow: 0 5px 20px rgba(0,0,0,0.2); 
            transition: transform 0.3s; 
        }
        .image-container img:hover { transform: scale(1.02); }
        
        .log-box { 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            max-height: 500px; 
            overflow-y: auto; 
        }
        .log-entry { 
            margin: 8px 0; 
            padding: 10px; 
            background: rgba(255,255,255,0.05); 
            border-radius: 5px; 
        }
        .log-time { color: var(--primary); margin-right: 10px; }
        .log-level { 
            padding: 2px 10px; 
            border-radius: 3px; 
            margin-right: 10px; 
            font-weight: 700; 
        }
        .log-level.info { background: var(--primary); color: white; }
        .log-level.success { background: var(--success); color: black; }
        .log-level.error { background: var(--danger); color: white; }
        .log-level.warning { background: var(--warning); color: black; }
        
        .badge { 
            padding: 5px 12px; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: 700; 
        }
        .badge-success { background: var(--success); color: black; }
        .badge-warning { background: var(--warning); color: black; }
        .badge-danger { background: var(--danger); color: white; }
        
        .detail-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 15px 0; 
        }
        .detail-item { 
            background: rgba(102, 126, 234, 0.05); 
            padding: 15px; 
            border-radius: 10px; 
        }
        .detail-label { 
            font-size: 0.9em; 
            color: var(--primary); 
            margin-bottom: 5px; 
            font-weight: 600; 
        }
        .detail-value { font-size: 1.1em; font-weight: 700; }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: rgba(102, 126, 234, 0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--primary-dark); }
        
        .fade-in {
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🎬 NFO转VSMETA转换器</h1>
                <p>专业级媒体文件转换工具 - 树形结构版</p>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()" id="theme-toggle">
                🌙 暗色主题
            </button>
        </div>
        
        <div class="nav">
            <button class="active" id="btn-dashboard" onclick="showPage('dashboard')">📊 仪表盘</button>
            <button id="btn-files" onclick="showPage('files')">📁 文件管理</button>
            <button id="btn-convert" onclick="showPage('convert')">🚀 批量转换</button>
            <button id="btn-logs" onclick="showPage('logs')">📋 运行日志</button>
        </div>
        
        <div id="page-dashboard" class="page active">
            <div class="card fade-in">
                <h2>📈 转换统计</h2>
                <div class="stats-grid">
                    <div class="stat-card success">
                        <div class="stat-value" id="stat-success">0</div>
                        <div class="stat-label">✅ 已转换</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-value" id="stat-pending">0</div>
                        <div class="stat-label">⏳ 待转换</div>
                    </div>
                    <div class="stat-card danger">
                        <div class="stat-value" id="stat-failed">0</div>
                        <div class="stat-label">❌ 失败</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-total">0</div>
                        <div class="stat-label">📁 总数</div>
                    </div>
                </div>
                
                <div class="progress-container">
                    <h3 style="margin-bottom: 15px;">📊 转换进度</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill">
                            <div class="progress-text" id="progress-text">0%</div>
                        </div>
                    </div>
                    <div id="progress-detail" style="text-align: center; margin-top: 10px; color: var(--primary);">0 / 0 文件</div>
                </div>
            </div>
            
            <div class="card fade-in">
                <h2>⚡ 快捷操作</h2>
                <button class="btn btn-primary" onclick="showPage('files'); refreshFiles();">📁 扫描文件</button>
                <button class="btn btn-success" onclick="showPage('convert');">🚀 开始转换</button>
                <button class="btn btn-secondary" onclick="showPage('logs'); refreshLogs();">📋 查看日志</button>
            </div>
        </div>
        
        <div id="page-files" class="page">
            <div class="card fade-in">
                <h2>📂 目录扫描</h2>
                
                <div class="drop-zone" id="drop-zone" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                    <div class="drop-zone-icon">📁</div>
                    <div class="drop-zone-text">拖拽文件夹到此处扫描</div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: var(--text-secondary);">或者点击下方按钮选择目录</div>
                </div>
                
                <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                    <button class="btn btn-secondary" style="padding: 8px 12px;" onclick="goToParentDir();" title="返回上一级">
                        ⬆️ 上一级
                    </button>
                    <input type="text" id="scan-dir" value="/workspace/test_movies" placeholder="输入目录路径" style="flex: 1;">
                </div>
                
                <div style="background: var(--bg-card); padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px dashed var(--primary);">
                    <div style="font-size: 0.85em; color: var(--text-secondary); margin-bottom: 5px;">📍 快捷访问</div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="btn btn-secondary" style="font-size: 12px; padding: 5px 10px;" onclick="document.getElementById('scan-dir').value='/workspace/test_movies'; refreshFiles();">
                            📁 测试文件夹
                        </button>
                        <button class="btn btn-secondary" style="font-size: 12px; padding: 5px 10px;" onclick="document.getElementById('scan-dir').value='/workspace'; refreshFiles();">
                            💼 工作区
                        </button>
                        <button class="btn btn-secondary" style="font-size: 12px; padding: 5px 10px;" onclick="document.getElementById('scan-dir').value='/'; refreshFiles();">
                            🏠 根目录
                        </button>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-primary" onclick="refreshFiles();">🔄 扫描</button>
                        <button class="btn btn-secondary" onclick="expandAll();">⬇️ 展开全部</button>
                        <button class="btn btn-secondary" onclick="collapseAll();">⬆️ 折叠全部</button>
                    </div>
                    <select id="filter-status" onchange="renderTree();" style="flex: 1; min-width: 150px;">
                        <option value="all">全部文件</option>
                        <option value="converted">✅ 已转换</option>
                        <option value="pending">⏳ 待转换</option>
                        <option value="no-nfo">❌ 无NFO</option>
                    </select>
                </div>
            </div>
            
            <div class="card fade-in">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <h2 style="margin: 0;">🌳 文件夹树形结构 (<span id="file-count">0</span>个文件)</h2>
                    </div>
                    <button class="btn btn-success" onclick="startConversion()" style="padding: 8px 20px; font-size: 14px;">
                        ▶ 开始转换
                    </button>
                </div>
                
                <div class="search-container">
                    <input 
                        type="text" 
                        id="search-input" 
                        class="search-input" 
                        placeholder="🔍 输入文件名或路径搜索..."
                        oninput="handleSearch()"
                    >
                    <span class="search-icon">🔍</span>
                </div>
                
                <div class="tree-view" id="file-tree">
                    <div style="text-align: center; padding: 40px; color: var(--primary);">👈 点击「扫描文件」按钮加载文件夹结构</div>
                </div>
            </div>
            
            <div class="card fade-in">
                <h2>📄 文件详情</h2>
                <div id="file-detail">
                    <div style="text-align: center; padding: 40px; color: var(--primary);">👈 从树形结构中选择一个文件查看详情</div>
                </div>
            </div>
        </div>
        
        <div id="page-convert" class="page">
            <div class="card fade-in">
                <h2>⚙️ 转换设置</h2>
                <input type="text" id="convert-dir" value="/workspace/test_movies" placeholder="目录路径">
                
                <div class="detail-grid" style="margin-top: 15px;">
                    <div class="detail-item">
                        <div class="detail-label">⚡ 工作线程数</div>
                        <input type="number" id="workers" value="4" min="1" max="16" style="width: 100%;">
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🔄 重试次数</div>
                        <input type="number" id="retry-attempts" value="3" min="0" max="10" style="width: 100%;">
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">⏱️ 重试延迟(秒)</div>
                        <input type="number" id="retry-delay" value="1" min="0" max="10" style="width: 100%;">
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🖼️ 图片压缩(KB)</div>
                        <input type="number" id="max-image-size" value="500" min="100" max="5000" step="100" style="width: 100%;">
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <div class="checkbox-group">
                        <input type="checkbox" id="overwrite">
                        <label for="overwrite">覆盖已有VSMETA文件</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="recursive" checked>
                        <label for="recursive">递归扫描子目录</label>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: var(--bg-card); border-radius: 8px; border-left: 4px solid var(--primary);">
                    <div style="font-size: 0.9em; color: var(--text-secondary); line-height: 1.6;">
                        <strong>💡 使用说明：</strong><br>
                        • <strong>工作线程数</strong>：并发处理的文件数，建议CPU核心数<br>
                        • <strong>重试次数</strong>：失败文件自动重试次数，默认3次<br>
                        • <strong>重试延迟</strong>：重试间隔时间（秒），默认1秒<br>
                        • <strong>图片压缩</strong>：海报图片最大大小，超过则自动压缩<br>
                        • <strong>覆盖文件</strong>：重新转换已存在的VSMETA文件<br>
                        • <strong>递归扫描</strong>：扫描所有子目录中的视频文件
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <button id="btn-start" class="btn btn-success" onclick="startConversionFromConvertPage();">▶️ 开始转换</button>
                    <button id="btn-stop" class="btn btn-danger" onclick="stopConversion();" style="display: none;">⏹️ 停止转换</button>
                </div>
            </div>
        </div>
        
        <div id="page-logs" class="page">
            <div class="card fade-in">
                <h2>📋 运行日志</h2>
                <button class="btn btn-secondary" onclick="refreshLogs();">🔄 刷新</button>
                <button class="btn btn-secondary" onclick="clearLogs();">🗑️ 清空</button>
                <button class="btn btn-secondary" onclick="downloadLogs();">📥 导出</button>
                <div class="log-box" id="log-box">
                    <div style="text-align: center; padding: 40px; color: var(--primary);">暂无日志</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let fileTree = [];
        let flatFiles = [];
        let selectedFile = null;
        let searchTimeout = null;
        
        // 主题切换
        function toggleTheme() {
            const body = document.body;
            const themeToggle = document.getElementById('theme-toggle');
            
            if (body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                themeToggle.textContent = '🌙 暗色主题';
                localStorage.setItem('theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                themeToggle.textContent = '☀️ 浅色主题';
                localStorage.setItem('theme', 'dark');
            }
        }
        
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            const themeToggle = document.getElementById('theme-toggle');
            
            if (savedTheme === 'dark') {
                document.body.setAttribute('data-theme', 'dark');
                themeToggle.textContent = '☀️ 浅色主题';
            }
        }
        
        // 拖拽处理
        function handleDragOver(e) {
            e.preventDefault();
            e.stopPropagation();
            document.getElementById('drop-zone').classList.add('drag-over');
        }
        
        function handleDragLeave(e) {
            e.preventDefault();
            e.stopPropagation();
            document.getElementById('drop-zone').classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            e.stopPropagation();
            document.getElementById('drop-zone').classList.remove('drag-over');
            
            if (e.dataTransfer.items) {
                const items = e.dataTransfer.items;
                for (let i = 0; i < items.length; i++) {
                    if (items[i].kind === 'file') {
                        const file = items[i].getAsFile();
                        if (file && file.path && file.path !== '/') {
                            document.getElementById('scan-dir').value = file.path;
                            refreshFiles();
                            return;
                        }
                    }
                }
            }
            
            alert('请拖拽文件夹到此处');
        }
        
        // 实时搜索
        function handleSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                renderTree();
            }, 300);
        }
        
        function showPage(name) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            document.getElementById('page-' + name).classList.add('active');
            document.getElementById('btn-' + name).classList.add('active');
        }
        
        async function api(url, method, data) {
            try {
                const opts = { method: method || 'GET' };
                if (data) {
                    opts.headers = {'Content-Type': 'application/json'};
                    opts.body = JSON.stringify(data);
                }
                const resp = await fetch(url, opts);
                return await resp.json();
            } catch (e) {
                console.error('API Error:', e);
                return {};
            }
        }
        
        async function refreshFiles() {
            const dir = document.getElementById('scan-dir').value;
            const tree = document.getElementById('file-tree');
            
            tree.innerHTML = 
                '<div style="text-align: center; padding: 60px; color: var(--primary);">' +
                    '<div style="font-size: 3em; margin-bottom: 20px;">🔄</div>' +
                    '<div style="font-size: 1.2em; margin-bottom: 10px;">正在扫描...</div>' +
                    '<div style="font-size: 0.9em; color: var(--text-secondary);">' + dir + '</div>' +
                '</div>';
            
            try {
                const data = await api('/api/scan-tree?dir=' + encodeURIComponent(dir));
                fileTree = data.tree || [];
                flatFiles = data.flatFiles || [];
                renderTree();
                await refreshStats();
            } catch (e) {
                console.error(e);
                tree.innerHTML = 
                    '<div style="text-align: center; padding: 60px; color: var(--danger);">' +
                        '<div style="font-size: 3em; margin-bottom: 20px;">❌</div>' +
                        '<div style="font-size: 1.2em; margin-bottom: 10px;">扫描失败</div>' +
                        '<div style="font-size: 0.9em; color: var(--text-secondary);">' + dir + '</div>' +
                    '</div>';
            }
        }
        
        function renderTree() {
            const tree = document.getElementById('file-tree');
            const count = document.getElementById('file-count');
            const filter = document.getElementById('filter-status').value;
            const searchQuery = document.getElementById('search-input').value.toLowerCase().trim();
            
            // 过滤文件
            let filteredTree = filterTree(fileTree, filter, searchQuery);
            
            if (!filteredTree.length) {
                tree.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--primary);">未找到符合条件的文件</div>';
                count.textContent = '0';
                return;
            }
            
            const totalFiles = countFiles(filteredTree);
            count.textContent = totalFiles;
            
            tree.innerHTML = renderTreeNodes(filteredTree, 0);
        }
        
        function filterTree(tree, filter, searchQuery) {
            return tree.map(node => {
                if (node.type === 'file') {
                    // 文件节点过滤
                    const matchFilter = filter === 'all' || 
                        (filter === 'converted' && node.statusClass === 'success') ||
                        (filter === 'pending' && node.statusClass === 'warning') ||
                        (filter === 'no-nfo' && node.statusClass === 'danger');
                    
                    const matchSearch = !searchQuery || 
                        node.name.toLowerCase().includes(searchQuery) ||
                        node.path.toLowerCase().includes(searchQuery);
                    
                    return matchFilter && matchSearch ? node : null;
                } else {
                    // 文件夹节点递归过滤
                    const filteredChildren = filterTree(node.children || [], filter, searchQuery);
                    if (filteredChildren.length > 0 || !searchQuery) {
                        return {
                            ...node,
                            children: filteredChildren.length > 0 ? filteredChildren : node.children,
                            expanded: searchQuery ? true : node.expanded
                        };
                    }
                    return null;
                }
            }).filter(node => node !== null);
        }
        
        function countFiles(tree) {
            let count = 0;
            tree.forEach(node => {
                if (node.type === 'file') {
                    count++;
                } else {
                    count += countFiles(node.children || []);
                }
            });
            return count;
        }
        
        function renderTreeNodes(nodes, level) {
            let html = '';
            nodes.forEach((node, index) => {
                if (node.type === 'folder') {
                    html += '<div class="tree-node">';
                    html += '<span class="tree-toggle" onclick="toggleNode(this, ' + level + ')">' + 
                            (node.expanded ? '▼' : '▶') + '</span>';
                    html += '<span class="tree-icon tree-folder">' + (node.expanded ? '📂' : '📁') + '</span>';
                    html += '<span data-path="' + encodeURIComponent(node.path) + '" onclick="selectFolder(this);" style="cursor: pointer; user-select: none;">' + node.name + '</span>';
                    html += '<span style="font-size: 0.8em; color: var(--text-secondary); margin-left: 8px;">(双击扫描)</span>';
                    
                    if (node.children && node.children.length > 0) {
                        html += '<div class="tree-children' + (node.expanded ? '' : ' collapsed') + '">';
                        html += renderTreeNodes(node.children, level + 1);
                        html += '</div>';
                    }
                    html += '</div>';
                } else {
                    const isSelected = selectedFile && selectedFile.path === node.path;
                    html += '<div class="tree-node' + (isSelected ? ' selected' : '') + '">';
                    html += '<span class="tree-toggle" style="visibility: hidden;">•</span>';
                    html += '<span class="tree-icon tree-file">🎬</span>';
                    html += '<span data-path="' + encodeURIComponent(node.path) + '" onclick="selectFileByPath(decodeURIComponent(this.dataset.path))">' + node.name + '</span>';
                    html += '<span class="badge badge-' + node.statusClass + '" style="margin-left: 10px;">' + node.statusText + '</span>';
                    html += '</div>';
                }
            });
            return html;
        }
        
        function toggleNode(element, level) {
            const childrenDiv = element.parentElement.querySelector('.tree-children');
            if (childrenDiv) {
                const isCollapsed = childrenDiv.classList.contains('collapsed');
                childrenDiv.classList.toggle('collapsed');
                const toggle = element.parentElement.querySelector('.tree-toggle');
                if (toggle) {
                    toggle.textContent = isCollapsed ? '▼' : '▶';
                }
            }
        }
        
        function goToParentDir() {
            const currentPath = document.getElementById('scan-dir').value;
            if (currentPath && currentPath !== '/') {
                const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
                document.getElementById('scan-dir').value = parentPath;
                refreshFiles();
            }
        }

        let folderClickTimer = null;
        function selectFolder(element) {
            const path = decodeURIComponent(element.dataset.path);
            document.getElementById('scan-dir').value = path;
            
            if (folderClickTimer) {
                clearTimeout(folderClickTimer);
                folderClickTimer = null;
                refreshFiles();
            } else {
                folderClickTimer = setTimeout(() => {
                    folderClickTimer = null;
                }, 300);
            }
        }
        
        function selectFileByPath(path) {
            const file = flatFiles.find(f => f.path === path);
            if (file) {
                selectedFile = file;
                renderTree();
                loadFileDetail(path);
            }
        }
        
        async function loadFileDetail(path) {
            const data = await api('/api/file-detail?path=' + encodeURIComponent(path));
            showFileDetail(data);
        }
        
        function expandAll() {
            document.querySelectorAll('.tree-children').forEach(el => {
                el.classList.remove('collapsed');
            });
            document.querySelectorAll('.tree-toggle').forEach(el => {
                if (el.textContent === '▶') {
                    el.textContent = '▼';
                }
            });
        }
        
        function collapseAll() {
            document.querySelectorAll('.tree-children').forEach(el => {
                el.classList.add('collapsed');
            });
            document.querySelectorAll('.tree-toggle').forEach(el => {
                if (el.textContent === '▼') {
                    el.textContent = '▶';
                }
            });
        }
        
        function showFileDetail(data) {
            const detail = document.getElementById('file-detail');
            
            let html = '<div class="detail-grid">';
            html += '<div class="detail-item"><div class="detail-label">文件名</div><div class="detail-value">' + (data.name || '-') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">目录</div><div class="detail-value" style="font-size: 0.9em;">' + (data.dir || '-') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">📄 NFO文件</div><div class="detail-value">' + (data.hasNfo ? '✅ 存在' : '❌ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">📝 VSMETA文件</div><div class="detail-value">' + (data.hasVsmeta ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">🖼️ 封面图片</div><div class="detail-value">' + (data.hasPoster ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">🎬 背景图片</div><div class="detail-value">' + (data.hasFanart ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '</div>';
            
            html += '<div class="tabs">';
            html += '<button class="tab active" id="tab-btn-nfo" onclick="showTab(' + "'nfo'" + ')">📄 NFO内容</button>';
            html += '<button class="tab" id="tab-btn-vsmeta" onclick="showTab(' + "'vsmeta'" + ')">📝 VSMETA内容</button>';
            html += '<button class="tab" id="tab-btn-compare" onclick="showTab(' + "'compare'" + ')">🔄 对比视图</button>';
            html += '</div>';
            
            html += '<div id="tab-nfo" class="tab-content active"><div class="code-block" id="nfo-content"></div></div>';
            html += '<div id="tab-vsmeta" class="tab-content"><div class="code-block" id="vsmeta-content"></div></div>';
            html += '<div id="tab-compare" class="tab-content">';
            html += '<div class="compare-grid">';
            html += '<div><h4 style="color: var(--primary); margin-bottom: 10px;">📄 NFO内容</h4><div class="code-block" id="compare-nfo"></div></div>';
            html += '<div><h4 style="color: var(--primary); margin-bottom: 10px;">📝 VSMETA内容</h4><div class="code-block" id="compare-vsmeta"></div></div>';
            html += '</div></div>';
            
            detail.innerHTML = html;
            
            document.getElementById('nfo-content').textContent = data.nfoContent || '无NFO内容';
            document.getElementById('vsmeta-content').textContent = data.vsmetaContent || '无VSMETA内容';
            document.getElementById('compare-nfo').textContent = data.nfoContent || '无NFO内容';
            document.getElementById('compare-vsmeta').textContent = data.vsmetaContent || '无VSMETA内容';
            
            const tabs = document.createElement('div');
            tabs.className = 'tabs';
            tabs.style.marginTop = '20px';
            if (data.hasPoster) {
                const btn = document.createElement('button');
                btn.className = 'tab';
                btn.textContent = '🖼️ 封面';
                btn.onclick = function() { showImageSafe(data.posterUrl, 'poster'); };
                tabs.appendChild(btn);
            }
            if (data.hasFanart) {
                const btn = document.createElement('button');
                btn.className = 'tab';
                btn.textContent = '🎬 背景图';
                btn.onclick = function() { showImageSafe(data.fanartUrl, 'fanart'); };
                tabs.appendChild(btn);
            }
            if (data.hasPoster || data.hasFanart) {
                detail.appendChild(tabs);
            }
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            const btn = document.getElementById('tab-btn-' + tabName);
            if (btn) btn.classList.add('active');
            
            const content = document.getElementById('tab-' + tabName);
            if (content) content.classList.add('active');
        }
        
        function showImageSafe(path, type) {
            if (!path) return;
            const detail = document.getElementById('file-detail');
            const btn = document.createElement('button');
            btn.className = 'btn btn-primary';
            btn.style.marginBottom = '15px';
            btn.textContent = '← 返回详情';
            btn.onclick = function() { selectFileByPath(path); };
            const imgContainer = document.createElement('div');
            imgContainer.className = 'image-container';
            const img = document.createElement('img');
            img.src = '/api/image/' + encodeURIComponent(path);
            img.alt = type;
            imgContainer.appendChild(img);
            detail.innerHTML = '<div class="tab-content active"></div>';
            detail.querySelector('.tab-content').appendChild(btn);
            detail.querySelector('.tab-content').appendChild(imgContainer);
        }
        
        async function startConversion() {
            const dir = document.getElementById('scan-dir').value;
            if (!dir) {
                alert('请先选择要扫描的文件夹！');
                return;
            }
            
            if (flatFiles.length === 0) {
                alert('没有找到可转换的文件！');
                return;
            }
            
            const pendingFiles = flatFiles.filter(f => f.statusClass !== 'success');
            if (pendingFiles.length === 0) {
                alert('所有文件都已转换完成！');
                return;
            }
            
            if (confirm('确定要开始转换吗？将转换 ' + pendingFiles.length + ' 个文件。')) {
                try {
                    const response = await fetch('/api/convert/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            dir: dir
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('✓ 转换任务已启动！请查看「转换」页面监控进度。');
                        showPage('convert');
                        loadConversionStatus();
                    } else {
                        alert('✗ 启动转换失败：' + (result.error || '未知错误'));
                    }
                } catch (e) {
                    console.error('启动转换失败:', e);
                    alert('✗ 启动转换失败：' + e.message);
                }
            }
        }
        
        async function refreshStats() {
            const data = await api('/api/status');
            const p = data.progress || {};
            
            const total = p.total || 0;
            const completed = p.completed || 0;
            const success = p.success || 0;
            const failed = p.failed || 0;
            const pending = Math.max(0, total - completed);
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            
            document.getElementById('stat-success').textContent = success;
            document.getElementById('stat-pending').textContent = pending;
            document.getElementById('stat-failed').textContent = failed;
            document.getElementById('stat-total').textContent = total;
            
            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-text').textContent = pct + '%';
            document.getElementById('progress-detail').textContent = completed + ' / ' + total + ' 文件' + (p.currentFile ? ' - ' + p.currentFile : '');
            
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            if (btnStart) btnStart.style.display = data.is_running ? 'none' : 'inline-block';
            if (btnStop) btnStop.style.display = data.is_running ? 'inline-block' : 'none';
        }
        
        async function stopConversion() {
            await api('/api/convert/stop', 'POST');
            alert('转换已停止');
        }
        
        async function startConversionFromConvertPage() {
            const dir = document.getElementById('convert-dir').value;
            if (!dir) {
                alert('请输入要转换的目录路径！');
                return;
            }
            
            const config = {
                dir: dir,
                workers: parseInt(document.getElementById('workers').value) || 4,
                retryAttempts: parseInt(document.getElementById('retry-attempts').value) || 3,
                retryDelay: parseInt(document.getElementById('retry-delay').value) || 1,
                maxImageSize: parseInt(document.getElementById('max-image-size').value) || 500,
                overwrite: document.getElementById('overwrite').checked,
                recursive: document.getElementById('recursive').checked
            };
            
            if (confirm('确定要开始转换吗？')) {
                try {
                    const response = await fetch('/api/convert/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('✓ 转换任务已启动！请查看转换进度。');
                        loadConversionStatus();
                    } else {
                        alert('✗ 启动转换失败：' + (result.error || '未知错误'));
                    }
                } catch (e) {
                    console.error('启动转换失败:', e);
                    alert('✗ 启动转换失败：' + e.message);
                }
            }
        }
        
        async function refreshLogs() {
            const data = await api('/api/logs');
            const logs = data.logs || [];
            const box = document.getElementById('log-box');
            
            if (!logs.length) {
                box.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--primary);">暂无日志</div>';
                return;
            }
            
            box.innerHTML = logs.map(log => 
                '<div class="log-entry">' +
                '<span class="log-time">[' + log.time + ']</span>' +
                '<span class="log-level ' + log.level + '">' + log.level + '</span>' +
                '<span>' + log.message + '</span>' +
                '</div>'
            ).join('');
            
            box.scrollTop = box.scrollHeight;
        }
        
        async function clearLogs() {
            await api('/api/logs', 'DELETE');
            document.getElementById('log-box').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--primary);">暂无日志</div>';
        }
        
        function downloadLogs() {
            const box = document.getElementById('log-box');
            const text = box.textContent;
            
            if (!text || text === '暂无日志') {
                alert('没有日志可导出');
                return;
            }
            
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'nfo-converter-logs-' + new Date().toISOString().slice(0, 10) + '.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        // 初始化
        loadTheme();
        setInterval(refreshStats, 2000);
        refreshStats();
        refreshLogs();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/api/status')
def api_status():
    return jsonify({
        'is_running': _state['is_running'],
        'progress': _state['progress']
    })


@app.route('/api/scan')
def api_scan():
    directory = request.args.get('dir', '/workspace/test_movies')
    files = scan_directory(directory)
    _state['scan_results'] = files
    _state['progress']['total'] = len(files)
    _add_log('info', f'扫描完成，找到 {len(files)} 个视频文件')
    return jsonify({'files': files})


@app.route('/api/scan-tree')
def api_scan_tree():
    """返回树形结构的数据"""
    directory = request.args.get('dir', '/workspace/test_movies')
    tree = build_tree(directory)
    flat_files = []
    collect_files(tree, flat_files)
    
    _state['scan_results'] = flat_files
    _state['progress']['total'] = len(flat_files)
    _add_log('info', f'扫描完成，找到 {len(flat_files)} 个视频文件')
    
    return jsonify({
        'tree': tree,
        'flatFiles': flat_files
    })


def build_tree(directory):
    """构建目录树"""
    tree = []
    if not os.path.exists(directory):
        _add_log('warning', f'目录未找到: {directory}')
        return tree
    
    try:
        items = sorted(os.listdir(directory))
        
        # 先处理文件夹
        folders = []
        for item in items:
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                folder_node = {
                    'type': 'folder',
                    'name': item,
                    'path': item_path,
                    'children': build_tree(item_path),
                    'expanded': False
                }
                # 只有包含文件的文件夹才显示
                if count_files_in_tree(folder_node) > 0:
                    folders.append(folder_node)
        
        # 再处理视频文件
        for item in items:
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in ['.mp4', '.mkv', '.avi', '.ts', '.mov', '.m4v', '.wmv']:
                    base = os.path.splitext(item_path)[0]
                    has_nfo = os.path.exists(base + '.nfo')
                    has_vsmeta = os.path.exists(base + '.vsmeta')
                    
                    if has_nfo and has_vsmeta:
                        status_class = 'success'
                        status_text = '已转换'
                    elif has_nfo:
                        status_class = 'warning'
                        status_text = '待转换'
                    else:
                        status_class = 'danger'
                        status_text = '无NFO'
                    
                    tree.append({
                        'type': 'file',
                        'name': item,
                        'path': item_path,
                        'hasNfo': has_nfo,
                        'hasVsmeta': has_vsmeta,
                        'statusClass': status_class,
                        'statusText': status_text
                    })
        
        # 合并文件夹和文件
        tree = folders + tree
    except Exception as e:
        _add_log('error', f'扫描失败: {e}')
    
    return tree


def count_files_in_tree(node):
    """计算树中的文件数量"""
    if node['type'] == 'file':
        return 1
    return sum(count_files_in_tree(child) for child in node.get('children', []))


def collect_files(tree, flat_list):
    """收集所有文件到扁平列表"""
    for node in tree:
        if node['type'] == 'file':
            flat_list.append(node)
        elif node['type'] == 'folder':
            collect_files(node.get('children', []), flat_list)


@app.route('/api/file-detail')
def api_file_detail():
    path = request.args.get('path', '')
    return jsonify(get_file_detail(path))


@app.route('/api/image/<path:filepath>')
def api_image(filepath):
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath)


@app.route('/api/logs', methods=['GET', 'DELETE'])
def api_logs():
    if request.method == 'DELETE':
        _state['logs'] = []
    return jsonify({'logs': _state['logs']})


@app.route('/api/convert/start', methods=['POST'])
def api_convert_start():
    if _state['is_running']:
        return jsonify({'success': False, 'error': 'Conversion in progress'})
    
    data = request.get_json(silent=True) or {}
    directory = data.get('dir', '/workspace/test_movies')
    workers = data.get('workers', 4)
    retry_attempts = data.get('retryAttempts', 3)
    retry_delay = data.get('retryDelay', 1)
    max_image_size = data.get('maxImageSize', 500)
    overwrite = data.get('overwrite', False)
    recursive = data.get('recursive', True)
    
    _state['is_running'] = True
    _state['progress']['completed'] = 0
    _state['progress']['success'] = 0
    _state['progress']['failed'] = 0
    _state['progress']['current_file'] = ''
    
    threading.Thread(
        target=run_conversion_cli, 
        args=(directory, workers, retry_attempts, retry_delay, max_image_size, overwrite, recursive),
        daemon=True
    ).start()
    return jsonify({'success': True})


@app.route('/api/convert/stop', methods=['POST'])
def api_convert_stop():
    _state['is_running'] = False
    _add_log('info', '转换已停止')
    return jsonify({'success': True})


def run_conversion_cli(directory, workers=4, retry_attempts=3, retry_delay=1, max_image_size=500, overwrite=False, recursive=True):
    try:
        cmd = [
            sys.executable,
            '-c',
            '''
import sys
sys.path.insert(0, "''' + os.path.dirname(os.path.abspath(__file__)) + '''")
from nfo_to_vsmeta_converter_complete import NFOToVSMETAConverter, Config

config = Config()
config.directory = "''' + directory + '''"
config.max_workers = ''' + str(workers) + '''
config.retry_attempts = ''' + str(retry_attempts) + '''
config.retry_delay = ''' + str(retry_delay) + '''
config.max_image_size_kb = ''' + str(max_image_size) + '''
config.overwrite = ''' + str(overwrite).lower() + '''
config.recursive = ''' + str(recursive).lower() + '''

converter = NFOToVSMETAConverter(config)
files = converter.file_scanner.scan()

for dirname, filename in files:
    try:
        result = converter._process_single_file(dirname, filename)
        if result.get('success'):
            print(f"SUCCESS: {filename}")
        else:
            print(f"FAILED: {filename} - {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"ERROR: {filename} - {str(e)}")
'''
        ]
        
        _add_log('info', '开始转换（线程: ' + str(workers) + ', 重试: ' + str(retry_attempts) + '次）...')
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                _add_log('info', line)
                
                if 'SUCCESS:' in line:
                    _state['progress']['success'] += 1
                    _state['progress']['completed'] += 1
                elif 'FAILED:' in line or 'ERROR:' in line:
                    _state['progress']['failed'] += 1
                    _state['progress']['completed'] += 1
        
        process.wait()
        
        files = scan_directory(directory)
        _state['scan_results'] = files
        
        _add_log('success', '转换完成！成功: ' + str(_state['progress']['success']) + ', 失败: ' + str(_state['progress']['failed']))
        
    except Exception as e:
        _add_log('error', '转换失败: ' + str(e))
    finally:
        _state['is_running'] = False
        _state['progress']['current_file'] = ''


def scan_directory(directory):
    results = []
    if not os.path.exists(directory):
        _add_log('warning', f'目录未找到: {directory}')
        return results
    
    try:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.mp4', '.mkv', '.avi', '.ts', '.mov', '.m4v', '.wmv']:
                    filepath = os.path.join(root, filename)
                    base = os.path.splitext(filepath)[0]
                    has_nfo = os.path.exists(base + '.nfo')
                    has_vsmeta = os.path.exists(base + '.vsmeta')
                    
                    if has_nfo and has_vsmeta:
                        status_class = 'success'
                        status_text = '已转换'
                    elif has_nfo:
                        status_class = 'warning'
                        status_text = '待转换'
                    else:
                        status_class = 'danger'
                        status_text = '无NFO'
                    
                    results.append({
                        'name': filename,
                        'path': filepath,
                        'dir': root,
                        'hasNfo': has_nfo,
                        'hasVsmeta': has_vsmeta,
                        'statusClass': status_class,
                        'statusText': status_text
                    })
    except Exception as e:
        _add_log('error', f'扫描失败: {e}')
    
    return results


def get_file_detail(filepath):
    base, _ = os.path.splitext(filepath)
    nfo_path = base + '.nfo'
    vsmeta_path = base + '.vsmeta'
    
    nfo_content = ''
    if os.path.exists(nfo_path):
        try:
            with open(nfo_path, 'r', encoding='utf-8', errors='replace') as f:
                nfo_content = f.read(10000)
        except:
            nfo_content = '无法读取NFO文件'
    
    vsmeta_content = ''
    if os.path.exists(vsmeta_path):
        try:
            with open(vsmeta_path, 'rb') as f:
                raw = f.read(4096)
                try:
                    vsmeta_content = raw.decode('utf-8', errors='replace')
                except:
                    vsmeta_content = '[二进制文件]'
        except:
            vsmeta_content = '无法读取VSMETA文件'
    
    poster_extensions = ['.jpg', '.jpeg', '.png', '.tbn']
    fanart_extensions = ['.jpg', '.jpeg', '.png']
    
    poster_path = None
    for ext in poster_extensions:
        if os.path.exists(base + '-poster' + ext):
            poster_path = base + '-poster' + ext
            break
    if not poster_path:
        for ext in poster_extensions:
            if os.path.exists(base + ext):
                poster_path = base + ext
                break
    
    fanart_path = None
    for ext in fanart_extensions:
        if os.path.exists(base + '-fanart' + ext):
            fanart_path = base + '-fanart' + ext
            break
    if not fanart_path:
        for ext in fanart_extensions:
            if os.path.exists(os.path.join(os.path.dirname(filepath), 'fanart' + ext)):
                fanart_path = os.path.join(os.path.dirname(filepath), 'fanart' + ext)
                break
    
    poster_url = None
    if poster_path:
        poster_url = os.path.abspath(poster_path)
    
    fanart_url = None
    if fanart_path:
        fanart_url = os.path.abspath(fanart_path)
    
    return {
        'name': os.path.basename(filepath),
        'dir': os.path.dirname(filepath),
        'hasNfo': os.path.exists(nfo_path),
        'hasVsmeta': os.path.exists(vsmeta_path),
        'hasPoster': poster_path is not None,
        'hasFanart': fanart_path is not None,
        'nfoContent': nfo_content,
        'vsmetaContent': vsmeta_content,
        'posterUrl': poster_url,
        'fanartUrl': fanart_url
    }


if __name__ == '__main__':
    if not HAS_FLASK:
        print('请先安装 Flask：pip install flask')
        sys.exit(1)
    
    print('''
╔══════════════════════════════════════════╗
║   NFO 转 VSMETA 转换器 Web UI        ║
║   🌳 树形结构版 - 支持展开/折叠     ║
╠══════════════════════════════════════════╣
║   访问地址: http://localhost:8004     ║
╚══════════════════════════════════════════╝
    ''')
    
    app.run(host='0.0.0.0', port=8004, debug=True)
