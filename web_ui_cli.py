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
        
        .header {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo { font-size: 1.25rem; font-weight: 700; }
        
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
        
        .page { display: none; padding: 1.5rem 2rem; }
        .page.active { display: block; }
        
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
        
        .input {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg2);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 6px;
            margin-top: 0.5rem;
        }
        
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
        
        .two-col {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 1.5rem;
        }
        @media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
        
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
            flex-wrap: wrap;
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
        
        .image-container {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1rem;
            text-align: center;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .image-container img {
            max-width: 100%;
            max-height: 500px;
            border-radius: 4px;
            object-fit: contain;
        }
        .image-placeholder {
            color: var(--text2);
            font-size: 1.1rem;
        }
        
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
        
        .alert {
            background: var(--bg2);
            border: 1px solid var(--warning);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            color: var(--warning);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎬 NFO to VSMETA Converter</div>
        <button class="btn" onclick="toggleTheme()">🌙 Theme</button>
    </div>
    
    <div class="nav">
        <button class="nav-btn active" onclick="showPage('dashboard')">📊 Dashboard</button>
        <button class="nav-btn" onclick="showPage('files')">📁 Files</button>
        <button class="nav-btn" onclick="showPage('convert')">🚀 Convert</button>
        <button class="nav-btn" onclick="showPage('logs')">📋 Logs</button>
    </div>
    
    <div class="page active" id="page-dashboard">
        <h2 style="margin-bottom: 1rem;">Status</h2>
        <div class="grid">
            <div class="card">
                <div class="stat-label">Total Files</div>
                <div class="stat-value" id="stat-total">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Converted</div>
                <div class="stat-value" style="color: var(--success);" id="stat-success">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Pending</div>
                <div class="stat-value" style="color: var(--warning);" id="stat-pending">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Failed</div>
                <div class="stat-value" style="color: var(--danger);" id="stat-failed">0</div>
            </div>
        </div>
        <div class="card">
            <h3 style="margin-bottom: 0.5rem;">Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
            </div>
            <div id="progress-text" style="margin-top: 0.75rem; color: var(--text2);">Waiting...</div>
        </div>
    </div>
    
    <div class="page" id="page-files">
        <h2 style="margin-bottom: 1rem;">Files</h2>
        <div style="margin-bottom: 1rem;">
            <label style="color: var(--text2);">Directory</label>
            <input type="text" class="input" id="config-dir" value="/workspace/test_movies" placeholder="/path/to/movies">
            <div style="margin-top: 1rem;">
                <button class="btn btn-primary" onclick="refreshFiles()">🔄 Scan Files</button>
            </div>
        </div>
        
        <div class="two-col">
            <div>
                <h3 style="margin-bottom: 0.75rem;">File List</h3>
                <div class="tree" id="file-tree">
                    <div style="color: var(--text2); padding: 1rem; text-align: center;">Click "Scan Files" to load files</div>
                </div>
            </div>
            
            <div>
                <h3 style="margin-bottom: 0.75rem;">File Details</h3>
                <div class="detail">
                    <div class="detail-tabs">
                        <button class="detail-tab active" onclick="showDetail('overview')">📋 Overview</button>
                        <button class="detail-tab" onclick="showDetail('nfo')">📄 NFO</button>
                        <button class="detail-tab" onclick="showDetail('vsmeta')">📝 VSMETA</button>
                        <button class="detail-tab" onclick="showDetail('compare')">🔄 Compare</button>
                        <button class="detail-tab" onclick="showDetail('poster')">🖼️ Poster</button>
                        <button class="detail-tab" onclick="showDetail('fanart')">🎬 Fanart</button>
                    </div>
                    
                    <div class="detail-content active" id="detail-overview">
                        <div id="overview-empty" style="color: var(--text2); padding: 2rem; text-align: center;">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem;">👈</div>
                            <div>Select a file from the list to view details</div>
                        </div>
                        <div id="overview-content"></div>
                    </div>
                    
                    <div class="detail-content" id="detail-nfo">
                        <div id="nfo-content" class="code">No NFO content</div>
                    </div>
                    
                    <div class="detail-content" id="detail-vsmeta">
                        <div id="vsmeta-content" class="code">No VSMETA content</div>
                    </div>
                    
                    <div class="detail-content" id="detail-compare">
                        <div class="compare">
                            <div>
                                <h4 style="margin-bottom: 0.5rem;">NFO Content</h4>
                                <div id="compare-nfo" class="code">No content</div>
                            </div>
                            <div>
                                <h4 style="margin-bottom: 0.5rem;">VSMETA Content</h4>
                                <div id="compare-vsmeta" class="code">No content</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-content" id="detail-poster">
                        <h4 style="margin-bottom: 0.5rem;">Poster Image</h4>
                        <div class="image-container" id="poster-container">
                            <div class="image-placeholder">Select a file first</div>
                        </div>
                    </div>
                    
                    <div class="detail-content" id="detail-fanart">
                        <h4 style="margin-bottom: 0.5rem;">Fanart Image</h4>
                        <div class="image-container" id="fanart-container">
                            <div class="image-placeholder">Select a file first</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="page" id="page-convert">
        <h2 style="margin-bottom: 1rem;">🚀 Convert</h2>
        
        <div class="alert">
            ⚠️ This version uses subprocess to call the converter, stable and reliable!
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 1rem;">Settings</h3>
            <div style="margin-bottom: 1rem;">
                <label style="color: var(--text2);">Directory</label>
                <input type="text" class="input" id="convert-dir" value="/workspace/test_movies">
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <label style="color: var(--text2);">Workers</label>
                    <input type="number" class="input" id="workers" value="4">
                </div>
                <div>
                    <label style="color: var(--text2);">Options</label>
                    <div style="margin-top: 0.75rem;">
                        <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                            <input type="checkbox" id="overwrite"> Overwrite existing VSMETA
                        </label>
                    </div>
                </div>
            </div>
            <div>
                <button class="btn btn-primary" id="btn-start" onclick="startConversion()">▶️ Start Convert</button>
                <button class="btn btn-danger" id="btn-stop" onclick="stopConversion()" style="display:none;">⏹️ Stop Convert</button>
            </div>
        </div>
    </div>
    
    <div class="page" id="page-logs">
        <h2 style="margin-bottom: 1rem;">Logs</h2>
        <div style="margin-bottom: 1rem;">
            <button class="btn" onclick="refreshLogs()">🔄 Refresh</button>
            <button class="btn" onclick="clearLogs()">🗑️ Clear</button>
        </div>
        <div class="log-box" id="log-box">No logs</div>
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
        
        function renderFileTree() {
            const container = document.getElementById('file-tree');
            
            if (!scanResults.length) {
                container.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text2);">No video files found<br><br>Supported formats: .mp4, .mkv, .avi, .ts, .mov</div>';
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
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            const el = document.getElementById('file-' + index);
            if (el) el.classList.add('selected');
            
            const file = scanResults[index];
            renderFileDetail(file);
        }
        
        async function renderFileDetail(file) {
            try {
                const data = await api('/api/file-detail?path=' + encodeURIComponent(file.path));
                
                document.getElementById('overview-empty').style.display = 'none';
                document.getElementById('overview-content').innerHTML = `
                    <div style="display:grid; gap:1rem; grid-template-columns:repeat(2, 1fr);">
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">Filename</div>
                            <div style="font-weight:600;">${data.name || '-'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">Directory</div>
                            <div style="font-size:0.9rem; color:var(--text2);">${data.dir || '-'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">NFO</div>
                            <div>${data.hasNfo ? '<span class="badge success">✅ Present</span>' : '<span class="badge danger">❌ Missing</span>'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">VSMETA</div>
                            <div>${data.hasVsmeta ? '<span class="badge success">✅ Present</span>' : '<span class="badge warning">⏳ Missing</span>'}</div>
                        </div>
                    </div>
                    <div style="display:grid; gap:1rem; grid-template-columns:repeat(2, 1fr); margin-top:1rem;">
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">Poster</div>
                            <div>${data.hasPoster ? '<span class="badge success">✅ Present</span>' : '<span class="badge warning">⏳ Missing</span>'}</div>
                        </div>
                        <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                            <div style="color:var(--text2); font-size:0.85rem;">Fanart</div>
                            <div>${data.hasFanart ? '<span class="badge success">✅ Present</span>' : '<span class="badge warning">⏳ Missing</span>'}</div>
                        </div>
                    </div>
                    ${data.metadata ? `
                        <div style="margin-top:1.5rem;">
                            <h4 style="margin-bottom:0.75rem;">Metadata</h4>
                            <div style="background: var(--bg); padding:1rem; border-radius:6px;">
                                <div style="margin-bottom:0.5rem;"><strong>Title:</strong> ${data.metadata.title || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>Year:</strong> ${data.metadata.year || '-'}</div>
                                <div style="margin-bottom:0.5rem;"><strong>Rating:</strong> ${data.metadata.rating || '-'}</div>
                                <div><strong>Plot:</strong> ${data.metadata.plot || '-'}</div>
                            </div>
                        </div>
                    ` : ''}
                `;
                
                document.getElementById('nfo-content').textContent = data.nfoContent || 'No NFO content';
                document.getElementById('compare-nfo').textContent = data.nfoContent || 'No NFO content';
                
                document.getElementById('vsmeta-content').textContent = data.vsmetaContent || 'No VSMETA content';
                document.getElementById('compare-vsmeta').textContent = data.vsmetaContent || 'No VSMETA content';
                
                const posterContainer = document.getElementById('poster-container');
                if (data.posterUrl) {
                    posterContainer.innerHTML = `<img src="${data.posterUrl}" alt="Poster" onclick="window.open('${data.posterUrl}', '_blank')" style="cursor: zoom-in;">`;
                } else {
                    posterContainer.innerHTML = '<div class="image-placeholder">No poster image</div>';
                }
                
                const fanartContainer = document.getElementById('fanart-container');
                if (data.fanartUrl) {
                    fanartContainer.innerHTML = `<img src="${data.fanartUrl}" alt="Fanart" onclick="window.open('${data.fanartUrl}', '_blank')" style="cursor: zoom-in;">`;
                } else {
                    fanartContainer.innerHTML = '<div class="image-placeholder">No fanart image</div>';
                }
                
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
                document.getElementById('progress-text').textContent = p.currentFile ? `Converting: ${p.currentFile} (${p.completed}/${p.total})` : 'Waiting...';
                
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
            } catch (e) {
                console.error(e);
            }
        }
        
        async function stopConversion() {
            try {
                await api('/api/convert/stop', 'POST');
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
                    container.innerHTML = '<div>No logs</div>';
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
                document.getElementById('log-box').innerHTML = '<div>No logs</div>';
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
        _add_log('info', f'Scan complete, found {len(files)} video files')
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
        _add_log('info', 'Conversion stopped')
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
        
        _add_log('info', 'Starting conversion...')
        
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
        
        _add_log('success', f'Conversion complete! Success: {_state["progress"]["success"]}, Failed: {_state["progress"]["failed"]}')
        
    except Exception as e:
        _add_log('error', f'Conversion failed: {str(e)}')
    finally:
        _state['is_running'] = False
        _state['progress']['current_file'] = ''


def scan_directory(directory):
    results = []
    if not os.path.exists(directory):
        _add_log('warning', f'Directory not found: {directory}')
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
                        status_text = 'Converted'
                    elif has_nfo:
                        status_class = 'warning'
                        status_text = 'Pending'
                    else:
                        status_class = 'danger'
                        status_text = 'No NFO'
                    
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
        _add_log('error', f'Scan failed: {e}')
    
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
        print('Please install Flask first: pip install flask')
        return
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8004, help='Port number')
    args = parser.parse_args()
    
    print(f'''
╔══════════════════════════════════════════╗
║   NFO to VSMETA Converter Web UI        ║
╠══════════════════════════════════════════╣
║   Access: http://localhost:{args.port:<5}    ║
╚══════════════════════════════════════════╝
    ''')
    
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()
