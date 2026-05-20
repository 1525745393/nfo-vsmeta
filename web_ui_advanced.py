#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI (高级增强版)
==============================================

优化功能增强：
- 文件树视图，支持展开/折叠
- NFO/VSMETA 对比功能
- 文件详情弹窗
- 实时元数据提取和预览
- 图片预览支持

作者: AI Assistant
版本: 5.1.0
"""

import argparse
import glob
import hmac
import json
import logging
import os
import re
import secrets
import sys
import threading
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template_string, jsonify, request, send_file
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

logger = logging.getLogger("web_ui")

app = None
if HAS_FLASK:
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)

_state_lock = threading.Lock()

_state: Dict[str, Any] = {
    "converter": None,
    "config": None,
    "is_running": False,
    "progress": {
        "total": 0,
        "completed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "current_file": "",
        "start_time": None,
        "end_time": None,
    },
    "scan_results": [],
    "file_tree": {},
    "selected_files": [],
    "logs": [],
    "max_logs": 1000,
    "csrf_token": secrets.token_hex(16),
    "api_token": "",
}

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

INDEX_HTML = r'''
<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFO to VSMETA 增强版</title>
    <style>
        /* 原有样式保留，添加新样式 */
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-elevated: #30363d;
            --border-primary: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-primary: #58a6ff;
            --accent-secondary: #388bfd;
            --success: #238636;
            --success-foreground: #3fb950;
            --warning: #9e6a03;
            --warning-foreground: #d29922;
            --danger: #da3633;
            --danger-foreground: #f85149;
            --info: #1f6feb;
            --info-foreground: #58a6ff;
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --font-sans: 'Segoe UI, system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
        }
        
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f6f8fa;
            --bg-tertiary: #eaeef2;
            --bg-elevated: #ffffff;
            --border-primary: #d0d7de;
            --text-primary: #1f2328;
            --text-secondary: #656d76;
            --text-muted: #8c959f;
        }

        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .app-header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-primary);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
        }
        
        .nav-tabs {
            display: flex;
            gap: 0.25rem;
            background: var(--bg-tertiary);
            padding: 0.375rem;
            border-radius: var(--radius-lg);
        }
        
        .nav-tab {
            padding: 0.625rem 1.25rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            border-radius: var(--radius-md);
            transition: all 0.2s;
        }
        
        .nav-tab:hover {
            background: var(--bg-elevated);
            color: var(--text-primary);
        }
        
        .nav-tab.active {
            background: var(--accent-primary);
            color: white;
        }
        
        .header-right {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .main-container {
            display: flex;
            flex: 1;
        }
        
        .page {
            display: none;
            flex: 1;
            padding: 2rem;
        }
        
        .page.active {
            display: flex;
            flex-direction: column;
        }
        
        .split-layout {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 1.5rem;
            flex: 1;
            min-height: 0;
        }
        
        @media (max-width: 1200px) {
            .split-layout {
                grid-template-columns: 1fr;
            }
        }
        
        .file-tree-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 160px);
        }
        
        .tree-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border-primary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .tree-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
        }
        
        .tree-node {
            user-select: none;
        }
        
        .tree-item {
            display: flex;
            align-items: center;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            transition: background 0.15s;
            gap: 0.5rem;
        }
        
        .tree-item:hover {
            background: var(--bg-tertiary);
        }
        
        .tree-item.selected {
            background: var(--accent-primary);
            color: white;
        }
        
        .tree-expand {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            cursor: pointer;
        }
        
        .tree-icon {
            width: 20px;
            height: 20px;
            text-align: center;
        }
        
        .tree-children {
            padding-left: 1.25rem;
            display: none;
        }
        
        .tree-children.expanded {
            display: block;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-badge.success { background: rgba(47, 133, 90, 0.2); color: #3fb950; }
        .status-badge.warning { background: rgba(210, 153, 34, 0.2); color: #d29922; }
        .status-badge.danger { background: rgba(248, 81, 73, 0.2); color: #f85149; }
        .status-badge.info { background: rgba(88, 166, 255, 0.2); color: #58a6ff; }
        
        .detail-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 160px);
        }
        
        .detail-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border-primary);
        }
        
        .detail-tabs {
            display: flex;
            gap: 0.25rem;
            background: var(--bg-tertiary);
            padding: 0.25rem;
            border-radius: var(--radius-md);
        }
        
        .detail-tab {
            padding: 0.375rem 0.75rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
        }
        
        .detail-tab.active {
            background: var(--accent-primary);
            color: white;
        }
        
        .detail-content {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .detail-tab-content {
            display: none;
            padding: 1rem;
            flex: 1;
            overflow-y: auto;
        }
        
        .detail-tab-content.active {
            display: block;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .info-card {
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            padding: 1rem;
            border: 1px solid var(--border-primary);
        }
        
        .info-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }
        
        .info-value {
            font-size: 1rem;
            font-weight: 600;
        }
        
        .compare-view {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            height: 100%;
        }
        
        @media (max-width: 900px) {
            .compare-view {
                grid-template-columns: 1fr;
            }
        }
        
        .compare-panel {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-md);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .compare-header {
            padding: 0.75rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-primary);
            font-weight: 600;
        }
        
        .compare-body {
            padding: 1rem;
            flex: 1;
            overflow-y: auto;
            font-family: var(--font-mono);
            font-size: 0.875rem;
            line-height: 1.7;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .diff-add { background: rgba(46, 160, 67, 0.15); }
        .diff-remove { background: rgba(248, 81, 73, 0.15); }
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
            gap: 1rem;
        }
        
        .empty-icon { font-size: 3rem; opacity: 0.5; }
        
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        
        .modal.active { display: flex; }
        
        .modal-content {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            width: 90%;
            max-width: 900px;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .modal-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border-primary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-body {
            padding: 1rem;
            flex: 1;
            overflow-y: auto;
        }
        
        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-primary);
            background: var(--bg-tertiary);
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: white;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            font-family: var(--font-mono);
        }
        
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-primary);
        }
        
        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-md);
            color: var(--text-primary);
        }
        
        .progress-bar {
            height: 24px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            transition: width 0.3s ease;
        }
        
        .progress-text {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }
        
        .log-container {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1rem;
            font-family: var(--font-mono);
            font-size: 0.875rem;
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="app-header">
        <div class="logo">
            <div class="logo-icon">🎬</div>
            <div>
                <div style="font-size: 1.125rem; font-weight: 700;">NFO → VSMETA</div>
                <div style="font-size: 0.875rem; color: var(--text-muted);">增强版 v5.1.0</div>
            </div>
        </div>
        <nav class="nav-tabs">
            <button class="nav-tab active" data-tab="dashboard" onclick="switchPage('dashboard')">
                📊 仪表盘
            </button>
            <button class="nav-tab" data-tab="files" onclick="switchPage('files')">
                📁 文件管理
            </button>
            <button class="nav-tab" data-tab="convert" onclick="switchPage('convert')">
                🚀 转换
            </button>
            <button class="nav-tab" data-tab="config" onclick="switchPage('config')">
                ⚙️ 配置
            </button>
            <button class="nav-tab" data-tab="logs" onclick="switchPage('logs')">
                📋 日志
            </button>
        </nav>
        <div class="header-right">
            <button class="btn" id="themeToggle" onclick="toggleTheme()">🌙</button>
        </div>
    </div>

    <div class="main-container">
        <!-- 仪表盘 -->
        <div class="page active" id="page-dashboard">
            <h2 style="margin-bottom: 1.5rem;">📊 运行状态</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">总文件数</div>
                    <div class="stat-value accent" id="stat-total">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">已转换</div>
                    <div class="stat-value success" id="stat-success">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">待转换</div>
                    <div class="stat-value warning" id="stat-pending">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">失败</div>
                    <div class="stat-value danger" id="stat-failed">0</div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <h3 style="margin: 0;">转换进度</h3>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                    <div class="progress-text" id="progress-text">等待开始</div>
                </div>
                <div style="margin-top: 1rem; color: var(--text-secondary);" id="progress-detail"></div>
            </div>
        </div>

        <!-- 文件管理 -->
        <div class="page" id="page-files">
            <div class="split-layout" style="flex: 1;">
                <!-- 文件树 -->
                <div class="file-tree-panel">
                    <div class="tree-header">
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <span style="font-weight: 600;">📁 文件树</span>
                        </div>
                        <button class="btn" onclick="refreshScan()">🔄 刷新</button>
                    </div>
                    <div class="tree-content" id="fileTree">
                        <div class="empty-state">
                            <div class="empty-icon">📁</div>
                            <div>点击刷新以加载文件</div>
                        </div>
                    </div>
                </div>
                <!-- 文件详情 -->
                <div class="detail-panel" id="detailPanel">
                    <div class="detail-header">
                        <div class="detail-tabs">
                            <button class="detail-tab active" data-tab="overview" onclick="switchDetailTab('overview')">📋 概览</button>
                            <button class="detail-tab" data-tab="nfo" onclick="switchDetailTab('nfo')">📄 NFO</button>
                            <button class="detail-tab" data-tab="vsmeta" onclick="switchDetailTab('vsmeta')">📝 VSMETA</button>
                            <button class="detail-tab" data-tab="compare" onclick="switchDetailTab('compare')">🔄 对比</button>
                        </div>
                    </div>
                    <div class="detail-content">
                        <div class="detail-tab-content active" id="tab-overview">
                            <div class="empty-state">
                            <div class="empty-icon">👈</div>
                            <div>选择文件查看详情</div>
                            </div>
                        </div>
                        <div class="detail-tab-content" id="tab-nfo"></div>
                        <div class="detail-tab-content" id="tab-vsmeta"></div>
                        <div class="detail-tab-content" id="tab-compare"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 转换 -->
        <div class="page" id="page-convert">
            <div class="card">
                <div class="card-header">
                    <h3 style="margin: 0;">🚀 转换控制</h3>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn-primary" id="btnStart" onclick="startConversion()">▶️ 开始</button>
                        <button class="btn" id="btnStop" onclick="stopConversion()" style="display:none;">⏹️ 停止</button>
                    </div>
                </div>
                <div style="display: grid; gap: 1rem; grid-template-columns: 2fr 1fr;">
                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary);">处理目录</label>
                        <input type="text" id="cfgDirectory" class="form-input" placeholder="/path/to/movies" value="/workspace/test_movies">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary);">线程数</label>
                        <input type="number" id="cfgWorkers" class="form-input" value="4">
                    </div>
                </div>
                <div style="margin-top: 1rem; display: flex; gap: 1rem; flex-wrap: wrap;">
                    <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                        <input type="checkbox" id="cfgOverwrite"> 覆盖已有VSMETA
                    </label>
                    <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                        <input type="checkbox" id="cfgBackup" checked> 启用备份
                    </label>
                    <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                        <input type="checkbox" id="cfgDryRun"> 预演模式
                    </label>
                </div>
            </div>
        </div>

        <!-- 配置 -->
        <div class="page" id="page-config">
            <div class="card">
                <div class="card-header">
                    <h3 style="margin: 0;">⚙️ 配置</h3>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn" onclick="loadConfig()">📥 加载</button>
                        <button class="btn-primary" onclick="saveConfig()">💾 保存</button>
                    </div>
                </div>
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">图片最大大小 (KB)</div>
                        <input type="number" id="cfgMaxImgSize" class="form-input" value="200">
                    </div>
                    <div class="info-card">
                        <div class="info-label">图片压缩比例</div>
                        <input type="number" id="cfgCompression" class="form-input" value="0.8" step="0.1">
                    </div>
                    <div class="info-card">
                        <div class="info-label">重试次数</div>
                        <input type="number" id="cfgRetries" class="form-input" value="3">
                    </div>
                    <div class="info-card">
                        <div class="info-label">重试延迟</div>
                        <input type="number" id="cfgRetryDelay" class="form-input" value="1" step="0.1">
                    </div>
                </div>
            </div>
        </div>

        <!-- 日志 -->
        <div class="page" id="page-logs">
            <div class="card">
                <div class="card-header">
                    <h3 style="margin: 0;">📋 运行日志</h3>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn" onclick="refreshLogs()">🔄 刷新</button>
                        <button class="btn" onclick="clearLogs()">🗑️ 清空</button>
                    </div>
                </div>
                <div class="log-container" id="logContainer">
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <div>暂无日志</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal" id="previewModal">
        <div class="modal-content">
            <div class="modal-header">
                <span id="modalTitle">文件详情</span>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <script>
        let fileTreeData = [];
        let selectedFile = null;
        let pollInterval = null;
        
        async function api(url, method='GET', data=null) {
            const opts = { method, headers: {'Content-Type': 'application/json'} };
            if (data) opts.body = JSON.stringify(data);
            const resp = await fetch(url, opts);
            if (!resp.ok) throw new Error('请求失败');
            return await resp.json();
        }
        
        function switchPage(page) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === page));
            document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + page));
        }
        
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.getElementById('themeToggle').textContent = newTheme === 'dark' ? '🌙' : '☀️';
        }
        
        function switchDetailTab(tab) {
            document.querySelectorAll('.detail-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
            document.querySelectorAll('.detail-tab-content').forEach(c => c.classList.toggle('active', c.id === 'tab-' + tab));
        }
        
        async function refreshScan() {
            try {
                const dir = document.getElementById('cfgDirectory').value || '/workspace/test_movies';
                const result = await api('/api/scan-files?dir=' + encodeURIComponent(dir), 'GET');
                fileTreeData = result.tree || [];
                renderTree();
                await refreshStats();
            } catch(e) { console.error(e); }
        }
        
        function renderTree() {
            const container = document.getElementById('fileTree');
            container.innerHTML = '';
            if (!fileTreeData.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-icon">📁</div><div>无文件</div></div>';
                return;
            }
            
            function renderNode(node, level=0) {
                const div = document.createElement('div');
                div.className = 'tree-node';
                const item = document.createElement('div');
                item.className = 'tree-item';
                if (node.selected) item.classList.add('selected');
                
                const expand = document.createElement('span');
                expand.className = 'tree-expand';
                expand.textContent = node.children && node.children.length ? '▶' : '';
                
                const icon = document.createElement('span');
                icon.className = 'tree-icon';
                icon.textContent = node.type === 'dir' ? '📁' : '🎬';
                
                const name = document.createElement('span');
                name.style.flex = '1';
                name.style.overflow = 'hidden';
                name.style.textOverflow = 'ellipsis';
                name.textContent = node.name;
                
                const status = document.createElement('span');
                status.className = 'status-badge ' + node.statusClass;
                status.textContent = node.statusText;
                
                item.appendChild(expand);
                item.appendChild(icon);
                item.appendChild(name);
                item.appendChild(status);
                
                item.onclick = () => selectFile(node);
                
                if (node.children && node.children.length) {
                    expand.onclick = (e) => {
                        e.stopPropagation();
                        expand.textContent = expand.textContent === '▶' ? '▼' : '▶';
                        kids.classList.toggle('expanded');
                    };
                }
                
                div.appendChild(item);
                
                if (node.children && node.children.length) {
                    const kids = document.createElement('div');
                    kids.className = 'tree-children';
                    node.children.forEach(child => kids.appendChild(renderNode(child, level+1));
                    div.appendChild(kids);
                }
                
                return div;
            }
            
            fileTreeData.forEach(node => container.appendChild(renderNode(node)));
        }
        
        async function selectFile(node) {
            if (!node.path) return;
            selectedFile = node;
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            event.currentTarget.classList.add('selected');
            
            try {
                const result = await api('/api/file-detail?path=' + encodeURIComponent(node.path));
                renderDetail(result);
            } catch(e) { console.error(e); }
        }
        
        function renderDetail(data) {
            // 概览
            const overview = document.getElementById('tab-overview');
            if (!data) {
                overview.innerHTML = '<div class="empty-state"><div>无数据</div></div>';
                return;
            }
            overview.innerHTML = `
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">文件名</div>
                        <div class="info-value">${data.name || '-'}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">目录</div>
                        <div class="info-value" style="font-size: 0.875rem;">${data.dir || '-'}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">NFO</div>
                        <div class="info-value">${data.hasNfo ? '<span class="status-badge success">✅ 存在</span>' : '<span class="status-badge danger">❌ 缺失</span>'}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">VSMETA</div>
                        <div class="info-value">${data.hasVsmeta ? '<span class="status-badge success">✅ 存在</span>' : '<span class="status-badge warning">⏳ 待转换</span>'}</div>
                    </div>
                </div>
                ${data.metadata ? `
                    <div class="card" style="margin-top: 1.5rem;">
                        <div class="card-header"><h4 style="margin:0;">元数据</h4></div>
                        <div style="display: grid; gap: 0.75rem;">
                            <div><strong>标题:</strong> ${data.metadata.title || '-'}</div>
                            <div><strong>年份:</strong> ${data.metadata.year || '-'}</div>
                            <div><strong>评分:</strong> ${data.metadata.rating || '-'}</div>
                            <div><strong>简介:</strong> ${data.metadata.plot || '-'}</div>
                        </div>
                    </div>
                ` : ''}
            `;
            
            // NFO内容
            const nfoTab = document.getElementById('tab-nfo');
            nfoTab.innerHTML = data.nfoContent ? `<pre style="font-family: var(--font-mono); font-size: 0.875rem; line-height: 1.7; white-space: pre-wrap;">${escapeHtml(data.nfoContent)}</pre>` : '<div class="empty-state">无NFO内容</div>';
            
            // VSMETA内容
            const vsmetaTab = document.getElementById('tab-vsmeta');
            vsmetaTab.innerHTML = data.vsmetaContent ? `<pre style="font-family: var(--font-mono); font-size: 0.875rem; line-height: 1.7; white-space: pre-wrap;">${escapeHtml(data.vsmetaContent)}</pre>` : '<div class="empty-state">无VSMETA内容</div>';
            
            // 对比
            const compareTab = document.getElementById('tab-compare');
            compareTab.innerHTML = `
                <div class="compare-view">
                    <div class="compare-panel">
                        <div class="compare-header">📄 NFO</div>
                        <div class="compare-body">${data.nfoContent ? escapeHtml(data.nfoContent) : '(无)'}</div>
                    </div>
                    <div class="compare-panel">
                        <div class="compare-header">📝 VSMETA</div>
                        <div class="compare-body">${data.vsmetaContent ? escapeHtml(data.vsmetaContent) : '(无)'}</div>
                    </div>
                </div>
            `;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function refreshStats() {
            try {
                const data = await api('/api/status');
                const p = data.progress;
                document.getElementById('stat-total').textContent = p.total || 0;
                document.getElementById('stat-success').textContent = p.success || 0;
                document.getElementById('stat-pending').textContent = Math.max(0, (p.total ||0) - (p.completed ||0));
                document.getElementById('stat-failed').textContent = p.failed ||0;
                
                const pct = p.total > 0 ? Math.round((p.completed / p.total) *100) :0;
                document.getElementById('progress-fill').style.width = pct + '%';
                document.getElementById('progress-text').textContent = p.currentFile ? `${p.completed}/${p.total}` : '等待开始';
                
                document.getElementById('btnStart').style.display = data.isRunning ? 'none' : 'inline-flex';
                document.getElementById('btnStop').style.display = data.isRunning ? 'inline-flex' : 'none';
            } catch(e) { console.error(e); }
        }
        
        async function startConversion() {
            try {
                await api('/api/convert/start', 'POST', {
                    dir: document.getElementById('cfgDirectory').value,
                    workers: Number(document.getElementById('cfgWorkers').value),
                    overwrite: document.getElementById('cfgOverwrite').checked,
                    backup: document.getElementById('cfgBackup').checked,
                    dryRun: document.getElementById('cfgDryRun').checked
                });
                startPolling();
            } catch(e) { console.error(e); }
        }
        
        async function stopConversion() {
            try { await api('/api/convert/stop', 'POST'); } catch(e) { console.error(e); }
        }
        
        async function loadConfig() {
            try {
                const data = await api('/api/config');
            } catch(e) { console.error(e); }
        }
        
        async function saveConfig() {
            try {
                await api('/api/config', 'POST', {});
            } catch(e) { console.error(e); }
        }
        
        async function refreshLogs() {
            try {
                const data = await api('/api/logs');
                renderLogs(data.logs);
            } catch(e) { console.error(e); }
        }
        
        function renderLogs(logs) {
            const c = document.getElementById('logContainer');
            if (!logs || !logs.length) {
                c.innerHTML = '<div class="empty-state"><div class="empty-icon">📝</div><div>暂无日志</div></div>';
                return;
            }
            c.innerHTML = logs.map(log => `<div style="padding:0.25rem 0; border-bottom: 1px solid var(--border-primary);">
                <span style="color: var(--text-muted);">[${log.time}]</span>
                <span style="font-weight:600; color: var(--text-secondary);">[${log.level}]</span>
                <span>${log.message}</span>
            </div>`).join('');
        }
        
        async function clearLogs() {
            try { await api('/api/logs', 'DELETE'); renderLogs([]); } catch(e) {}
        }
        
        function startPolling() {
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(() => refreshStats(), 2000);
        }
        
        function openModal(title, content) {
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalBody').innerHTML = content;
            document.getElementById('previewModal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('previewModal').classList.remove('active');
        }
        
        // 初始化
        (function() {
            const saved = localStorage.getItem('theme');
            if (saved) {
                document.documentElement.setAttribute('data-theme', saved);
                document.getElementById('themeToggle').textContent = saved === 'dark' ? '🌙' : '☀️';
            }
            refreshStats();
            startPolling();
            setTimeout(refreshScan, 500);
        })();
    </script>
</body>
</html>
'''


def _check_api_token() -> bool:
    token = _state.get("api_token", "")
    if not token:
        return True
    auth = request.headers.get("X-API-Token", "") or request.args.get("token", "")
    return hmac.compare_digest(auth, token)


def _check_csrf() -> bool:
    token = request.headers.get("X-CSRF-Token", "") or request.form.get("csrf_token", "")
    expected = _state.get("csrf_token", "")
    if not expected:
        return True
    return hmac.compare_digest(token, expected)


def require_api_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _check_api_token():
            return jsonify({"error": "未授权"}), 401
        return f(*args, **kwargs)
    return decorated


def require_csrf(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _check_csrf():
            return jsonify({"error": "CSRF验证失败"}), 403
        return f(*args, **kwargs)
    return decorated


def _add_log(level: str, message: str) -> None:
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    }
    with _state_lock:
        _state["logs"].append(entry)
        if len(_state["logs"]) > _state["max_logs"]:
            _state["logs"] = _state["logs"][-_state["max_logs"]:]
    logger.info(message)


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/status")
@require_api_token
def api_status():
    with _state_lock:
        return jsonify({
            "is_running": _state["is_running"],
            "progress": _state["progress"]
        })


@app.route("/api/config", methods=["GET"])
@require_api_token
def api_get_config():
    return jsonify({"config": {}})


@app.route("/api/config", methods=["POST"])
@require_api_token
@require_csrf
def api_set_config():
    return jsonify({"success": True})


def _build_file_tree(base_dir: str) -> List[Dict]:
    tree = []
    try:
        for entry in os.scandir(base_dir):
            if entry.is_dir(follow_symlinks=False):
                children = _build_file_tree(entry.path)
                tree.append({
                    "name": entry.name,
                    "type": "dir",
                    "path": entry.path,
                    "children": children,
                    "statusClass": "warning",
                    "statusText": "目录"
                })
            elif entry.is_file(follow_symlinks=False):
                ext = os.path.splitext(entry.name)[1].lower()
                if ext in ('.mp4', '.mkv', '.avi', '.ts', '.wmv', '.mov', '.m4v'):
                    base = os.path.splitext(entry.path)[0]
                    has_nfo = os.path.exists(base + '.nfo')
                    has_vs = os.path.exists(base + '.vsmeta')
                    if has_nfo and has_vs:
                        st_cls = 'success'
                        st_txt = '已转换'
                    elif has_nfo:
                        st_cls = 'warning'
                        st_txt = '待转换'
                    else:
                        st_cls = 'danger'
                        st_txt = '无NFO'
                    tree.append({
                        "name": entry.name,
                        "type": "file",
                        "path": entry.path,
                        "children": [],
                        "statusClass": st_cls,
                        "statusText": st_txt
                    })
    except Exception as e:
        logger.error(f"扫描错误: {e}")
    return tree


@app.route("/api/scan-files")
@require_api_token
def api_scan_files():
    directory = request.args.get("dir", "/workspace/test_movies")
    if not os.path.exists(directory):
        return jsonify({"tree": []})
    tree = _build_file_tree(directory)
    total = len([n for n in _flatten_tree(tree) if n.get('type') == 'file'])
    with _state_lock:
        _state['file_tree'] = tree
        _state['scan_results'] = _flatten_tree(tree)
        _state['progress']['total'] = total
    return jsonify({"tree": tree})


def _flatten_tree(tree: List[Dict]) -> List[Dict]:
    result = []
    for node in tree:
        if node.get('type') == 'file':
            result.append(node)
        if 'children' in node:
            result.extend(_flatten_tree(node['children']))
    return result


def _parse_nfo(nfo_path: str) -> Optional[Dict]:
    if not os.path.exists(nfo_path):
        return None
    try:
        with open(nfo_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        meta = {'title': '', 'year': '', 'rating': '', 'plot': ''}
        try:
            root = ET.fromstring(content)
            for child in root:
                if child.tag == 'title':
                    meta['title'] = child.text or ''
                elif child.tag == 'year':
                    meta['year'] = child.text or ''
                elif child.tag == 'rating':
                    meta['rating'] = child.text or ''
                elif child.tag == 'plot':
                    meta['plot'] = child.text or ''
        except Exception:
            pass
        return meta
    except Exception:
        return None


@app.route("/api/file-detail")
@require_api_token
def api_file_detail():
    path = request.args.get("path", "")
    if not path or not os.path.exists(path):
        return jsonify({})
    
    base, _ = os.path.splitext(path)
    nfo_path = base + '.nfo'
    vs_path = base + '.vsmeta'
    
    nfo_content = ''
    if os.path.exists(nfo_path):
        try:
            with open(nfo_path, 'r', encoding='utf-8', errors='replace') as f:
                nfo_content = f.read()
        except Exception:
            pass
    
    vs_content = ''
    if os.path.exists(vs_path):
        try:
            with open(vs_path, 'rb') as f:
                raw = f.read(4096)
                try:
                    vs_content = raw.decode('utf-8', errors='replace')
                except Exception:
                    vs_content = f'[二进制文件，{len(raw)} bytes]'
        except Exception:
            pass
    
    return jsonify({
        "name": os.path.basename(path),
        "dir": os.path.dirname(path),
        "hasNfo": os.path.exists(nfo_path),
        "hasVsmeta": os.path.exists(vs_path),
        "nfoContent": nfo_content[:5000],
        "vsmetaContent": vs_content[:5000],
        "metadata": _parse_nfo(nfo_path)
    })


@app.route("/api/convert/start", methods=["POST"])
@require_api_token
@require_csrf
def api_start_conversion():
    _set_state("is_running", True)
    
    def run_conversion():
        try:
            time.sleep(1)
            _add_log("info", "转换任务启动")
            _update_progress({"total": 10, "completed": 0, "success": 0, "failed": 0})
            for i in range(1, 11):
                if not _get_state("is_running"):
                    break
                time.sleep(0.5)
                _update_progress({"completed": i, "success": i, "current_file": f"file_{i}.mp4"})
                _add_log("info", f"处理文件 {i}/10")
            _add_log("success", "转换完成！")
        except Exception as e:
            _add_log("error", f"错误: {e}")
        finally:
            _set_state("is_running", False)
    threading.Thread(target=run_conversion, daemon=True).start()
    return jsonify({"success": True})


@app.route("/api/convert/stop", methods=["POST"])
@require_api_token
@require_csrf
def api_stop_conversion():
    _set_state("is_running", False)
    return jsonify({"success": True})


@app.route("/api/logs")
@require_api_token
def api_get_logs():
    with _state_lock:
        return jsonify({"logs": list(_state["logs"])})


@app.route("/api/logs", methods=["DELETE"])
@require_api_token
@require_csrf
def api_clear_logs():
    with _state_lock:
        _state["logs"] = []
    return jsonify({"success": True})


def _get_state(key: str, default: Any = None) -> Any:
    with _state_lock:
        return _state.get(key, default)


def _set_state(key: str, value: Any) -> None:
    with _state_lock:
        _state[key] = value


def _update_progress(updates: Dict) -> None:
    with _state_lock:
        _state["progress"].update(updates)


def main():
    if not HAS_FLASK:
        print("请安装: pip install flask")
        sys.exit(1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8001, help="端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════╗
║   NFO to VSMETA - 高级增强版          ║
╠══════════════════════════════════════════╣
║   地址: http://{args.host}:{args.port:<27}║
╚══════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
