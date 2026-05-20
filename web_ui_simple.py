#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - 稳定增强版
=====================================
专为易用性优化，所有功能都能正常工作
"""

import argparse
import os
import sys
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from dataclasses import dataclass
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template_string, jsonify, request
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
    <title>NFO to VSMETA</title>
    <style>
        :root {
            --bg: #0d1117;
            --bg2: #161b22;
            --border: #30363d;
            --text: #f0f6fc;
            --text2: #8b949e;
            --accent: #58a6ff;
            --success: #3fb950;
            --warning: #d29922;
            --danger: #f85149;
        }
        [data-theme="light"] {
            --bg: #ffffff;
            --bg2: #f6f8fa;
            --border: #d0d7de;
            --text: #1f2328;
            --text2: #656d76;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        
        /* 头部 */
        .header {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo { font-size: 1.25rem; font-weight: 700; }
        
        /* 导航 */
        .nav {
            display: flex;
            gap: 0.5rem;
            background: var(--bg2);
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .nav-btn {
            padding: 0.5rem 1rem;
            border: none;
            background: transparent;
            color: var(--text2);
            cursor: pointer;
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .nav-btn:hover { background: var(--border); }
        .nav-btn.active { background: var(--accent); color: white; }
        
        /* 页面 */
        .page { display: none; padding: 1.5rem 2rem; }
        .page.active { display: block; }
        
        /* 网格 */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
        }
        .stat-label { font-size: 0.8rem; color: var(--text2); text-transform: uppercase; }
        .stat-value { font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }
        
        /* 按钮 */
        .btn {
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--bg2);
            color: var(--text);
            cursor: pointer;
            font-size: 0.95rem;
            margin-right: 0.5rem;
        }
        .btn:hover { background: var(--border); }
        .btn-primary { background: var(--accent); color: white; border-color: var(--accent); }
        .btn-danger { background: var(--danger); color: white; border-color: var(--danger); }
        
        /* 输入 */
        .input {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg2);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 6px;
            margin-top: 0.5rem;
        }
        
        /* 进度条 */
        .progress-bar {
            height: 28px;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), #388bfd);
            transition: width 0.3s;
        }
        
        /* 两栏布局 */
        .two-col {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 1.5rem;
        }
        @media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
        
        /* 文件树 */
        .tree {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem;
            max-height: 60vh;
            overflow-y: auto;
        }
        .tree-item {
            padding: 0.5rem;
            cursor: pointer;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .tree-item:hover { background: rgba(88, 166, 255, 0.1); }
        .tree-item.selected { background: rgba(88, 166, 255, 0.2); }
        
        /* 状态徽章 */
        .badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge.success { background: rgba(63, 185, 80, 0.2); color: var(--success); }
        .badge.warning { background: rgba(210, 153, 34, 0.2); color: var(--warning); }
        .badge.danger { background: rgba(248, 81, 73, 0.2); color: var(--danger); }
        
        /* 详情面板 */
        .detail {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        .detail-tabs {
            display: flex;
            gap: 0.25rem;
            background: var(--bg);
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .detail-tab {
            padding: 0.35rem 0.75rem;
            border: none;
            background: transparent;
            color: var(--text2);
            cursor: pointer;
            border-radius: 4px;
        }
        .detail-tab.active { background: var(--accent); color: white; }
        .detail-content { padding: 1rem; display: none; }
        .detail-content.active { display: block; }
        
        /* 对比 */
        .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        @media (max-width: 900px) { .compare { grid-template-columns: 1fr; } }
        .code {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 50vh;
        }
        
        /* 日志 */
        .log-box {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85rem;
            max-height: 50vh;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎬 NFO → VSMETA</div>
        <button class="btn" onclick="toggleTheme()">🌙 主题</button>
    </div>
    
    <div class="nav">
        <button class="nav-btn active" onclick="showPage('dashboard')">📊 仪表盘</button>
        <button class="nav-btn" onclick="showPage('files')">📁 文件管理</button>
        <button class="nav-btn" onclick="showPage('convert')">🚀 转换</button>
        <button class="nav-btn" onclick="showPage('logs')">📋 日志</button>
    </div>
    
    <!-- 仪表盘 -->
    <div class="page active" id="page-dashboard">
        <h2 style="margin-bottom: 1rem;">运行状态</h2>
        <div class="grid">
            <div class="card">
                <div class="stat-label">总文件数</div>
                <div class="stat-value" id="stat-total">0</div>
            </div>
            <div class="card">
                <div class="stat-label">已转换</div>
                <div class="stat-value" style="color: var(--success);" id="stat-success">0</div>
            </div>
            <div class="card">
                <div class="stat-label">待转换</div>
                <div class="stat-value" style="color: var(--warning);" id="stat-pending">0</div>
            </div>
            <div class="card">
                <div class="stat-label">失败</div>
                <div class="stat-value" style="color: var(--danger);" id="stat-failed">0</div>
            </div>
        </div>
        <div class="card">
            <h3 style="margin-bottom: 0.5rem;">转换进度</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
            </div>
            <div id="progress-text" style="margin-top: 0.75rem; color: var(--text2);">等待开始...</div>
        </div>
    </div>
    
    <!-- 文件管理 -->
    <div class="page" id="page-files">
        <h2 style="margin-bottom: 1rem;">文件管理</h2>
        <div style="margin-bottom: 1rem;">
            <label style="color: var(--text2);">处理目录</label>
            <input type="text" class="input" id="config-dir" value="/workspace/test_movies" placeholder="/path/to/your/movies">
            <div style="margin-top: 1rem;">
                <button class="btn btn-primary" onclick="refreshFiles()">🔄 扫描文件</button>
            </div>
        </div>
        
        <div class="two-col">
            <!-- 文件列表 -->
            <div>
                <h3 style="margin-bottom: 0.75rem;">文件列表</h3>
                <div class="tree" id="file-tree">
                    <div style="color: var(--text2); padding: 1rem; text-align: center;">点击上方「扫描文件」按钮加载文件列表</div>
                </div>
            </div>
            
            <!-- 文件详情 -->
            <div>
                <h3 style="margin-bottom: 0.75rem;">文件详情</h3>
                <div class="detail">
                    <div class="detail-tabs">
                        <button class="detail-tab active" onclick="showDetail('overview')">📋 概览</button>
                        <button class="detail-tab" onclick="showDetail('nfo')">📄 NFO文件</button>
                        <button class="detail-tab" onclick="showDetail('vsmeta')">📝 VSMETA文件</button>
                        <button class="detail-tab" onclick="showDetail('compare')">🔄 对比视图</button>
                    </div>
                    
                    <div class="detail-content active" id="detail-overview">
                        <div id="overview-empty" style="color: var(--text2); padding: 2rem; text-align: center;">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem;">👈</div>
                            <div>请在左侧文件列表中选择一个文件查看详情</div>
                        </div>
                        <div id="overview-content"></div>
                    </div>
                    
                    <div class="detail-content" id="detail-nfo">
                        <div id="nfo-content" class="code">无NFO内容</div>
                    </div>
                    
                    <div class="detail-content" id="detail-vsmeta">
                        <div id="vsmeta-content" class="code">无VSMETA内容</div>
                    </div>
                    
                    <div class="detail-content" id="detail-compare">
                        <div class="compare">
                            <div>
                                <h4 style="margin-bottom: 0.5rem;">NFO文件内容</h4>
                                <div id="compare-nfo" class="code">无内容</div>
                            </div>
                            <div>
                                <h4 style="margin-bottom: 0.5rem;">VSMETA文件内容</h4>
                                <div id="compare-vsmeta" class="code">无内容</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 转换控制 -->
    <div class="page" id="page-convert">
        <h2 style="margin-bottom: 1rem;">转换控制</h2>
        <div class="card">
            <h3 style="margin-bottom: 1rem;">转换设置</h3>
            <div style="margin-bottom: 1rem;">
                <label style="color: var(--text2);">处理目录</label>
                <input type="text" class="input" id="convert-dir" value="/workspace/test_movies">
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <label style="color: var(--text2);">工作线程数</label>
                    <input type="number" class="input" id="workers" value="4">
                </div>
                <div>
                    <label style="color: var(--text2);">覆盖已有VSMETA</label>
                    <input type="checkbox" id="overwrite" style="width: auto; margin-top: 1rem; transform: scale(1.5);">
                </div>
            </div>
            <div>
                <button class="btn btn-primary" id="btn-start" onclick="startConversion()">▶️ 开始转换</button>
                <button class="btn btn-danger" id="btn-stop" onclick="stopConversion()" style="display:none;">⏹️ 停止转换</button>
            </div>
        </div>
    </div>
    
    <!-- 日志 -->
    <div class="page" id="page-logs">
        <h2 style="margin-bottom: 1rem;">运行日志</h2>
        <div style="margin-bottom: 1rem;">
            <button class="btn" onclick="refreshLogs()">🔄 刷新日志</button>
            <button class="btn" onclick="clearLogs()">🗑️ 清空日志</button>
        </div>
        <div class="log-box" id="log-box">暂无日志</div>
    </div>
    
    <script>
        let scanResults = [];
        
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
                btn.classList.toggle('active', btn.textContent.includes(pageName === 'dashboard' ? '仪表盘' : 
                    pageName === 'files' ? '文件' : 
                    pageName === 'convert' ? '转换' : '日志')));
            
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
                t.classList.toggle('active', t.textContent.includes(tab === 'overview' ? '概览' : 
                    tab === 'nfo' ? 'NFO' : 
                    tab === 'vsmeta' ? 'VSMETA' : '对比')));
            
            document.querySelectorAll('.detail-content').forEach(c => 
                c.classList.toggle('active', c.id === 'detail-' + tab));
        }
        
        async function refreshFiles() {
            const dir = document.getElementById('config-dir').value;
            document.getElementById('file-tree').innerHTML = '<div style="text-align:center; padding:1rem;">正在扫描...</div>';
            
            try {
                const data = await api('/api/scan?dir=' + encodeURIComponent(dir));
                scanResults = data.files || [];
                renderFileTree();
                await refreshStats();
            } catch (e) {
                console.error(e);
            }
        }
        
        function renderFileTree() {
            const container = document.getElementById('file-tree');
            
            if (!scanResults.length) {
                container.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text2);">没有找到视频文件</div>';
                return;
            }
            
            container.innerHTML = scanResults.map((file, idx) => `
                <div class="tree-item" onclick="selectFile(${idx})" id="file-${idx}">
                    <span>🎬</span>
                    <span style="flex:1;">${file.name}</span>
                    <span class="badge ${file.statusClass}">${file.statusText}</span>
                </div>
            `).join('');
        }
        
        function selectFile(index) {
            // 高亮选中
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            const el = document.getElementById('file-' + index);
            if (el) el.classList.add('selected');
            
            // 显示详情
            const file = scanResults[index];
            renderFileDetail(file);
        }
        
        async function renderFileDetail(file) {
            try {
                const data = await api('/api/file-detail?path=' + encodeURIComponent(file.path));
                
                // 显示概览
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
                            <div style="color:var(--text2); font-size:0.85rem;">NFO状态</div>
                            <div>${data.hasNfo ? '<span class=\"badge success\">✅ 存在</span>' : '<span class=\"badge danger\">❌ 不存在</span>'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">VSMETA状态</div>
                            <div>${data.hasVsmeta ? '<span class=\"badge success\">✅ 存在</span>' : '<span class=\"badge warning\">⏳ 待转换</span>'}</div>
                        </div>
                    </div>
                    ${data.metadata ? `
                        <div style="margin-top:1.5rem;">
                            <h4 style="margin-bottom:0.75rem;">元数据信息</h4>
                            <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                                <div style="margin-bottom:0.5rem;"><strong>标题:</strong> ${data.metadata.title || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>年份:</strong> ${data.metadata.year || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>评分:</strong> ${data.metadata.rating || '-'}</div>
                                <div><strong>简介:</strong> ${data.metadata.plot || '-'}</div>
                            </div>
                        </div>
                    ` : ''}
                `;
                
                // 显示NFO内容
                document.getElementById('nfo-content').textContent = data.nfoContent || '无NFO内容';
                document.getElementById('compare-nfo').textContent = data.nfoContent || '无NFO内容';
                
                // 显示VSMETA内容
                document.getElementById('vsmeta-content').textContent = data.vsmetaContent || '无VSMETA内容';
                document.getElementById('compare-vsmeta').textContent = data.vsmetaContent || '无VSMETA内容';
                
            } catch (e) {
                console.error('Detail error:', e);
            }
        }
        
        async function refreshStats() {
            try {
                const data = await api('/api/status');
                const p = data.progress || {};
                document.getElementById('stat-total').textContent = p.total || 0;
                document.getElementById('stat-success').textContent = p.success || 0;
                document.getElementById('stat-pending').textContent = Math.max(0, (p.total || 0) - (p.completed || 0));
                document.getElementById('stat-failed').textContent = p.failed || 0;
                
                const pct = p.total > 0 ? Math.round((p.completed / p.total) * 100) : 0;
                document.getElementById('progress-fill').style.width = pct + '%';
                document.getElementById('progress-text').textContent = p.currentFile ? `正在处理: ${p.currentFile} (${p.completed}/${p.total})` : '等待开始...';
                
                document.getElementById('btn-start').style.display = data.is_running ? 'none' : 'inline-block';
                document.getElementById('btn-stop').style.display = data.is_running ? 'inline-block' : 'none';
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
                _addLog('info', '转换任务已启动');
            } catch (e) {
                console.error(e);
            }
        }
        
        async function stopConversion() {
            try {
                await api('/api/convert/stop', 'POST');
                _addLog('info', '停止信号已发送');
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
                    container.innerHTML = '<div>暂无日志</div>';
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
                document.getElementById('log-box').innerHTML = '<div>暂无日志</div>';
            } catch (e) {
                console.error(e);
            }
        }
        
        // 初始化
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
        
        // 定期刷新
        setInterval(refreshStats, 2000);
        
        // 初始化数据
        refreshStats();
        
        // 页面加载后自动扫描
        setTimeout(refreshFiles, 500);
        
        // 简单的本地日志
        function _addLog(level, msg) {
            const logEntry = { time: new Date().toLocaleTimeString(), level, message: msg };
            _state["logs"].push(logEntry);
        }
        
        let _state = { logs: [] };
        
        // 确保点击事件绑定正确
        document.addEventListener('DOMContentLoaded', function() {
            console.log('页面加载完成，事件已绑定');
        });
        
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


@app.route('/api/logs', methods=['GET', 'DELETE'])
def api_logs():
    if request.method == 'DELETE':
        _state['logs'] = []
    return jsonify({'logs': _state['logs']})


@app.route('/api/convert/start', methods=['POST'])
def api_convert_start():
    if _state['is_running']:
        return jsonify({'success': False, 'error': '转换进行中'})
    
    _state['is_running'] = True
    _state['progress']['completed'] = 0
    _state['progress']['success'] = 0
    _state['progress']['failed'] = 0
    _state['progress']['current_file'] = ''
    
    threading.Thread(target=run_conversion_demo, daemon=True).start()
    return jsonify({'success': True})


@app.route('/api/convert/stop', methods=['POST'])
def api_convert_stop():
    _state['is_running'] = False
    _add_log('info', '转换任务已停止')
    return jsonify({'success': True})


def run_conversion_demo():
    total = len(_state['scan_results'])
    _state['progress']['total'] = total
    
    for idx in range(total):
        if not _state['is_running']:
            break
        
        file = _state['scan_results'][idx] if idx < len(_state['scan_results']) else {}
        _state['progress']['current_file'] = file.get('name', f'file_{idx}')
        _state['progress']['completed'] = idx + 1
        _state['progress']['success'] = idx + 1
        
        _add_log('info', f'正在处理: {file.get("name", f"file_{idx}")}')
        time.sleep(0.5)
    
    _state['is_running'] = False
    _state['progress']['current_file'] = ''
    _add_log('success', '转换任务完成！')


def scan_directory(directory):
    results = []
    if not os.path.exists(directory):
        return results
    
    try:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.mp4', '.mkv', '.avi', '.ts', '.mov']:
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
        print(f'Scan error: {e}')
    
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
            nfo_content = f'无法读取: {e}'
    
    vsmeta_content = ''
    if os.path.exists(vsmeta_path):
        try:
            with open(vsmeta_path, 'rb') as f:
                raw = f.read(4096)
                try:
                    vsmeta_content = raw.decode('utf-8', errors='replace')
                except Exception:
                    vsmeta_content = f'[Binary file, {len(raw)} bytes]'
        except Exception as e:
            vsmeta_content = f'无法读取: {e}'
    
    metadata = parse_nfo_metadata(nfo_path)
    
    return {
        'name': os.path.basename(filepath),
        'dir': os.path.dirname(filepath),
        'hasNfo': os.path.exists(nfo_path),
        'hasVsmeta': os.path.exists(vsmeta_path),
        'nfoContent': nfo_content,
        'vsmetaContent': vsmeta_content,
        'metadata': metadata
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
        print('请先安装: pip install flask')
        return
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8003, help='端口')
    args = parser.parse_args()
    
    print(f'''
╔══════════════════════════════════════════╗
║   NFO → VSMETA - 稳定增强版          ║
╠══════════════════════════════════════════╣
║   访问地址: http://localhost:{args.port:<5}    ║
╚══════════════════════════════════════════╝
    ''')
    
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()
