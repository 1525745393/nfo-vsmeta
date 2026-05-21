#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI 完整功能版（修复版）
==================================================
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
    <title>NFO转VSMETA转换器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2196F3; color: white; padding: 30px; text-align: center; border-radius: 8px; margin-bottom: 20px; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav button { flex: 1; padding: 15px; border: none; background: #e0e0e0; cursor: pointer; border-radius: 5px; font-size: 16px; }
        .nav button.active { background: #2196F3; color: white; }
        .page { display: none; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .page.active { display: block; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #ddd; }
        .btn { padding: 12px 24px; border: none; background: #2196F3; color: white; cursor: pointer; border-radius: 5px; margin: 5px; }
        .btn:hover { background: #1976D2; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .file-item { padding: 12px; background: #f9f9f9; margin: 8px 0; border-radius: 5px; cursor: pointer; }
        .file-item:hover { background: #e3f2fd; }
        .badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; margin-left: 10px; }
        .success { background: #4CAF50; color: white; }
        .warning { background: #FF9800; color: white; }
        .danger { background: #f44336; color: white; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat { background: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px; }
        .stat-value { font-size: 2.5em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 NFO转VSMETA转换器</h1>
            <p>完整功能版</p>
        </div>
        
        <div class="nav">
            <button class="active" id="btn-dashboard" onclick="showPage('dashboard')">📊 仪表盘</button>
            <button id="btn-files" onclick="showPage('files')">📁 文件</button>
            <button id="btn-convert" onclick="showPage('convert')">🚀 转换</button>
            <button id="btn-logs" onclick="showPage('logs')">📋 日志</button>
        </div>
        
        <div id="page-dashboard" class="page active">
            <div class="card">
                <h2>📊 统计信息</h2>
                <div class="stats">
                    <div class="stat"><div class="stat-value" id="success-count">0</div><div>已转换</div></div>
                    <div class="stat"><div class="stat-value" id="pending-count">0</div><div>待转换</div></div>
                    <div class="stat"><div class="stat-value" id="failed-count">0</div><div>失败</div></div>
                    <div class="stat"><div class="stat-value" id="total-count">0</div><div>总数</div></div>
                </div>
            </div>
            <div class="card">
                <h2>⚡ 快捷操作</h2>
                <button class="btn" onclick="showPage('files'); refreshFiles();">📁 扫描文件</button>
                <button class="btn" onclick="showPage('convert');">🚀 开始转换</button>
                <button class="btn" onclick="showPage('logs');">📋 查看日志</button>
            </div>
        </div>
        
        <div id="page-files" class="page">
            <div class="card">
                <h2>📂 扫描目录</h2>
                <input type="text" id="scan-dir" value="/workspace/test_movies">
                <button class="btn" onclick="refreshFiles();">🔄 扫描</button>
            </div>
            <div class="card">
                <h2>📋 文件列表 (<span id="file-count">0</span>)</h2>
                <div id="file-tree"></div>
            </div>
            <div class="card">
                <h2>📄 文件详情</h2>
                <div id="file-detail"></div>
            </div>
        </div>
        
        <div id="page-convert" class="page">
            <div class="card">
                <h2>⚙️ 转换设置</h2>
                <input type="text" id="convert-dir" value="/workspace/test_movies">
                <button class="btn" id="start-btn" onclick="startConversion();">▶️ 开始转换</button>
                <button class="btn" id="stop-btn" onclick="stopConversion();" style="display:none;">⏹️ 停止</button>
            </div>
        </div>
        
        <div id="page-logs" class="page">
            <div class="card">
                <h2>📋 运行日志</h2>
                <button class="btn" onclick="refreshLogs();">🔄 刷新</button>
                <button class="btn" onclick="clearLogs();">🗑️ 清空</button>
                <div id="log-box" style="background:#1e1e1e;color:#d4d4d4;padding:15px;margin-top:15px;max-height:400px;overflow-y:auto;font-family:monospace;border-radius:5px;"></div>
            </div>
        </div>
    </div>
    
    <script>
        let files = [];
        
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
                console.error('Error:', e);
                return {};
            }
        }
        
        async function refreshFiles() {
            const dir = document.getElementById('scan-dir').value;
            document.getElementById('file-tree').innerHTML = '<p>扫描中...</p>';
            const data = await api('/api/scan?dir=' + encodeURIComponent(dir));
            files = data.files || [];
            renderFiles();
            refreshStats();
        }
        
        function renderFiles() {
            const tree = document.getElementById('file-tree');
            const count = document.getElementById('file-count');
            count.textContent = files.length;
            
            if (files.length === 0) {
                tree.innerHTML = '<p>未找到文件</p>';
                return;
            }
            
            tree.innerHTML = files.map((f, i) => 
                '<div class="file-item" onclick="showDetail(' + i + ')">' +
                '<span>🎬 ' + f.name + '</span>' +
                '<span class="badge ' + f.statusClass + '">' + f.statusText + '</span>' +
                '</div>'
            ).join('');
        }
        
        function showDetail(index) {
            const file = files[index];
            const detail = document.getElementById('file-detail');
            detail.innerHTML = 
                '<p><strong>文件名：</strong>' + file.name + '</p>' +
                '<p><strong>NFO：</strong>' + (file.hasNfo ? '✅ 存在' : '❌ 缺失') + '</p>' +
                '<p><strong>VSMETA：</strong>' + (file.hasVsmeta ? '✅ 存在' : '⏳ 缺失') + '</p>' +
                '<p><strong>目录：</strong>' + file.dir + '</p>';
        }
        
        async function refreshStats() {
            const data = await api('/api/status');
            const p = data.progress || {};
            document.getElementById('success-count').textContent = p.success || 0;
            document.getElementById('pending-count').textContent = Math.max(0, (p.total || 0) - (p.completed || 0));
            document.getElementById('failed-count').textContent = p.failed || 0;
            document.getElementById('total-count').textContent = p.total || 0;
            
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            if (startBtn) startBtn.style.display = data.is_running ? 'none' : 'inline-block';
            if (stopBtn) stopBtn.style.display = data.is_running ? 'inline-block' : 'none';
        }
        
        async function startConversion() {
            const dir = document.getElementById('convert-dir').value;
            await api('/api/convert/start', 'POST', {dir: dir});
            alert('转换已开始');
        }
        
        async function stopConversion() {
            await api('/api/convert/stop', 'POST');
        }
        
        async function refreshLogs() {
            const data = await api('/api/logs');
            const logs = data.logs || [];
            const box = document.getElementById('log-box');
            if (logs.length === 0) {
                box.innerHTML = '<p>暂无日志</p>';
                return;
            }
            box.innerHTML = logs.map(l => 
                '<div style="margin:5px 0;padding:5px;background:rgba(255,255,255,0.05);">' +
                '[' + l.time + '] <strong>[' + l.level + ']</strong> ' + l.message +
                '</div>'
            ).join('');
        }
        
        async function clearLogs() {
            await api('/api/logs', 'DELETE');
            document.getElementById('log-box').innerHTML = '<p>暂无日志</p>';
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
