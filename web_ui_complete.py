#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI 完整功能版
==========================================
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


INDEX_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFO转VSMETA转换器 - 完整版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff; 
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: rgba(255,255,255,0.1); 
            backdrop-filter: blur(10px);
            padding: 25px; 
            border-radius: 15px; 
            margin-bottom: 20px; 
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .nav button {
            flex: 1;
            padding: 15px 20px; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer;
            font-size: 16px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            transition: all 0.3s;
            font-weight: 600;
        }
        .nav button:hover { 
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }
        .nav button.active { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
        }
        
        .page { display: none; }
        .page.active { display: block; }
        
        .card { 
            background: rgba(255,255,255,0.95);
            color: #333;
            padding: 25px; 
            border-radius: 15px; 
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .card h2 { 
            color: #667eea; 
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .stat-card.success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .stat-card.warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .stat-card.danger { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .stat-value { font-size: 3em; font-weight: 700; margin: 10px 0; }
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
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.5s;
            border-radius: 20px;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: 700;
            color: #667eea;
            font-size: 1.2em;
        }
        
        .btn { 
            padding: 15px 30px; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 16px;
            margin: 5px;
            transition: all 0.3s;
            font-weight: 600;
        }
        .btn-primary { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        .btn-success { 
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: #fff;
        }
        .btn-danger { 
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: #fff;
        }
        .btn-secondary { 
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        input, select { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #667eea; 
            border-radius: 10px; 
            background: rgba(102, 126, 234, 0.05);
            color: #333;
            font-size: 16px;
            margin: 10px 0;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 15px 0;
        }
        .checkbox-group input[type="checkbox"] {
            width: auto;
            transform: scale(1.5);
        }
        
        .file-list {
            max-height: 500px;
            overflow-y: auto;
            margin: 15px 0;
        }
        .file-item {
            padding: 15px;
            background: rgba(102, 126, 234, 0.05);
            margin: 8px 0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-item:hover { 
            background: rgba(102, 126, 234, 0.15);
            transform: translateX(5px);
        }
        .file-item.selected { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        
        .badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-success { background: #38ef7d; color: #000; }
        .badge-warning { background: #f093fb; color: #000; }
        .badge-danger { background: #f45c43; color: #fff; }
        
        .detail-section {
            background: rgba(102, 126, 234, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .detail-item {
            background: rgba(255,255,255,0.5);
            padding: 15px;
            border-radius: 8px;
        }
        .detail-label {
            font-size: 0.9em;
            color: #667eea;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .detail-value {
            font-size: 1.1em;
            font-weight: 700;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .tab {
            padding: 12px 24px;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab:hover {
            background: rgba(102, 126, 234, 0.2);
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
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
        
        .image-container {
            text-align: center;
            padding: 20px;
        }
        .image-container img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .log-box {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 500px;
            overflow-y: auto;
            max-height: 500px;
        }
        .log-entry {
            margin: 8px 0;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }
        .log-time { color: #667eea; margin-right: 10px; }
        .log-level { 
            padding: 2px 8px; 
            border-radius: 3px; 
            margin-right: 10px;
            font-weight: 700;
        }
        .log-level.info { background: #667eea; color: #fff; }
        .log-level.success { background: #38ef7d; color: #000; }
        .log-level.error { background: #f45c43; color: #fff; }
        .log-level.warning { background: #f093fb; color: #000; }
        
        .compare-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .compare-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 NFO转VSMETA转换器</h1>
            <p>专业级媒体文件转换工具 - 完整版</p>
        </div>
        
        <div class="nav">
            <button id="btn-dashboard" class="active" onclick="showPage('dashboard')">📊 仪表盘</button>
            <button id="btn-files" onclick="showPage('files')">📁 文件管理</button>
            <button id="btn-convert" onclick="showPage('convert')">🚀 批量转换</button>
            <button id="btn-logs" onclick="showPage('logs')">📋 运行日志</button>
        </div>
        
        <!-- 仪表盘页面 -->
        <div id="page-dashboard" class="page active">
            <div class="card">
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
                        <div class="stat-label">📁 总文件数</div>
                    </div>
                </div>
                
                <div class="progress-container">
                    <h3 style="margin-bottom: 15px; color: #667eea;">📊 转换进度</h3>
                    <div class="progress-bar">
                        <div id="progress-fill" class="progress-fill"></div>
                        <div id="progress-text" class="progress-text">0%</div>
                    </div>
                    <div id="progress-detail" style="text-align: center; margin-top: 10px; color: #667eea;">
                        0 / 0 文件
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>⚡ 快捷操作</h2>
                <button class="btn btn-primary" onclick="showPage('files'); refreshFiles();">📁 扫描文件</button>
                <button class="btn btn-success" onclick="showPage('convert');">🚀 开始转换</button>
                <button class="btn btn-secondary" onclick="showPage('logs'); refreshLogs();">📋 查看日志</button>
            </div>
        </div>
        
        <!-- 文件管理页面 -->
        <div id="page-files" class="page">
            <div class="card">
                <h2>📂 目录扫描</h2>
                <input type="text" id="scan-dir" value="/workspace/test_movies" placeholder="输入目录路径">
                <button class="btn btn-primary" onclick="refreshFiles()">🔄 扫描文件</button>
            </div>
            
            <div class="card">
                <h2>📋 文件列表 (<span id="file-count">0</span>个文件)</h2>
                <select id="filter-status" onchange="renderFileTree()" style="margin-bottom: 15px;">
                    <option value="all">全部</option>
                    <option value="converted">已转换</option>
                    <option value="pending">待转换</option>
                    <option value="no-nfo">无NFO</option>
                </select>
                <div class="file-list" id="file-tree">
                    <div style="text-align: center; padding: 40px; color: #667eea;">
                        👈 点击「扫描文件」按钮加载文件列表
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📄 文件详情</h2>
                <div id="file-detail">
                    <div style="text-align: center; padding: 40px; color: #667eea;">
                        👈 从列表中选择一个文件查看详情
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 批量转换页面 -->
        <div id="page-convert" class="page">
            <div class="card">
                <h2>⚙️ 转换设置</h2>
                <input type="text" id="convert-dir" value="/workspace/test_movies" placeholder="目录路径">
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">⚡ 工作线程数</div>
                        <input type="number" id="workers" value="4" min="1" max="16">
                    </div>
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="overwrite">
                    <label for="overwrite">覆盖已有VSMETA文件</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="recursive" checked>
                    <label for="recursive">递归扫描子目录</label>
                </div>
                
                <div style="margin-top: 20px;">
                    <button id="btn-start" class="btn btn-success" onclick="startConversion()">▶️ 开始转换</button>
                    <button id="btn-stop" class="btn btn-danger" onclick="stopConversion()" style="display: none;">⏹️ 停止转换</button>
                </div>
            </div>
        </div>
        
        <!-- 运行日志页面 -->
        <div id="page-logs" class="page">
            <div class="card">
                <h2>📋 运行日志</h2>
                <button class="btn btn-secondary" onclick="refreshLogs()">🔄 刷新</button>
                <button class="btn btn-secondary" onclick="clearLogs()">🗑️ 清空</button>
                <button class="btn btn-secondary" onclick="downloadLogs()">📥 导出</button>
                <div class="log-box" id="log-box">
                    <div style="text-align: center; padding: 40px; color: #667eea;">
                        暂无日志
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let scanResults = [];
        let selectedFile = null;
        
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
                console.error('API error:', e);
                return {};
            }
        }
        
        async function refreshFiles() {
            const dir = document.getElementById('scan-dir').value;
            const tree = document.getElementById('file-tree');
            tree.innerHTML = '<div style="text-align: center; padding: 40px; color: #667eea;">🔄 正在扫描...</div>';
            
            try {
                const data = await api('/api/scan?dir=' + encodeURIComponent(dir));
                scanResults = data.files || [];
                renderFileTree();
                await refreshStats();
            } catch (e) {
                console.error(e);
                tree.innerHTML = '<div style="text-align: center; padding: 40px; color: #f45c43;">❌ 扫描失败</div>';
            }
        }
        
        function renderFileTree() {
            const container = document.getElementById('file-tree');
            const count = document.getElementById('file-count');
            const filter = document.getElementById('filter-status').value;
            
            let filtered = scanResults;
            if (filter !== 'all') {
                filtered = scanResults.filter(file => {
                    if (filter === 'converted') return file.statusClass === 'success';
                    if (filter === 'pending') return file.statusClass === 'warning';
                    if (filter === 'no-nfo') return file.statusClass === 'danger';
                    return true;
                });
            }
            
            if (!filtered.length) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #667eea;">未找到符合条件的文件</div>';
                count.textContent = '0';
                return;
            }
            
            count.textContent = filtered.length;
            container.innerHTML = filtered.map((file, idx) => {
                const realIdx = scanResults.indexOf(file);
                return '<div class="file-item' + (selectedFile && selectedFile.path === file.path ? ' selected' : '') + '" ' +
                       'onclick="selectFile(' + realIdx + ')">' +
                       '<span>🎬 ' + file.name + '</span>' +
                       '<span class="badge badge-' + file.statusClass + '">' + file.statusText + '</span>' +
                       '</div>';
            }).join('');
        }
        
        async function selectFile(index) {
            const file = scanResults[index];
            selectedFile = file;
            renderFileTree();
            
            const data = await api('/api/file-detail?path=' + encodeURIComponent(file.path));
            showFileDetail(data);
        }
        
        function showFileDetail(data) {
            const container = document.getElementById('file-detail');
            
            let html = '<div class="detail-section">';
            html += '<div class="detail-grid">';
            html += '<div class="detail-item"><div class="detail-label">文件名</div><div class="detail-value">' + (data.name || '-') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">目录</div><div class="detail-value" style="font-size: 0.9em;">' + (data.dir || '-') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">NFO文件</div><div class="detail-value">' + (data.hasNfo ? '✅ 存在' : '❌ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">VSMETA文件</div><div class="detail-value">' + (data.hasVsmeta ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">封面图片</div><div class="detail-value">' + (data.hasPoster ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '<div class="detail-item"><div class="detail-label">背景图片</div><div class="detail-value">' + (data.hasFanart ? '✅ 存在' : '⏳ 缺失') + '</div></div>';
            html += '</div></div>';
            
            // 标签页
            html += '<div class="tabs">';
            html += '<button class="tab active" onclick="showTab(\'nfo\')">📄 NFO内容</button>';
            html += '<button class="tab" onclick="showTab(\'vsmeta\')">📝 VSMETA内容</button>';
            html += '<button class="tab" onclick="showTab(\'compare\')">🔄 对比视图</button>';
            if (data.hasPoster) html += '<button class="tab" onclick="showTab(\'poster\')">🖼️ 封面</button>';
            if (data.hasFanart) html += '<button class="tab" onclick="showTab(\'fanart\')">🎬 背景图</button>';
            html += '</div>';
            
            // NFO内容
            html += '<div id="tab-nfo" class="tab-content active">';
            html += '<div class="code-block">' + escapeHtml(data.nfoContent || '无NFO内容') + '</div>';
            html += '</div>';
            
            // VSMETA内容
            html += '<div id="tab-vsmeta" class="tab-content">';
            html += '<div class="code-block">' + escapeHtml(data.vsmetaContent || '无VSMETA内容') + '</div>';
            html += '</div>';
            
            // 对比视图
            html += '<div id="tab-compare" class="tab-content">';
            html += '<div class="compare-grid">';
            html += '<div><h4 style="color: #667eea; margin-bottom: 10px;">📄 NFO内容</h4><div class="code-block">' + escapeHtml(data.nfoContent || '无NFO内容') + '</div></div>';
            html += '<div><h4 style="color: #667eea; margin-bottom: 10px;">📝 VSMETA内容</h4><div class="code-block">' + escapeHtml(data.vsmetaContent || '无VSMETA内容') + '</div></div>';
            html += '</div></div>';
            
            // 封面
            if (data.posterUrl) {
                html += '<div id="tab-poster" class="tab-content">';
                html += '<div class="image-container"><img src="' + data.posterUrl + '" alt="封面" onclick="window.open(\'' + data.posterUrl + '\', \'_blank\')"></div>';
                html += '</div>';
            }
            
            // 背景图
            if (data.fanartUrl) {
                html += '<div id="tab-fanart" class="tab-content">';
                html += '<div class="image-container"><img src="' + data.fanartUrl + '" alt="背景图" onclick="window.open(\'' + data.fanartUrl + '\', \'_blank\')"></div>';
                html += '</div>';
            }
            
            container.innerHTML = html;
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            document.querySelectorAll('.tab').forEach(t => {
                if (t.textContent.includes(tabName === 'nfo' ? 'NFO' : tabName === 'vsmeta' ? 'VSMETA' : tabName === 'compare' ? '对比' : tabName === 'poster' ? '封面' : '背景图')) {
                    t.classList.add('active');
                }
            });
            
            document.getElementById('tab-' + tabName).classList.add('active');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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
        
        async function startConversion() {
            const dir = document.getElementById('convert-dir').value;
            const workers = parseInt(document.getElementById('workers').value) || 4;
            const overwrite = document.getElementById('overwrite').checked;
            
            await api('/api/convert/start', 'POST', {
                dir: dir,
                workers: workers,
                overwrite: overwrite
            });
            
            alert('转换已开始！');
        }
        
        async function stopConversion() {
            await api('/api/convert/stop', 'POST');
            alert('转换已停止');
        }
        
        async function refreshLogs() {
            const data = await api('/api/logs');
            const logs = data.logs || [];
            
            const container = document.getElementById('log-box');
            if (!logs.length) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #667eea;">暂无日志</div>';
                return;
            }
            
            container.innerHTML = logs.map(log => 
                '<div class="log-entry">' +
                '<span class="log-time">[' + log.time + ']</span>' +
                '<span class="log-level ' + log.level + '">' + log.level + '</span>' +
                '<span>' + log.message + '</span>' +
                '</div>'
            ).join('');
            
            container.scrollTop = container.scrollHeight;
        }
        
        async function clearLogs() {
            await api('/api/logs', 'DELETE');
            document.getElementById('log-box').innerHTML = '<div style="text-align: center; padding: 40px; color: #667eea;">暂无日志</div>';
        }
        
        function downloadLogs() {
            const logBox = document.getElementById('log-box');
            const logs = logBox.textContent;
            
            if (!logs || logs === '暂无日志') {
                alert('没有日志可导出');
                return;
            }
            
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'nfo-converter-logs-' + new Date().toISOString().slice(0,10) + '.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        setInterval(refreshStats, 2000);
        refreshStats();
        refreshLogs();
    </script>
</body>
</html>
'''


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
    import xml.etree.ElementTree as ET
    
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
        poster_url = f'/api/image/{os.path.abspath(poster_path)}'
    
    fanart_url = None
    if fanart_path:
        fanart_url = f'/api/image/{os.path.abspath(fanart_path)}'
    
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
╠══════════════════════════════════════════╣
║   访问地址: http://localhost:8004     ║
╚══════════════════════════════════════════╝
    ''')
    
    app.run(host='0.0.0.0', port=8004, debug=True)
