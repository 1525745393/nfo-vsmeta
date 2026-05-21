#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFO to VSMETA 转换器 - Web UI 简化版
=====================================
"""

import os
import sys
import subprocess
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template_string, jsonify, request
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
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }
        .header { background: #16213e; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav button {
            padding: 15px 25px; border: none; border-radius: 8px; cursor: pointer;
            font-size: 16px; background: #0f3460; color: #fff; flex: 1;
        }
        .nav button:hover { background: #e94560; }
        .nav button.active { background: #e94560; }
        .page { display: none; padding: 20px; }
        .page.active { display: block; }
        .card { background: #16213e; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; margin: 5px; }
        .btn-primary { background: #e94560; color: #fff; }
        .btn-secondary { background: #0f3460; color: #fff; }
        .btn:hover { opacity: 0.8; }
        input { width: 100%; padding: 12px; border: 2px solid #0f3460; border-radius: 8px; background: #1a1a2e; color: #fff; margin: 5px 0; }
        .tree-item { padding: 12px; background: #0f3460; margin: 5px 0; border-radius: 8px; cursor: pointer; }
        .tree-item:hover { background: #e94560; }
        .tree-item.selected { background: #e94560; border: 2px solid #fff; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px; }
        .badge-success { background: #4ade80; color: #000; }
        .badge-warning { background: #fbbf24; color: #000; }
        .badge-danger { background: #f87171; color: #000; }
        .progress-bar { height: 30px; background: #0f3460; border-radius: 15px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #e94560, #0f3460); width: 0%; transition: width 0.5s; }
        .log-box { background: #0f3460; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 NFO转VSMETA转换器</h1>
    </div>
    
    <div class="nav">
        <button id="btn-dashboard" class="active" onclick="showPage('dashboard')">📊 仪表盘</button>
        <button id="btn-files" onclick="showPage('files')">📁 文件</button>
        <button id="btn-convert" onclick="showPage('convert')">🚀 转换</button>
        <button id="btn-logs" onclick="showPage('logs')">📋 日志</button>
    </div>
    
    <div id="page-dashboard" class="page active">
        <div class="card">
            <h2>📈 转换统计</h2>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="font-size: 32px; color: #4ade80;">0</div>
                    <div>✅ 已转换</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; color: #fbbf24;">0</div>
                    <div>⏳ 待转换</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; color: #f87171;">0</div>
                    <div>❌ 失败</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; color: #60a5fa;">0</div>
                    <div>📁 总数</div>
                </div>
            </div>
            <div class="progress-bar">
                <div id="progress-fill" class="progress-fill"></div>
            </div>
            <div id="progress-text" style="text-align: center; margin: 10px 0;">等待中...</div>
        </div>
        
        <div class="card">
            <h2>⚡ 快捷操作</h2>
            <button class="btn btn-primary" onclick="showPage('files'); refreshFiles();">📁 扫描文件</button>
            <button class="btn btn-primary" onclick="showPage('convert');">🚀 开始转换</button>
            <button class="btn btn-secondary" onclick="showPage('logs'); refreshLogs();">📋 查看日志</button>
        </div>
    </div>
    
    <div id="page-files" class="page">
        <div class="card">
            <h2>📂 选择目录</h2>
            <input type="text" id="scan-dir" value="/workspace/test_movies" placeholder="输入目录路径">
            <button class="btn btn-primary" onclick="refreshFiles()">🔄 扫描</button>
        </div>
        
        <div class="card">
            <h2>📋 文件列表 (<span id="file-count">0</span>个文件)</h2>
            <div id="file-tree" style="margin-top: 15px;">
                <div style="color: #8b949e; text-align: center; padding: 20px;">点击「扫描」加载文件</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📄 文件详情</h2>
            <div id="file-detail" style="margin-top: 15px;">
                <div style="color: #8b949e; text-align: center; padding: 20px;">👈 从列表中选择一个文件</div>
            </div>
        </div>
    </div>
    
    <div id="page-convert" class="page">
        <div class="card">
            <h2>⚙️ 转换设置</h2>
            <input type="text" id="convert-dir" value="/workspace/test_movies" placeholder="目录路径">
            <div style="margin: 15px 0;">
                <label><input type="checkbox" id="overwrite"> 覆盖已有VSMETA</label>
            </div>
            <button id="btn-start" class="btn btn-primary" onclick="startConversion()">▶️ 开始转换</button>
            <button id="btn-stop" class="btn btn-danger" style="background: #f87171; display: none;" onclick="stopConversion()">⏹️ 停止</button>
        </div>
    </div>
    
    <div id="page-logs" class="page">
        <div class="card">
            <h2>📋 运行日志</h2>
            <button class="btn btn-secondary" onclick="refreshLogs()">🔄 刷新</button>
            <button class="btn btn-secondary" onclick="clearLogs()">🗑️ 清空</button>
            <div id="log-box" class="log-box" style="margin-top: 15px;">暂无日志</div>
        </div>
    </div>
    
    <script>
        let scanResults = [];
        
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
            document.getElementById('file-tree').innerHTML = '<div style="color: #8b949e; text-align: center; padding: 20px;">正在扫描...</div>';
            
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
            const count = document.getElementById('file-count');
            
            if (!scanResults.length) {
                container.innerHTML = '<div style="color: #8b949e; text-align: center; padding: 20px;">未找到视频文件</div>';
                count.textContent = '0';
                return;
            }
            
            count.textContent = scanResults.length;
            container.innerHTML = scanResults.map((file, idx) => 
                '<div class="tree-item" onclick="selectFile(' + idx + ')" id="file-' + idx + '">' +
                    '<span>🎬 ' + file.name + '</span>' +
                    '<span class="badge badge-' + file.statusClass + '">' + file.statusText + '</span>' +
                '</div>'
            ).join('');
        }
        
        async function selectFile(index) {
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            document.getElementById('file-' + index).classList.add('selected');
            
            const file = scanResults[index];
            const data = await api('/api/file-detail?path=' + encodeURIComponent(file.path));
            
            document.getElementById('file-detail').innerHTML = 
                '<div style="background: #0f3460; padding: 15px; border-radius: 8px;">' +
                    '<p><strong>文件名：</strong>' + (data.name || '-') + '</p>' +
                    '<p><strong>NFO：</strong>' + (data.hasNfo ? '✅ 存在' : '❌ 缺失') + '</p>' +
                    '<p><strong>VSMETA：</strong>' + (data.hasVsmeta ? '✅ 存在' : '⏳ 缺失') + '</p>' +
                    '<p><strong>封面：</strong>' + (data.hasPoster ? '✅ 存在' : '⏳ 缺失') + '</p>' +
                    '<p><strong>背景图：</strong>' + (data.hasFanart ? '✅ 存在' : '⏳ 缺失') + '</p>' +
                '</div>';
        }
        
        async function refreshStats() {
            const data = await api('/api/status');
            const p = data.progress || {};
            
            const total = p.total || 0;
            const completed = p.completed || 0;
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            
            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-text').textContent = pct === 100 ? '转换完成！' : (p.currentFile || '等待中...');
            
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            if (btnStart) btnStart.style.display = data.is_running ? 'none' : 'inline-block';
            if (btnStop) btnStop.style.display = data.is_running ? 'inline-block' : 'none';
        }
        
        async function startConversion() {
            await api('/api/convert/start', 'POST', {
                dir: document.getElementById('convert-dir').value
            });
        }
        
        async function stopConversion() {
            await api('/api/convert/stop', 'POST');
        }
        
        async function refreshLogs() {
            const data = await api('/api/logs');
            const logs = data.logs || [];
            
            const container = document.getElementById('log-box');
            if (!logs.length) {
                container.innerHTML = '<div>暂无日志</div>';
                return;
            }
            
            container.innerHTML = logs.map(log => 
                '<div>[<span style="color: #8b949e;">' + log.time + '</span>] ' +
                '[<strong>' + log.level + '</strong>] ' + log.message + '</div>'
            ).join('');
        }
        
        async function clearLogs() {
            await api('/api/logs', 'DELETE');
            document.getElementById('log-box').innerHTML = '<div>暂无日志</div>';
        }
        
        setInterval(refreshStats, 2000);
        refreshStats();
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
    
    return {
        'name': os.path.basename(filepath),
        'dir': os.path.dirname(filepath),
        'hasNfo': os.path.exists(nfo_path),
        'hasVsmeta': os.path.exists(vsmeta_path),
        'hasPoster': poster_path is not None,
        'hasFanart': fanart_path is not None
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
