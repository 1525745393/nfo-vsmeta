#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI
==========================================
通过subprocess调用转换器，支持封面和背景图查看
"""

import argparse
import os
import sys
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import threading

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
    "progress": {
        "total": 0,
        "completed": 0,
        "success": 0,
        "failed": 0,
        "current_file": ""
    },
    "scan_results": [],
    "logs": []
}


def _add_log(level: str, message: str):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    _state["logs"].append(entry)
    if len(_state["logs"]) > 1000:
        _state["logs"] = _state["logs"][-1000:]


INDEX_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFO 转 VSMETA 转换器</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0e14;
            --bg2: #111620;
            --bg3: #1a2030;
            --border: #2a3445;
            --border-light: #3a4555;
            --text: #f0f3f6;
            --text2: #9aa5b5;
            --text3: #6b7585;
            --accent: #4a9eff;
            --accent-light: #6ab0ff;
            --accent-dark: #3080e0;
            --success: #4ade80;
            --success-light: #60d090;
            --warning: #fbbf24;
            --warning-light: #fcd34d;
            --danger: #f87171;
            --danger-light: #fca5a5;
            --gradient-primary: linear-gradient(135deg, #4a9eff 0%, #6366f1 100%);
            --gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            --gradient-danger: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
            --shadow-glow: 0 0 20px rgba(74, 158, 255, 0.3);
        }
        
        [data-theme="light"] {
            --bg: #f8fafc;
            --bg2: #ffffff;
            --bg3: #f1f5f9;
            --border: #e2e8f0;
            --border-light: #cbd5e1;
            --text: #0f172a;
            --text2: #475569;
            --text3: #94a3b8;
            --accent: #3b82f6;
            --accent-light: #60a5fa;
            --accent-dark: #2563eb;
            --success: #22c55e;
            --success-light: #4ade80;
            --warning: #f59e0b;
            --warning-light: #fbbf24;
            --danger: #ef4444;
            --danger-light: #f87171;
            --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
            --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.2);
        }
        
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0;
            transition: all 0.2s ease;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .header {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 1.25rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .nav {
            display: flex;
            gap: 0.75rem;
            background: var(--bg2);
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }
        
        .nav-btn {
            padding: 0.75rem 1.5rem;
            border: none;
            background: transparent;
            color: var(--text2);
            cursor: pointer;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 500;
            position: relative;
            overflow: hidden;
        }
        
        .nav-btn:hover {
            background: var(--bg3);
            color: var(--text);
        }
        
        .nav-btn.active {
            background: var(--gradient-primary);
            color: white;
            box-shadow: var(--shadow-md);
        }
        
        .page { 
            display: none; 
            padding: 2rem 2.5rem;
            animation: fadeIn 0.3s ease;
        }
        
        .page.active { display: block; }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }
        
        .card.success::before { background: var(--gradient-success); }
        .card.warning::before { background: var(--gradient-warning); }
        .card.danger::before { background: var(--gradient-danger); }
        
        .stat-label {
            font-size: 0.85rem;
            color: var(--text3);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 2.25rem;
            font-weight: 700;
            margin-top: 0.25rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--bg2);
            color: var(--text);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            margin-right: 0.75rem;
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.3s, height 0.3s;
        }
        
        .btn:hover::before {
            width: 200px;
            height: 200px;
        }
        
        .btn:hover {
            background: var(--bg3);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-primary {
            background: var(--gradient-primary);
            color: white;
            border: none;
            box-shadow: var(--shadow-md);
        }
        
        .btn-primary:hover {
            box-shadow: var(--shadow-lg), var(--shadow-glow);
        }
        
        .btn-danger {
            background: var(--gradient-danger);
            color: white;
            border: none;
        }
        
        .btn-success {
            background: var(--gradient-success);
            color: white;
            border: none;
        }
        
        .input {
            width: 100%;
            padding: 0.875rem 1rem;
            background: var(--bg2);
            border: 2px solid var(--border);
            color: var(--text);
            border-radius: 8px;
            margin-top: 0.5rem;
            font-size: 0.95rem;
            box-shadow: var(--shadow-sm);
        }
        
        .input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: var(--shadow-md), 0 0 0 3px rgba(74, 158, 255, 0.1);
        }
        
        .progress-bar {
            height: 32px;
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            margin: 1.25rem 0;
            box-shadow: var(--shadow-sm);
        }
        
        .progress-fill {
            height: 100%;
            background: var(--gradient-primary);
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.2) 50%,
                transparent 100%
            );
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .two-col {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 1100px) { 
            .two-col { grid-template-columns: 1fr; }
        }
        
        .tree {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            max-height: 65vh;
            overflow-y: auto;
            box-shadow: var(--shadow-sm);
        }
        
        .tree-item {
            padding: 0.875rem;
            cursor: pointer;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
            border: 1px solid transparent;
        }
        
        .tree-item:hover {
            background: var(--bg3);
            border-color: var(--accent);
            transform: translateX(4px);
        }
        
        .tree-item.selected {
            background: rgba(74, 158, 255, 0.1);
            border-color: var(--accent);
            box-shadow: var(--shadow-glow);
        }
        
        .badge {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            box-shadow: var(--shadow-sm);
        }
        
        .badge.success {
            background: var(--gradient-success);
            color: white;
        }
        
        .badge.warning {
            background: var(--gradient-warning);
            color: white;
        }
        
        .badge.danger {
            background: var(--gradient-danger);
            color: white;
        }
        
        .detail {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }
        
        .detail-tabs {
            display: flex;
            gap: 0.5rem;
            background: var(--bg);
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
            flex-wrap: wrap;
            overflow-x: auto;
        }
        
        .detail-tab {
            padding: 0.5rem 1rem;
            border: none;
            background: transparent;
            color: var(--text2);
            cursor: pointer;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            white-space: nowrap;
        }
        
        .detail-tab:hover {
            background: var(--bg2);
            color: var(--text);
        }
        
        .detail-tab.active {
            background: var(--gradient-primary);
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        .detail-content { 
            padding: 1.25rem; 
            display: none;
            animation: fadeIn 0.2s ease;
        }
        
        .detail-content.active { display: block; }
        
        .compare { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 1.25rem; 
        }
        
        @media (max-width: 900px) { 
            .compare { grid-template-columns: 1fr; } 
        }
        
        .code {
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 55vh;
            box-shadow: var(--shadow-sm);
        }
        
        .image-container {
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            min-height: 350px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-sm);
        }
        
        .image-container img {
            max-width: 100%;
            max-height: 550px;
            border-radius: 8px;
            object-fit: contain;
            box-shadow: var(--shadow-lg);
            transition: transform 0.3s ease;
        }
        
        .image-container img:hover {
            transform: scale(1.02);
        }
        
        .image-placeholder {
            color: var(--text3);
            font-size: 1.15rem;
        }
        
        .log-box {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            max-height: 55vh;
            overflow-y: auto;
            box-shadow: var(--shadow-sm);
        }
        
        .alert {
            background: var(--bg2);
            border: 2px solid var(--warning);
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            color: var(--warning);
            box-shadow: var(--shadow-md);
        }
        
        h2 {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--text);
        }
        
        h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text);
        }
        
        h4 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: var(--text);
        }
        
        ::selection {
            background: var(--accent);
            color: white;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-light);
        }
        
        /* 工作流步骤 */
        .workflow-step {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            background: var(--bg3);
            border: 2px solid var(--border);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .workflow-step.active {
            background: rgba(74, 158, 255, 0.1);
            border-color: var(--accent);
            box-shadow: var(--shadow-glow);
        }
        
        .workflow-step.completed {
            background: rgba(74, 222, 128, 0.1);
            border-color: var(--success);
        }
        
        .step-number {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--gradient-primary);
            color: white;
            border-radius: 50%;
            font-weight: 700;
            font-size: 0.9rem;
        }
        
        .workflow-step.completed .step-number {
            background: var(--gradient-success);
        }
        
        .step-text {
            font-weight: 500;
            color: var(--text);
        }
        
        .workflow-arrow {
            color: var(--text3);
            font-size: 1.25rem;
            font-weight: 700;
        }
        
        /* 快捷操作按钮 */
        .card button {
            width: 100%;
            height: 48px;
            font-size: 0.95rem;
        }
        
        /* 导出按钮 */
        button.btn-success {
            background: var(--gradient-success);
            color: white;
            border: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎬 NFO 转 VSMETA 转换器</div>
        <button class="btn" onclick="toggleTheme()">🌙 主题</button>
    </div>
    
    <div class="nav">
        <button class="nav-btn active" onclick="showPage('dashboard')">📊 仪表盘</button>
        <button class="nav-btn" onclick="showPage('files')">📁 文件</button>
        <button class="nav-btn" onclick="showPage('convert')">🚀 转换</button>
        <button class="nav-btn" onclick="showPage('logs')">📋 日志</button>
    </div>
    
    <div class="page active" id="page-dashboard">
        <h2 style="margin-bottom: 1.5rem;">📊 控制面板</h2>
        
        <!-- 工作流引导 -->
        <div class="card" style="margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;">🚀 快速开始</h3>
            <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                <div class="workflow-step active" id="step-1">
                    <div class="step-number">1</div>
                    <div class="step-text">选择目录</div>
                </div>
                <div class="workflow-arrow">→</div>
                <div class="workflow-step" id="step-2">
                    <div class="step-number">2</div>
                    <div class="step-text">扫描文件</div>
                </div>
                <div class="workflow-arrow">→</div>
                <div class="workflow-step" id="step-3">
                    <div class="step-number">3</div>
                    <div class="step-text">开始转换</div>
                </div>
                <div class="workflow-arrow">→</div>
                <div class="workflow-step" id="step-4">
                    <div class="step-number">4</div>
                    <div class="step-text">完成</div>
                </div>
            </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="grid">
            <div class="card success">
                <div class="stat-label">✅ 已转换</div>
                <div class="stat-value" id="stat-success">0</div>
            </div>
            <div class="card warning">
                <div class="stat-label">⏳ 待转换</div>
                <div class="stat-value" id="stat-pending">0</div>
            </div>
            <div class="card danger">
                <div class="stat-label">❌ 失败</div>
                <div class="stat-value" id="stat-failed">0</div>
            </div>
            <div class="card">
                <div class="stat-label">📁 总文件数</div>
                <div class="stat-value" id="stat-total">0</div>
            </div>
        </div>
        
        <!-- 转换进度 -->
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3>📈 转换进度</h3>
                <div id="progress-percentage" style="font-size: 1.5rem; font-weight: 700; color: var(--accent);">0%</div>
            </div>
            <div class="progress-bar" style="height: 40px;">
                <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 1rem; color: var(--text2);">
                <div id="progress-text">等待中...</div>
                <div id="progress-detail">0 / 0 文件</div>
            </div>
            
            <!-- 速度指示器 -->
            <div id="speed-indicator" style="display: none; margin-top: 1rem; padding: 0.75rem; background: var(--bg3); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <span>⚡ 转换速度</span>
                    <span id="conversion-speed">0 文件/秒</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                    <span>⏱️ 预计剩余</span>
                    <span id="time-remaining">计算中...</span>
                </div>
            </div>
        </div>
        
        <!-- 快捷操作 -->
        <div class="card" style="margin-top: 1.5rem;">
            <h3 style="margin-bottom: 1rem;">⚡ 快捷操作</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <button class="btn btn-primary" onclick="showPage('files'); refreshFiles();">
                    📁 扫描文件
                </button>
                <button class="btn btn-primary" onclick="showPage('convert'); startConversion();">
                    ▶️ 开始转换
                </button>
                <button class="btn" onclick="showPage('logs'); refreshLogs();">
                    📋 查看日志
                </button>
                <button class="btn" onclick="toggleTheme()">
                    🌙 切换主题
                </button>
            </div>
        </div>
    </div>
    
    <div class="page" id="page-files">
        <h2 style="margin-bottom: 1.5rem;">📁 文件管理</h2>
        
        <!-- 搜索和过滤 -->
        <div class="card" style="margin-bottom: 1.5rem;">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1rem; align-items: end;">
                <div>
                    <label style="color: var(--text2); font-size: 0.9rem;">📂 目录路径</label>
                    <input type="text" class="input" id="config-dir" value="/workspace/test_movies" placeholder="/path/to/movies">
                </div>
                <div>
                    <label style="color: var(--text2); font-size: 0.9rem;">🔍 状态过滤</label>
                    <select class="input" id="filter-status" onchange="filterFiles()">
                        <option value="all">全部</option>
                        <option value="converted">已转换</option>
                        <option value="pending">待转换</option>
                        <option value="no-nfo">无NFO</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="refreshFiles()" style="height: fit-content;">
                    🔄 扫描
                </button>
            </div>
        </div>
        
        <div class="two-col">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <h3>📋 文件列表</h3>
                    <div id="file-count" style="color: var(--text2); font-size: 0.9rem;">0 个文件</div>
                </div>
                <div class="tree" id="file-tree">
                    <div style="color: var(--text2); padding: 1rem; text-align: center;">点击「扫描」加载文件</div>
                </div>
            </div>
            
            <div>
                <h3 style="margin-bottom: 0.75rem;">📋 文件详情</h3>
                <div class="detail">
                    <div class="detail-tabs">
                        <button class="detail-tab active" onclick="showDetail('overview')">📋 概览</button>
                        <button class="detail-tab" onclick="showDetail('nfo')">📄 NFO</button>
                        <button class="detail-tab" onclick="showDetail('vsmeta')">📝 VSMETA</button>
                        <button class="detail-tab" onclick="showDetail('compare')">🔄 对比</button>
                        <button class="detail-tab" onclick="showDetail('poster')">🖼️ 封面</button>
                        <button class="detail-tab" onclick="showDetail('fanart')">🎬 背景图</button>
                    </div>
                    
                    <div class="detail-content active" id="detail-overview">
                        <div id="overview-empty" style="color: var(--text2); padding: 2rem; text-align: center;">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem;">👈</div>
                            <div>从列表中选择一个文件查看详情</div>
                        </div>
                        <div id="overview-content"></div>
                    </div>
                    
                    <div class="detail-content" id="detail-nfo">
                        <div id="nfo-content" class="code">无 NFO 内容</div>
                    </div>
                    
                    <div class="detail-content" id="detail-vsmeta">
                        <div id="vsmeta-content" class="code">无 VSMETA 内容</div>
                    </div>
                    
                    <div class="detail-content" id="detail-compare">
                        <div class="compare">
                            <div>
                                <h4>NFO 内容</h4>
                                <div id="compare-nfo" class="code">无内容</div>
                            </div>
                            <div>
                                <h4>VSMETA 内容</h4>
                                <div id="compare-vsmeta" class="code">无内容</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-content" id="detail-poster">
                        <h4>封面图片</h4>
                        <div class="image-container" id="poster-container">
                            <div class="image-placeholder">请先选择文件</div>
                        </div>
                    </div>
                    
                    <div class="detail-content" id="detail-fanart">
                        <h4>背景图片</h4>
                        <div class="image-container" id="fanart-container">
                            <div class="image-placeholder">请先选择文件</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="page" id="page-convert">
        <h2 style="margin-bottom: 1.5rem;">🚀 批量转换</h2>
        
        <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid var(--accent);">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="font-size: 2rem;">💡</span>
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">提示</div>
                    <div style="color: var(--text2); font-size: 0.9rem;">此版本使用 subprocess 调用转换器，稳定可靠！支持批量转换、自动跳过已转换文件。</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 1.5rem;">⚙️ 转换设置</h3>
            
            <div style="margin-bottom: 1.5rem;">
                <label style="color: var(--text2); font-size: 0.9rem;">📂 处理目录</label>
                <input type="text" class="input" id="convert-dir" value="/workspace/test_movies">
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                <div>
                    <label style="color: var(--text2); font-size: 0.9rem;">⚡ 工作线程数</label>
                    <input type="number" class="input" id="workers" value="4" min="1" max="16">
                </div>
                <div>
                    <label style="color: var(--text2); font-size: 0.9rem;">📋 选项</label>
                    <div style="margin-top: 0.75rem;">
                        <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; margin-bottom: 0.5rem;">
                            <input type="checkbox" id="overwrite"> 
                            <span>覆盖已有 VSMETA</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                            <input type="checkbox" id="recursive" checked>
                            <span>递归扫描子目录</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; gap: 1rem;">
                <button class="btn btn-primary" id="btn-start" onclick="startConversion()" style="flex: 1;">
                    ▶️ 开始转换
                </button>
                <button class="btn btn-danger" id="btn-stop" onclick="stopConversion()" style="flex: 1; display: none;">
                    ⏹️ 停止转换
                </button>
            </div>
        </div>
    </div>
    
    <div class="page" id="page-logs">
        <h2 style="margin-bottom: 1.5rem;">📋 运行日志</h2>
        <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
            <button class="btn" onclick="refreshLogs()">
                🔄 刷新
            </button>
            <button class="btn" onclick="clearLogs()">
                🗑️ 清空
            </button>
            <button class="btn" onclick="downloadLogs()">
                📥 导出日志
            </button>
        </div>
        <div class="log-box" id="log-box">暂无日志</div>
    </div>
    
    <script>
        let scanResults = [];
        let selectedIndex = -1;
        
        // ==================== 交互体验优化 ====================
        
        // 拖拽上传功能
        function initDragDrop() {
            const dropZone = document.getElementById('config-dir');
            if (!dropZone) return;
            
            dropZone.parentElement.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.parentElement.style.border = '2px dashed var(--accent)';
                dropZone.parentElement.style.background = 'rgba(74, 158, 255, 0.1)';
            });
            
            dropZone.parentElement.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.parentElement.style.border = '';
                dropZone.parentElement.style.background = '';
            });
            
            dropZone.parentElement.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.parentElement.style.border = '';
                dropZone.parentElement.style.background = '';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const path = files[0].path || files[0].webkitRelativePath;
                    if (path) {
                        const dir = path.split('/')[0];
                        dropZone.value = '/' + dir;
                        showNotification('已设置目录：' + dir, 'success');
                    }
                }
            });
        }
        
        // 快捷键支持
        function initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + Enter - 开始转换
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    startConversion();
                    return;
                }
                
                // Ctrl/Cmd + R - 刷新文件列表
                if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                    e.preventDefault();
                    refreshFiles();
                    return;
                }
                
                // Escape - 停止转换
                if (e.key === 'Escape') {
                    stopConversion();
                    return;
                }
                
                // T - 切换主题
                if (e.key === 't' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT') {
                    toggleTheme();
                    return;
                }
                
                // 1-4 - 切换页面
                if (e.key === '1' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT') {
                    showPage('dashboard');
                    return;
                }
                if (e.key === '2' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT') {
                    showPage('files');
                    return;
                }
                if (e.key === '3' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT') {
                    showPage('convert');
                    return;
                }
                if (e.key === '4' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT') {
                    showPage('logs');
                    return;
                }
                
                // 上下箭头 - 文件列表导航
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    if (document.querySelector('.page.active')?.id === 'page-files') {
                        e.preventDefault();
                        navigateFileList(e.key === 'ArrowUp' ? -1 : 1);
                    }
                }
            });
        }
        
        // 文件列表键盘导航
        function navigateFileList(direction) {
            if (scanResults.length === 0) return;
            
            selectedIndex += direction;
            if (selectedIndex < 0) selectedIndex = 0;
            if (selectedIndex >= scanResults.length) selectedIndex = scanResults.length - 1;
            
            selectFile(selectedIndex);
            
            // 滚动到可见
            const selectedEl = document.getElementById('file-' + selectedIndex);
            if (selectedEl) {
                selectedEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        // 通知系统
        function showNotification(message, type='info') {
            const existing = document.querySelector('.notification');
            if (existing) existing.remove();
            
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                padding: 1rem 1.5rem;
                background: var(--bg2);
                border: 2px solid var(--${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'accent'});
                border-radius: 8px;
                box-shadow: var(--shadow-lg);
                z-index: 1000;
                animation: slideIn 0.3s ease;
                max-width: 400px;
            `;
            notification.innerHTML = `
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <span style="font-size:1.5rem;">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
                    <span>${message}</span>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // 添加动画样式
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
            
            setTimeout(() => {
                notification.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
        
        // 工具提示
        function initTooltips() {
            const tooltips = document.querySelectorAll('[data-tooltip]');
            tooltips.forEach(el => {
                el.addEventListener('mouseenter', (e) => {
                    const tooltip = document.createElement('div');
                    tooltip.className = 'tooltip';
                    tooltip.textContent = el.dataset.tooltip;
                    tooltip.style.cssText = `
                        position: absolute;
                        background: var(--bg3);
                        color: var(--text);
                        padding: 0.5rem 0.75rem;
                        border-radius: 6px;
                        font-size: 0.85rem;
                        box-shadow: var(--shadow-md);
                        z-index: 1000;
                        white-space: nowrap;
                        pointer-events: none;
                    `;
                    el.appendChild(tooltip);
                });
                
                el.addEventListener('mouseleave', () => {
                    const tooltip = el.querySelector('.tooltip');
                    if (tooltip) tooltip.remove();
                });
            });
        }
        
        // 初始化所有交互功能
        document.addEventListener('DOMContentLoaded', () => {
            initDragDrop();
            initKeyboardShortcuts();
            initTooltips();
            updateWorkflowSteps();
            showNotification('快捷键提示：1-4切换页面，T切换主题，Ctrl+Enter开始转换', 'info');
        });
        
        // ==================== 工作流指示器 ====================
        function updateWorkflowSteps() {
            const dirInput = document.getElementById('config-dir');
            const step1 = document.getElementById('step-1');
            const step2 = document.getElementById('step-2');
            const step3 = document.getElementById('step-3');
            const step4 = document.getElementById('step-4');
            
            if (!dirInput || !step1) return;
            
            // 步骤1: 选择目录 - 始终完成
            step1.classList.add('completed');
            
            // 步骤2: 扫描文件
            if (scanResults.length > 0) {
                step2.classList.remove('active');
                step2.classList.add('completed');
            }
            
            // 步骤3: 开始转换
            if (_state && _state.is_running) {
                step3.classList.add('active');
            }
            
            // 步骤4: 完成
            if (_state && !_state.is_running && _state.progress && _state.progress.completed > 0) {
                step4.classList.add('completed');
            }
        }
        
        // ==================== 文件过滤 ====================
        function filterFiles() {
            const filter = document.getElementById('filter-status')?.value || 'all';
            renderFileTree(filter);
        }
        
        // ==================== 导出日志 ====================
        function downloadLogs() {
            const logBox = document.getElementById('log-box');
            if (!logBox) return;
            
            const logs = Array.from(logBox.querySelectorAll('div')).map(div => div.textContent).join('\n');
            
            if (!logs || logs === '暂无日志') {
                showNotification('没有日志可导出', 'error');
                return;
            }
            
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfo-converter-logs-${new Date().toISOString().slice(0,10)}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('日志已导出', 'success');
        }
        
        async function api(url, method='GET', data=null) {
            try {
                const opts = { method, headers: {'Content-Type': 'application/json'} };
                if (data) opts.body = JSON.stringify(data);
                const resp = await fetch(url, opts);
                return await resp.json();
            } catch (e) {
                console.error('API error:', e);
                return {};
            }
        }
        
        function showPage(pageName) {
            document.querySelectorAll('.nav-btn').forEach(btn => 
                btn.classList.toggle('active', btn.textContent.includes(pageName)));
            
            document.querySelectorAll('.page').forEach(page => 
                page.classList.toggle('active', page.id === 'page-' + pageName));
        }
        
        function toggleTheme() {
            const html = document.documentElement;
            const newTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        function showDetail(tab) {
            document.querySelectorAll('.detail-tab').forEach(t => 
                t.classList.toggle('active', t.textContent.includes(tab)));
            
            document.querySelectorAll('.detail-content').forEach(c => 
                c.classList.toggle('active', c.id === 'detail-' + tab));
        }
        
        async function refreshFiles() {
            const dir = document.getElementById('config-dir').value;
            document.getElementById('file-tree').innerHTML = '<div style="text-align:center; padding:1rem;">Scanning...</div>';
            
            try {
                const data = await api('/api/scan?dir=' + encodeURIComponent(dir));
                scanResults = data.files || [];
                renderFileTree();
                await refreshStats();
            } catch (e) {
                console.error(e);
            }
        }
        
        function renderFileTree(filter='all') {
            const container = document.getElementById('file-tree');
            const fileCount = document.getElementById('file-count');
            
            if (!scanResults.length) {
                container.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text2);">未找到视频文件<br><br>支持的格式：.mp4, .mkv, .avi, .ts, .mov</div>';
                if (fileCount) fileCount.textContent = '0 个文件';
                return;
            }
            
            let filtered = scanResults;
            
            if (filter !== 'all') {
                filtered = scanResults.filter(file => {
                    if (filter === 'converted') return file.statusClass === 'success';
                    if (filter === 'pending') return file.statusClass === 'warning';
                    if (filter === 'no-nfo') return file.statusClass === 'danger';
                    return true;
                });
            }
            
            if (fileCount) fileCount.textContent = `${filtered.length} 个文件`;
            
            if (!filtered.length) {
                container.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text2);">没有符合条件的文件</div>';
                return;
            }
            
            container.innerHTML = filtered.map((file, idx) => `
                <div class="tree-item" onclick="selectFilteredFile('${file.path}')" id="file-${file.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                    <span>🎬</span>
                    <span style="flex:1;">${file.name}</span>
                    <span class="badge ${file.statusClass}">${file.statusText}</span>
                </div>
            `).join('');
        }
        
        function selectFilteredFile(filepath) {
            const file = scanResults.find(f => f.path === filepath);
            if (file) {
                const idx = scanResults.indexOf(file);
                selectFile(idx);
            }
        }
        
        function selectFile(index) {
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            const file = scanResults[index];
            if (file) {
                const el = document.getElementById('file-' + file.path.replace(/[^a-zA-Z0-9]/g, '_'));
                if (el) el.classList.add('selected');
            }
            
            renderFileDetail(file);
        }
        
        async function renderFileDetail(file) {
            try {
                const data = await api('/api/file-detail?path=' + encodeURIComponent(file.path));
                
                document.getElementById('overview-empty').style.display = 'none';
                document.getElementById('overview-content').innerHTML = `
                    <div style="display:grid; gap:1rem; grid-template-columns:repeat(2, 1fr);">
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">文件名</div>
                            <div style="font-weight:600;">${data.name || '-'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">目录</div>
                            <div style="font-size:0.9rem; color:var(--text2);">${data.dir || '-'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">NFO</div>
                            <div>${data.hasNfo ? '<span class="badge success">✅ 存在</span>' : '<span class="badge danger">❌ 缺失</span>'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">VSMETA</div>
                            <div>${data.hasVsmeta ? '<span class="badge success">✅ 存在</span>' : '<span class="badge warning">⏳ 缺失</span>'}</div>
                        </div>
                    </div>
                    <div style="display:grid; gap:1rem; grid-template-columns:repeat(2, 1fr); margin-top:1rem;">
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">封面</div>
                            <div>${data.hasPoster ? '<span class="badge success">✅ 存在</span>' : '<span class="badge warning">⏳ 缺失</span>'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">背景图</div>
                            <div>${data.hasFanart ? '<span class="badge success">✅ 存在</span>' : '<span class="badge warning">⏳ 缺失</span>'}</div>
                        </div>
                    </div>
                    ${data.metadata ? `
                        <div style="margin-top:1.5rem;">
                            <h4 style="margin-bottom:0.75rem;">元数据</h4>
                            <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                                <div style="margin-bottom:0.5rem;"><strong>标题:</strong> ${data.metadata.title || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>年份:</strong> ${data.metadata.year || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>评分:</strong> ${data.metadata.rating || '-'}</div>
                                <div><strong>简介:</strong> ${data.metadata.plot || '-'}</div>
                            </div>
                        </div>
                    ` : ''}
                `;
                
                document.getElementById('nfo-content').textContent = data.nfoContent || '无 NFO 内容';
                document.getElementById('compare-nfo').textContent = data.nfoContent || '无 NFO 内容';
                
                document.getElementById('vsmeta-content').textContent = data.vsmetaContent || '无 VSMETA 内容';
                document.getElementById('compare-vsmeta').textContent = data.vsmetaContent || '无 VSMETA 内容';
                
                const posterContainer = document.getElementById('poster-container');
                if (data.posterUrl) {
                    posterContainer.innerHTML = `<img src="${data.posterUrl}" alt="封面" onclick="window.open('${data.posterUrl}', '_blank')" style="cursor: zoom-in;">`;
                } else {
                    posterContainer.innerHTML = '<div class="image-placeholder">无封面图片</div>';
                }
                
                const fanartContainer = document.getElementById('fanart-container');
                if (data.fanartUrl) {
                    fanartContainer.innerHTML = `<img src="${data.fanartUrl}" alt="背景图" onclick="window.open('${data.fanartUrl}', '_blank')" style="cursor: zoom-in;">`;
                } else {
                    fanartContainer.innerHTML = '<div class="image-placeholder">无背景图片</div>';
                }
                
            } catch (e) {
                console.error('Detail error:', e);
            }
        }
        
        async function refreshStats() {
            try {
                const data = await api('/api/status');
                const p = data.progress || {};
                
                // 更新统计卡片
                document.getElementById('stat-total').textContent = p.total || 0;
                document.getElementById('stat-success').textContent = p.success || 0;
                document.getElementById('stat-pending').textContent = Math.max(0, (p.total || 0) - (p.completed || 0));
                document.getElementById('stat-failed').textContent = p.failed || 0;
                
                // 计算百分比
                const pct = p.total > 0 ? Math.round((p.completed / p.total) * 100) : 0;
                
                // 更新进度条
                document.getElementById('progress-fill').style.width = pct + '%';
                document.getElementById('progress-percentage').textContent = pct + '%';
                
                // 更新进度文本
                if (p.currentFile) {
                    document.getElementById('progress-text').textContent = `正在转换: ${p.currentFile}`;
                    document.getElementById('progress-detail').textContent = `${p.completed} / ${p.total} 文件`;
                } else {
                    document.getElementById('progress-text').textContent = pct === 100 ? '转换完成！' : '等待中...';
                    document.getElementById('progress-detail').textContent = `${p.completed} / ${p.total} 文件`;
                }
                
                // 更新按钮状态
                const btnStart = document.getElementById('btn-start');
                const btnStop = document.getElementById('btn-stop');
                if (btnStart) btnStart.style.display = data.is_running ? 'none' : 'inline-block';
                if (btnStop) btnStop.style.display = data.is_running ? 'inline-block' : 'none';
                
                // 更新工作流指示器
                updateWorkflowSteps();
                
            } catch (e) {
                console.error(e);
            }
        }
        
        async function startConversion() {
            try {
                await api('/api/convert/start', 'POST', {
                    dir: document.getElementById('convert-dir').value,
                    workers: parseInt(document.getElementById('workers').value),
                    overwrite: document.getElementById('overwrite').checked
                });
                showNotification('开始转换...', 'info');
            } catch (e) {
                console.error(e);
            }
        }
        
        async function stopConversion() {
            try {
                await api('/api/convert/stop', 'POST');
                showNotification('转换已停止', 'warning');
            } catch (e) {
                console.error(e);
            }
        }
        
        async function refreshLogs() {
            try {
                const data = await api('/api/logs');
                const logs = data.logs || [];
                
                const container = document.getElementById('log-box');
                if (!logs.length) {
                    container.innerHTML = '<div>无日志</div>';
                    return;
                }
                
                container.innerHTML = logs.map(log => `
                    <div>
                        <span style="color: var(--text2);">[${log.time}]</span>
                        <span style="font-weight:600;">[${log.level.toUpperCase()}]</span>
                        <span> ${log.message}</span>
                    </div>
                `).join('');
                
            } catch (e) {
                console.error(e);
            }
        }
        
        async function clearLogs() {
            try {
                await api('/api/logs', 'DELETE');
                document.getElementById('log-box').innerHTML = '<div>无日志</div>';
            } catch (e) {
                console.error(e);
            }
        }
        
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
        
        setInterval(refreshStats, 2000);
        setInterval(refreshLogs, 3000);
        
        refreshStats();
    </script>
</body>
</html>
'''


if HAS_FLASK:
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
    
    
    @app.route('/api/file-detail')
    def api_file_detail():
        path = request.args.get('path', '')
        return jsonify(get_file_detail(path))
    
    
    @app.route('/api/image')
    def api_image():
        path = request.args.get('path', '')
        if not path or not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.isfile(path):
            return jsonify({'error': 'Not a file'}), 400
        
        ext = os.path.splitext(path)[1].lower()
        mimetypes = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.tbn': 'image/jpeg'
        }
        mimetype = mimetypes.get(ext, 'application/octet-stream')
        
        return send_file(path, mimetype=mimetype)
    
    
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
        
        _state['is_running'] = True
        _state['progress']['completed'] = 0
        _state['progress']['success'] = 0
        _state['progress']['failed'] = 0
        _state['progress']['current_file'] = ''
        
        threading.Thread(target=run_conversion_cli, args=(directory,), daemon=True).start()
        return jsonify({'success': True})
    
    
    @app.route('/api/convert/stop', methods=['POST'])
    def api_convert_stop():
        _state['is_running'] = False
        _add_log('info', '转换已停止')
        return jsonify({'success': True})


def run_conversion_cli(directory):
    try:
        cmd = [
            sys.executable,
            '-c',
            f'''
import sys
sys.path.insert(0, "{os.path.dirname(os.path.abspath(__file__))}")
from nfo_to_vsmeta_converter_complete import NFOToVSMETAConverter, Config

config = Config()
config.directory = "{directory}"
config.max_workers = 4

converter = NFOToVSMETAConverter(config)
files = converter.file_scanner.scan()

for dirname, filename in files:
    try:
        result = converter._process_single_file(dirname, filename)
        if result.get('success'):
            print(f"SUCCESS: {{filename}}")
        else:
            print(f"FAILED: {{filename}} - {{result.get('error', 'Unknown error')}}")
    except Exception as e:
        print(f"ERROR: {{filename}} - {{str(e)}}")
'''
        ]
        
        _add_log('info', '开始转换...')
        
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
        
        _add_log('success', f'转换完成！成功: {_state["progress"]["success"]}, 失败: {_state["progress"]["failed"]}')
        
    except Exception as e:
        _add_log('error', f'转换失败: {str(e)}')
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
        except Exception as e:
            nfo_content = f'Cannot read: {e}'
    
    vsmeta_content = ''
    if os.path.exists(vsmeta_path):
        try:
            with open(vsmeta_path, 'rb') as f:
                raw = f.read(4096)
                try:
                    vsmeta_content = raw.decode('utf-8', errors='replace')
                except Exception:
                    vsmeta_content = f'[Binary, {len(raw)} bytes]'
        except Exception as e:
            vsmeta_content = f'Cannot read: {e}'
    
    metadata = parse_nfo_metadata(nfo_path)
    
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
    if not poster_path:
        for ext in poster_extensions:
            if os.path.exists(os.path.join(os.path.dirname(filepath), 'poster' + ext)):
                poster_path = os.path.join(os.path.dirname(filepath), 'poster' + ext)
                break
    if not poster_path:
        for ext in poster_extensions:
            if os.path.exists(os.path.join(os.path.dirname(filepath), 'folder' + ext)):
                poster_path = os.path.join(os.path.dirname(filepath), 'folder' + ext)
                break
    
    fanart_path = None
    for ext in fanart_extensions:
        if os.path.exists(base + '-fanart' + ext):
            fanart_path = base + '-fanart' + ext
            break
    if not fanart_path:
        for ext in fanart_extensions:
            if os.path.exists(base + '-banner' + ext):
                fanart_path = base + '-banner' + ext
                break
    if not fanart_path:
        for ext in fanart_extensions:
            if os.path.exists(os.path.join(os.path.dirname(filepath), 'fanart' + ext)):
                fanart_path = os.path.join(os.path.dirname(filepath), 'fanart' + ext)
                break
    if not fanart_path:
        for ext in fanart_extensions:
            if os.path.exists(os.path.join(os.path.dirname(filepath), 'banner' + ext)):
                fanart_path = os.path.join(os.path.dirname(filepath), 'banner' + ext)
                break
    
    poster_url = None
    if poster_path:
        poster_url = f'/api/image?path={os.path.abspath(poster_path)}'
    
    fanart_url = None
    if fanart_path:
        fanart_url = f'/api/image?path={os.path.abspath(fanart_path)}'
    
    return {
        'name': os.path.basename(filepath),
        'dir': os.path.dirname(filepath),
        'hasNfo': os.path.exists(nfo_path),
        'hasVsmeta': os.path.exists(vsmeta_path),
        'hasPoster': poster_path is not None,
        'hasFanart': fanart_path is not None,
        'nfoContent': nfo_content,
        'vsmetaContent': vsmeta_content,
        'metadata': metadata,
        'posterUrl': poster_url,
        'fanartUrl': fanart_url
    }


def parse_nfo_metadata(nfo_path):
    if not os.path.exists(nfo_path):
        return None
    try:
        with open(nfo_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        root = ET.fromstring(content)
        metadata = {
            'title': '',
            'year': '',
            'rating': '',
            'plot': ''
        }
        
        for child in root:
            if child.tag == 'title' and child.text:
                metadata['title'] = child.text
            elif child.tag == 'year' and child.text:
                metadata['year'] = child.text
            elif child.tag == 'rating' and child.text:
                metadata['rating'] = child.text
            elif child.tag == 'plot' and child.text:
                metadata['plot'] = child.text
        
        return metadata
    except Exception:
        return None


def main():
    if not HAS_FLASK:
        print('请先安装 Flask：pip install flask')
        return
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8004, help='端口号')
    args = parser.parse_args()
    
    print(f'''
╔══════════════════════════════════════════╗
║   NFO 转 VSMETA 转换器 Web UI        ║
╠══════════════════════════════════════════╣
║   访问地址: http://localhost:{args.port:<5}    ║
╚══════════════════════════════════════════╝
    ''')
    
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()
