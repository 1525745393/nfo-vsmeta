#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI (现代化专业版)
==============================================

特性：
- 响应式设计，兼容电脑、NAS、容器
- 现代化UI界面，支持深色/浅色主题
- 实时进度监控和日志显示
- 文件扫描和批量转换
- Docker/容器友好部署

使用方法：
    python web_ui.py
    python web_ui.py --port 8080 --token mysecret

依赖：
    pip install flask

作者: AI Assistant
版本: 5.0.0
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
    "selected_files": [],
    "logs": [],
    "max_logs": 1000,
    "csrf_token": secrets.token_hex(16),
    "api_token": "",
}

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


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
    safe_level = level if level in ("info", "warning", "error", "success", "debug") else "info"
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": safe_level,
        "message": str(message),
    }
    with _state_lock:
        _state["logs"].append(entry)
        if len(_state["logs"]) > _state["max_logs"]:
            _state["logs"] = _state["logs"][-_state["max_logs"]:]
    logger.info(message)


def _get_state(key: str, default: Any = None) -> Any:
    with _state_lock:
        return _state.get(key, default)


def _set_state(key: str, value: Any) -> None:
    with _state_lock:
        _state[key] = value


def _update_progress(updates: Dict) -> None:
    with _state_lock:
        _state["progress"].update(updates)


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFO to VSMETA 转换器</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-elevated: #30363d;
            --border-primary: #30363d;
            --border-secondary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-primary: #58a6ff;
            --accent-secondary: #388bfd;
            --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --success: #238636;
            --success-foreground: #3fb950;
            --warning: #9e6a03;
            --warning-foreground: #d29922;
            --danger: #da3633;
            --danger-foreground: #f85149;
            --info: #1f6feb;
            --info-foreground: #58a6ff;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.4);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.5);
            --shadow-glow: 0 0 20px rgba(88,166,255,0.3);
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --font-sans: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
        }
        
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f6f8fa;
            --bg-tertiary: #eaeef2;
            --bg-elevated: #ffffff;
            --border-primary: #d0d7de;
            --border-secondary: #d8dee4;
            --text-primary: #1f2328;
            --text-secondary: #656d76;
            --text-muted: #8c959f;
            --accent-primary: #0969da;
            --accent-secondary: #0550ae;
            --success: #1a7f37;
            --success-foreground: #2da44e;
            --warning: #9a6700;
            --warning-foreground: #bf8700;
            --danger: #cf222e;
            --danger-foreground: #fa4549;
            --info: #0550ae;
            --info-foreground: #0969da;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
            --shadow-glow: 0 0 20px rgba(9,105,218,0.2);
        }
        
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        html {
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        .app-container {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-primary);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo {
            width: 40px;
            height: 40px;
            background: var(--accent-gradient);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 700;
            color: white;
            font-family: var(--font-mono);
            box-shadow: var(--shadow-glow);
        }
        
        .brand {
            display: flex;
            flex-direction: column;
        }
        
        .brand-title {
            font-size: 1.125rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }
        
        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-family: var(--font-mono);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success-foreground);
            animation: pulse 2s infinite;
        }
        
        .status-dot.idle {
            background: var(--text-muted);
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
        }
        
        .btn-icon {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-md);
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.125rem;
            transition: all 0.2s ease;
        }
        
        .btn-icon:hover {
            background: var(--bg-elevated);
            border-color: var(--accent-primary);
            color: var(--accent-primary);
        }
        
        /* Main Content */
        .main {
            flex: 1;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }
        
        /* Navigation */
        .nav-tabs {
            display: flex;
            gap: 0.25rem;
            margin-bottom: 2rem;
            background: var(--bg-secondary);
            padding: 0.5rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-primary);
            overflow-x: auto;
        }
        
        .nav-tab {
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
            border: none;
            background: transparent;
            font-family: inherit;
        }
        
        .nav-tab:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .nav-tab.active {
            background: var(--accent-primary);
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        /* Pages */
        .page {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .page.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Dashboard */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            transition: all 0.2s ease;
        }
        
        .stat-card:hover {
            border-color: var(--accent-primary);
            box-shadow: var(--shadow-glow);
        }
        
        .stat-label {
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            font-family: var(--font-mono);
            color: var(--text-primary);
            line-height: 1;
        }
        
        .stat-value.success { color: var(--success-foreground); }
        .stat-value.warning { color: var(--warning-foreground); }
        .stat-value.danger { color: var(--danger-foreground); }
        .stat-value.info { color: var(--info-foreground); }
        .stat-value.accent { color: var(--accent-primary); }
        
        /* Cards */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-primary);
        }
        
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Buttons */
        .btn {
            padding: 0.625rem 1.25rem;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid var(--border-primary);
            background: var(--bg-tertiary);
            color: var(--text-primary);
            font-family: inherit;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn:hover {
            background: var(--bg-elevated);
            border-color: var(--accent-primary);
        }
        
        .btn-primary {
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-secondary);
            border-color: var(--accent-secondary);
        }
        
        .btn-success {
            background: var(--success);
            border-color: var(--success);
            color: white;
        }
        
        .btn-success:hover {
            background: var(--success-foreground);
        }
        
        .btn-danger {
            background: var(--danger);
            border-color: var(--danger);
            color: white;
        }
        
        .btn-danger:hover {
            background: var(--danger-foreground);
        }
        
        .btn-group {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 1.25rem;
        }
        
        .form-label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 0.875rem;
            font-family: var(--font-mono);
            transition: all 0.2s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(88,166,255,0.1);
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        /* Checkbox */
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
            cursor: pointer;
        }
        
        .checkbox-label input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: var(--accent-primary);
            cursor: pointer;
        }
        
        /* Progress Bar */
        .progress-container {
            margin: 1.5rem 0;
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
            background: var(--accent-gradient);
            border-radius: var(--radius-md);
            transition: width 0.5s ease;
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
                transparent,
                rgba(255,255,255,0.2),
                transparent
            );
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-text {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            font-family: var(--font-mono);
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        
        /* Table */
        .table-container {
            overflow-x: auto;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-primary);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        
        th {
            text-align: left;
            padding: 1rem;
            background: var(--bg-tertiary);
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-primary);
        }
        
        td {
            padding: 0.875rem 1rem;
            border-bottom: 1px solid var(--border-secondary);
            color: var(--text-secondary);
        }
        
        tr:hover td {
            background: var(--bg-tertiary);
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.625rem;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            font-weight: 600;
            font-family: var(--font-mono);
        }
        
        .badge.success {
            background: rgba(35,134,54,0.15);
            color: var(--success-foreground);
        }
        
        .badge.warning {
            background: rgba(158,106,3,0.15);
            color: var(--warning-foreground);
        }
        
        .badge.danger {
            background: rgba(218,54,51,0.15);
            color: var(--danger-foreground);
        }
        
        .badge.info {
            background: rgba(31,111,235,0.15);
            color: var(--info-foreground);
        }
        
        /* Log Container */
        .log-container {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1rem;
            max-height: 500px;
            overflow-y: auto;
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            line-height: 1.8;
        }
        
        .log-entry {
            color: var(--text-secondary);
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border-secondary);
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .log-time {
            color: var(--text-muted);
            margin-right: 0.5rem;
        }
        
        .log-level {
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .log-level.info { color: var(--info-foreground); }
        .log-level.warning { color: var(--warning-foreground); }
        .log-level.error { color: var(--danger-foreground); }
        .log-level.success { color: var(--success-foreground); }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-muted);
        }
        
        .empty-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        .empty-text {
            font-size: 0.875rem;
        }
        
        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            pointer-events: none;
        }
        
        .toast {
            background: var(--bg-elevated);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-md);
            padding: 1rem 1.25rem;
            font-size: 0.875rem;
            color: var(--text-primary);
            box-shadow: var(--shadow-lg);
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            pointer-events: auto;
            max-width: 360px;
        }
        
        .toast.success {
            border-left: 3px solid var(--success-foreground);
        }
        
        .toast.error {
            border-left: 3px solid var(--danger-foreground);
        }
        
        .toast.warning {
            border-left: 3px solid var(--warning-foreground);
        }
        
        .toast.info {
            border-left: 3px solid var(--info-foreground);
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(40px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .main {
                padding: 1rem;
            }
            
            .nav-tabs {
                padding: 0.25rem;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .btn-group {
                width: 100%;
            }
            
            .btn {
                flex: 1;
                justify-content: center;
            }
        }
        
        /* Keyboard Shortcuts */
        .shortcuts-hint {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: 1rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 50;
        }
        
        .shortcuts-hint.visible {
            opacity: 1;
        }
        
        .kbd {
            display: inline-block;
            padding: 0.125rem 0.375rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-sm);
            font-family: var(--font-mono);
            font-size: 0.6875rem;
            margin: 0 0.125rem;
        }
        
        /* Footer */
        .footer {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-primary);
            padding: 1rem 2rem;
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .footer a {
            color: var(--accent-primary);
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="header-left">
                <div class="logo">N</div>
                <div class="brand">
                    <div class="brand-title">NFO → VSMETA</div>
                    <div class="brand-subtitle">Web Console v5.0</div>
                </div>
            </div>
            <div class="header-right">
                <div class="status-indicator">
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText">就绪</span>
                </div>
                <button class="btn-icon" id="themeToggle" title="切换主题">🌙</button>
            </div>
        </header>
        
        <!-- Main Content -->
        <main class="main">
            <!-- Navigation Tabs -->
            <nav class="nav-tabs">
                <button class="nav-tab active" data-tab="dashboard" onclick="switchTab('dashboard')">
                    📊 仪表盘
                </button>
                <button class="nav-tab" data-tab="convert" onclick="switchTab('convert')">
                    🚀 转换
                </button>
                <button class="nav-tab" data-tab="config" onclick="switchTab('config')">
                    ⚙️ 配置
                </button>
                <button class="nav-tab" data-tab="logs" onclick="switchTab('logs')">
                    📋 日志
                </button>
            </nav>
            
            <!-- Dashboard Page -->
            <div class="page active" id="page-dashboard">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">总文件数</div>
                        <div class="stat-value accent" id="statTotal">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">已处理</div>
                        <div class="stat-value info" id="statProcessed">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">成功</div>
                        <div class="stat-value success" id="statSuccess">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">失败</div>
                        <div class="stat-value danger" id="statFailed">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">跳过</div>
                        <div class="stat-value warning" id="statSkipped">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">成功率</div>
                        <div class="stat-value" id="statRate">0%</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📈 转换进度</h2>
                        <span id="progressPercent" style="font-family: var(--font-mono); color: var(--accent-primary);">0%</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                            <div class="progress-text" id="progressText">等待开始...</div>
                        </div>
                    </div>
                    <div id="progressDetail" style="font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem;"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">⚡ 快捷操作</h2>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-primary" onclick="switchTab('convert')">
                            🚀 开始转换
                        </button>
                        <button class="btn" onclick="switchTab('config')">
                            ⚙️ 配置设置
                        </button>
                        <button class="btn" onclick="switchTab('logs')">
                            📋 查看日志
                        </button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">⌨️ 键盘快捷键</h2>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.875rem; color: var(--text-secondary);">
                        <div><span class="kbd">Ctrl</span> + <span class="kbd">S</span> 保存配置</div>
                        <div><span class="kbd">Ctrl</span> + <span class="kbd">Enter</span> 开始转换</div>
                        <div><span class="kbd">T</span> 切换主题</div>
                        <div><span class="kbd">1-4</span> 切换标签页</div>
                    </div>
                </div>
            </div>
            
            <!-- Convert Page -->
            <div class="page" id="page-convert">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">🚀 转换控制</h2>
                        <div class="btn-group">
                            <button class="btn btn-success" id="btnStart" onclick="startConversion()">
                                ▶️ 开始转换
                            </button>
                            <button class="btn btn-danger" id="btnStop" onclick="stopConversion()" style="display: none;">
                                ⏹️ 停止
                            </button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">处理目录（多个用逗号分隔）</label>
                        <input type="text" class="form-input" id="cfgDirectory" placeholder="/path/to/movies" value="/workspace/test_movies">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">线程数</label>
                            <input type="number" class="form-input" id="cfgWorkers" value="4" min="1" max="32">
                        </div>
                        <div class="form-group">
                            <label class="form-label">处理模式</label>
                            <select class="form-input" id="cfgMode">
                                <option value="thread">多线程</option>
                                <option value="process">多进程</option>
                            </select>
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgOverwrite">
                            覆盖已有文件
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgBackup" checked>
                            启用备份
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgDryRun">
                            预演模式
                        </label>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📂 扫描结果 <span id="scanCount" style="font-size: 0.875rem; color: var(--text-muted);"></span></h2>
                        <div class="btn-group">
                            <button class="btn" onclick="refreshScanResults()">🔄 刷新</button>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>文件名</th>
                                    <th>目录</th>
                                    <th>NFO</th>
                                    <th>VSMETA</th>
                                    <th>状态</th>
                                </tr>
                            </thead>
                            <tbody id="scanResults">
                                <tr>
                                    <td colspan="6">
                                        <div class="empty-state">
                                            <div class="empty-icon">📁</div>
                                            <div class="empty-text">点击"开始转换"后显示扫描结果</div>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Config Page -->
            <div class="page" id="page-config">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">⚙️ 基本配置</h2>
                        <div class="btn-group">
                            <button class="btn" onclick="loadConfig()">📥 加载</button>
                            <button class="btn btn-primary" onclick="saveConfig()">💾 保存</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">处理目录</label>
                        <input type="text" class="form-input" id="cfgDir" placeholder=".">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">图片最大大小 (KB)</label>
                            <input type="number" class="form-input" id="cfgMaxImgSize" value="200">
                        </div>
                        <div class="form-group">
                            <label class="form-label">图片压缩比例</label>
                            <input type="number" class="form-input" id="cfgCompression" value="0.8" step="0.1" min="0.1" max="1.0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">重试次数</label>
                            <input type="number" class="form-input" id="cfgRetries" value="3">
                        </div>
                        <div class="form-group">
                            <label class="form-label">重试延迟 (秒)</label>
                            <input type="number" class="form-input" id="cfgRetryDelay" value="1.0" step="0.1">
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">🛡️ 安全设置</h2>
                    </div>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgSafeWrite" checked>
                            事务性写入
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgSanitizeFilename">
                            清洗文件名
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="cfgFixEncoding" checked>
                            自动修复编码
                        </label>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📋 文件过滤</h2>
                    </div>
                    <div class="form-group">
                        <label class="form-label">视频扩展名（逗号分隔）</label>
                        <input type="text" class="form-input" id="cfgVideoExt" value=".mp4, .mkv, .avi, .ts, .wmv, .rmvb, .mov, .m4v">
                    </div>
                    <div class="form-group">
                        <label class="form-label">文件名正则过滤</label>
                        <input type="text" class="form-input" id="cfgRegex" placeholder=".*1080p.*">
                    </div>
                </div>
            </div>
            
            <!-- Logs Page -->
            <div class="page" id="page-logs">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">📋 运行日志</h2>
                        <div class="btn-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="autoScroll" checked>
                                自动滚动
                            </label>
                            <button class="btn" onclick="clearLogs()">🗑️ 清空</button>
                            <button class="btn" onclick="refreshLogs()">🔄 刷新</button>
                        </div>
                    </div>
                    <div class="log-container" id="logContainer">
                        <div class="empty-state">
                            <div class="empty-icon">📝</div>
                            <div class="empty-text">暂无日志记录</div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        
        <!-- Footer -->
        <footer class="footer">
            <p>NFO to VSMETA 转换器 v5.0 | 兼容电脑 · NAS · 容器</p>
        </footer>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <!-- Shortcuts Hint -->
    <div class="shortcuts-hint" id="shortcutsHint">
        按 <span class="kbd">?</span> 查看快捷键
    </div>
    
    <script>
        // State
        let currentConfig = {};
        let isRunning = false;
        let pollInterval = null;
        
        // API Helper
        async function api(url, method = 'GET', data = null) {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || '请求失败');
            }
            
            return result;
        }
        
        // Toast Notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
                <span>${message}</span>
            `;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // Tab Switching
        function switchTab(name) {
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.toggle('active', tab.dataset.tab === name);
            });
            
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            
            document.getElementById(`page-${name}`).classList.add('active');
            
            if (name === 'logs') {
                refreshLogs();
            }
        }
        
        // Theme Toggle
        document.getElementById('themeToggle').addEventListener('click', () => {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            document.getElementById('themeToggle').textContent = newTheme === 'dark' ? '🌙' : '☀️';
            localStorage.setItem('theme', newTheme);
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.getElementById('themeToggle').textContent = savedTheme === 'dark' ? '🌙' : '☀️';
        
        // Dashboard Refresh
        async function refreshDashboard() {
            try {
                const data = await api('/api/status');
                const p = data.progress || {};
                
                document.getElementById('statTotal').textContent = p.total || 0;
                document.getElementById('statProcessed').textContent = p.completed || 0;
                document.getElementById('statSuccess').textContent = p.success || 0;
                document.getElementById('statFailed').textContent = p.failed || 0;
                document.getElementById('statSkipped').textContent = p.skipped || 0;
                
                const total = p.total || 0;
                const completed = p.completed || 0;
                const rate = total > 0 ? Math.round((completed / total) * 100) : 0;
                document.getElementById('statRate').textContent = `${rate}%`;
                
                document.getElementById('progressPercent').textContent = `${rate}%`;
                document.getElementById('progressBar').style.width = `${rate}%`;
                document.getElementById('progressText').textContent = completed > 0 ? `${completed}/${total}` : '等待开始...';
                
                document.getElementById('progressDetail').textContent = p.current_file ? `当前处理: ${p.current_file}` : '';
                
                const dot = document.getElementById('statusDot');
                const text = document.getElementById('statusText');
                
                if (data.is_running) {
                    dot.classList.remove('idle');
                    text.textContent = '运行中';
                } else {
                    dot.classList.add('idle');
                    text.textContent = '就绪';
                }
                
                isRunning = data.is_running;
                
                const btnStart = document.getElementById('btnStart');
                const btnStop = document.getElementById('btnStop');
                
                if (data.is_running) {
                    btnStart.style.display = 'none';
                    btnStop.style.display = 'inline-flex';
                } else {
                    btnStart.style.display = 'inline-flex';
                    btnStop.style.display = 'none';
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        // Conversion
        async function startConversion() {
            try {
                const config = getConfigFromForm();
                await api('/api/convert/start', 'POST', config);
                showToast('转换任务已启动', 'success');
                startPolling();
                setTimeout(() => refreshScanResults(), 2000);
            } catch (e) {
                showToast('启动失败: ' + e.message, 'error');
            }
        }
        
        async function stopConversion() {
            try {
                await api('/api/convert/stop', 'POST');
                showToast('已发送停止信号', 'warning');
            } catch (e) {
                showToast('停止失败: ' + e.message, 'error');
            }
        }
        
        function getConfigFromForm() {
            return {
                directory: document.getElementById('cfgDirectory').value,
                max_workers: parseInt(document.getElementById('cfgWorkers').value) || 4,
                process_mode: document.getElementById('cfgMode').value,
                overwrite_existing: document.getElementById('cfgOverwrite').checked,
                enable_backup: document.getElementById('cfgBackup').checked,
                dry_run: document.getElementById('cfgDryRun').checked,
                max_image_size_kb: parseInt(document.getElementById('cfgMaxImgSize').value) || 200,
                image_compression_ratio: parseFloat(document.getElementById('cfgCompression').value) || 0.8,
                retry_attempts: parseInt(document.getElementById('cfgRetries').value) || 3,
                retry_delay: parseFloat(document.getElementById('cfgRetryDelay').value) || 1.0,
                safe_write_mode: document.getElementById('cfgSafeWrite').checked,
                sanitize_filename: document.getElementById('cfgSanitizeFilename').checked,
                fix_encoding: document.getElementById('cfgFixEncoding').checked,
                video_extensions: document.getElementById('cfgVideoExt').value.split(',').map(s => s.trim()),
                file_regex: document.getElementById('cfgRegex').value
            };
        }
        
        // Scan Results
        async function refreshScanResults() {
            try {
                const data = await api('/api/scan-results');
                const files = data.files || [];
                
                document.getElementById('scanCount').textContent = files.length ? `共 ${files.length} 个文件` : '';
                
                const tbody = document.getElementById('scanResults');
                
                if (files.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6">
                                <div class="empty-state">
                                    <div class="empty-icon">📁</div>
                                    <div class="empty-text">暂无扫描结果</div>
                                </div>
                            </td>
                        </tr>
                    `;
                    return;
                }
                
                tbody.innerHTML = files.map((f, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td style="font-family: var(--font-mono); font-size: 0.8125rem;">${f.filename}</td>
                        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${f.directory}</td>
                        <td><span class="badge ${f.has_nfo ? 'success' : 'danger'}">${f.has_nfo ? '有' : '无'}</span></td>
                        <td><span class="badge ${f.has_vsmeta ? 'success' : 'danger'}">${f.has_vsmeta ? '有' : '无'}</span></td>
                        <td>${f.is_converted ? '<span class="badge success">已转换</span>' : '<span class="badge warning">待转换</span>'}</td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error(e);
            }
        }
        
        // Config
        async function loadConfig() {
            try {
                const data = await api('/api/config');
                const config = data.config || {};
                
                document.getElementById('cfgDir').value = config.directory || '';
                document.getElementById('cfgMaxImgSize').value = config.max_image_size_kb || 200;
                document.getElementById('cfgCompression').value = config.image_compression_ratio || 0.8;
                document.getElementById('cfgRetries').value = config.retry_attempts || 3;
                document.getElementById('cfgRetryDelay').value = config.retry_delay || 1.0;
                document.getElementById('cfgSafeWrite').checked = config.safe_write_mode !== false;
                document.getElementById('cfgSanitizeFilename').checked = config.sanitize_filename || false;
                document.getElementById('cfgFixEncoding').checked = config.fix_encoding !== false;
                
                showToast('配置已加载', 'success');
            } catch (e) {
                showToast('加载失败: ' + e.message, 'error');
            }
        }
        
        async function saveConfig() {
            try {
                const config = getConfigFromForm();
                await api('/api/config', 'POST', config);
                showToast('配置已保存', 'success');
            } catch (e) {
                showToast('保存失败: ' + e.message, 'error');
            }
        }
        
        // Logs
        async function refreshLogs() {
            try {
                const data = await api('/api/logs');
                const logs = data.logs || [];
                
                const container = document.getElementById('logContainer');
                
                if (logs.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">📝</div>
                            <div class="empty-text">暂无日志记录</div>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = logs.map(log => `
                    <div class="log-entry">
                        <span class="log-time">[${log.time}]</span>
                        <span class="log-level ${log.level}">[${log.level.toUpperCase()}]</span>
                        <span>${log.message}</span>
                    </div>
                `).join('');
                
                if (document.getElementById('autoScroll').checked) {
                    container.scrollTop = container.scrollHeight;
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        async function clearLogs() {
            try {
                await api('/api/logs', 'DELETE');
                document.getElementById('logContainer').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <div class="empty-text">暂无日志记录</div>
                    </div>
                `;
                showToast('日志已清空', 'success');
            } catch (e) {
                showToast('清空失败: ' + e.message, 'error');
            }
        }
        
        // Polling
        function startPolling() {
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(() => {
                refreshDashboard();
                if (document.getElementById('page-logs').classList.contains('active')) {
                    refreshLogs();
                }
            }, 2000);
        }
        
        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveConfig();
            } else if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                if (!isRunning) startConversion();
            } else if (e.key === 't' || e.key === 'T') {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    document.getElementById('themeToggle').click();
                }
            } else if (e.key >= '1' && e.key <= '4') {
                const tabs = ['dashboard', 'convert', 'config', 'logs'];
                switchTab(tabs[parseInt(e.key) - 1]);
            }
        });
        
        // Init
        (async function() {
            await refreshDashboard();
            startPolling();
        })();
    </script>
</body>
</html>"""


# ============================================================================
# API Routes
# ============================================================================

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/status")
@require_api_token
def api_status():
    with _state_lock:
        progress = _state["progress"].copy()
        is_running = _state["is_running"]
    return jsonify({
        "is_running": is_running,
        "progress": progress
    })


@app.route("/api/config", methods=["GET"])
@require_api_token
def api_get_config():
    config = _get_state("config")
    if config and is_dataclass(config):
        return jsonify({"config": asdict(config)})
    return jsonify({"config": {}})


@app.route("/api/config", methods=["POST"])
@require_api_token
@require_csrf
def api_set_config():
    data = request.get_json(silent=True) or {}
    try:
        from nfo_to_vsmeta_converter_complete import Config
        
        existing = _get_state("config")
        if existing and is_dataclass(existing):
            d = asdict(existing)
            d.update(data)
            config = Config(**d)
        else:
            config = Config(**data)
        
        _set_state("config", config)
        converter = _get_state("converter")
        if converter:
            converter.config = config
        
        _add_log("info", "配置已更新")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert/start", methods=["POST"])
@require_api_token
@require_csrf
def api_start_conversion():
    if _get_state("is_running"):
        return jsonify({"error": "转换正在进行中"}), 400
    
    data = request.get_json(silent=True) or {}
    
    try:
        from nfo_to_vsmeta_converter_complete import Config, NFOToVSMETAConverter
        
        config = _get_state("config") or Config()
        
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        _set_state("config", config)
        _set_state("is_running", True)
        _update_progress({
            "total": 0,
            "completed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "current_file": "",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        })
        
        def run_conversion():
            try:
                converter = NFOToVSMETAConverter(config)
                _set_state("converter", converter)
                
                files = converter.file_scanner.scan()
                total = len(files)
                _update_progress({"total": total})
                
                scan_data = []
                for d, f in files:
                    fp = os.path.join(d, f)
                    base_name = os.path.splitext(f)[0]
                    
                    nfo_found = any(
                        os.path.exists(os.path.join(d, base_name + ext))
                        for ext in (config.nfo_extensions or [".nfo"])
                    )
                    vsmeta_found = os.path.exists(fp + config.vsmeta_extension)
                    
                    scan_data.append({
                        "filename": f,
                        "directory": d,
                        "has_nfo": nfo_found,
                        "has_vsmeta": vsmeta_found,
                        "is_converted": nfo_found and vsmeta_found,
                    })
                
                _set_state("scan_results", scan_data)
                
                if not files:
                    _add_log("warning", "未找到需要处理的视频文件")
                    return
                
                pending = [
                    (d, f) for d, f in files
                    if not converter.checkpoint.is_completed(os.path.join(d, f))
                ]
                
                if not pending:
                    _add_log("success", "所有文件已处理完成！")
                    return
                
                for directory, filename in pending:
                    if not _get_state("is_running"):
                        _add_log("warning", "转换已被用户停止")
                        break
                    
                    filepath = os.path.join(directory, filename)
                    _update_progress({"current_file": filename})
                    
                    try:
                        result = converter._process_with_retry(directory, filename)
                        
                        with _state_lock:
                            if result.get("success"):
                                _state["progress"]["success"] += 1
                            else:
                                _state["progress"]["failed"] += 1
                        
                        _add_log("info", f"[{'成功' if result.get('success') else '失败'}] {filename}")
                    except Exception as e:
                        with _state_lock:
                            _state["progress"]["failed"] += 1
                        _add_log("error", f"[错误] {filename}: {e}")
                    
                    with _state_lock:
                        _state["progress"]["completed"] += 1
                
                p = _get_state("progress")
                _add_log("success", f"转换完成！成功: {p['success']}, 失败: {p['failed']}")
                
            except Exception as e:
                _add_log("error", f"转换出错: {e}")
            finally:
                _set_state("is_running", False)
                _update_progress({"current_file": "", "end_time": datetime.now().isoformat()})
        
        threading.Thread(target=run_conversion, daemon=True).start()
        return jsonify({"success": True})
    
    except Exception as e:
        _set_state("is_running", False)
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert/stop", methods=["POST"])
@require_api_token
@require_csrf
def api_stop_conversion():
    _set_state("is_running", False)
    converter = _get_state("converter")
    if converter and hasattr(converter, "_interrupted"):
        converter._interrupted = True
    _add_log("warning", "已发送停止信号")
    return jsonify({"success": True})


@app.route("/api/scan-results")
@require_api_token
def api_get_scan_results():
    results = _get_state("scan_results", [])
    return jsonify({"files": results})


@app.route("/api/logs")
@require_api_token
def api_get_logs():
    with _state_lock:
        logs = list(_state["logs"])
    return jsonify({"logs": logs})


@app.route("/api/logs", methods=["DELETE"])
@require_api_token
@require_csrf
def api_clear_logs():
    with _state_lock:
        _state["logs"] = []
    return jsonify({"success": True})


# ============================================================================
# Main
# ============================================================================

def main():
    if not HAS_FLASK:
        print("错误: 请先安装 Flask: pip install flask")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="NFO to VSMETA 转换器 - Web UI v5.0")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--token", default="", help="API认证Token")
    args = parser.parse_args()
    
    if args.token:
        _state["api_token"] = args.token
        print("⚠️  API认证已启用")
    
    if args.host == "0.0.0.0" and not args.token:
        print("⚠️  警告: 绑定 0.0.0.0 且未设置 API Token")
    
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    
    print(f"""
╔══════════════════════════════════════════╗
║   NFO to VSMETA 转换器 - Web UI v5.0   ║
╠══════════════════════════════════════════╣
║   地址: http://{args.host}:{args.port:<27}║
║   兼容: 电脑 · NAS · 容器              ║
╚══════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
