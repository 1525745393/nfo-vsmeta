#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取文件
with open('web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 要替换的专业模式页面的起始标记
old_pro_page_start = '''            <!-- ========== 专业模式 ========== -->
            <div class="page" id="page-pro">
                <style>
                    .pro-container{display:flex;flex-direction:column;height:calc(100vh - 120px)}
                    .pro-toolbar{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
                    .pro-toolbar-section{display:flex;gap:12px;align-items:center;flex:1;min-width:250px}
                    .pro-toolbar-section label{font-size:12px;color:var(--text-muted);margin-bottom:0}
                    .pro-toolbar-section input,.pro-toolbar-section select{padding:8px 12px;background:var(--bg-input);border:1px solid var(--border);border-radius:8px;color:var(--text-primary);font-size:13px}
                    .pro-toolbar-actions{display:flex;gap:8px}
                    .pro-main{display:grid;grid-template-columns:280px 1fr 300px;gap:12px;flex:1;min-height:0}
                    .pro-panel{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
                    .pro-panel-header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
                    .pro-panel-header h3{font-size:14px;font-weight:600;margin:0}
                    .pro-panel-content{flex:1;overflow:auto;padding:12px}
                    .file-tree-item{padding:10px 12px;border-radius:8px;cursor:pointer;margin-bottom:4px;transition:all .2s;border:2px solid transparent;display:flex;align-items:center;gap:10px}
                    .file-tree-item:hover{background:var(--bg-input)}
                    .file-tree-item.active{border-color:var(--accent);background:rgba(59,130,246,.08)}
                    .file-tree-item .status-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
                    .file-tree-item .status-dot.success{background:var(--success)}
                    .file-tree-item .status-dot.warning{background:var(--warning)}
                    .file-tree-item .status-dot.error{background:var(--danger)}
                    .file-tree-item .filename{flex:1;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
                    .file-tree-item .file-meta{font-size:11px;color:var(--text-muted)}
                    .diff-container{display:grid;grid-template-columns:1fr 1fr;gap:16px;height:100%}
                    .diff-panel{background:var(--bg-input);border:1px solid var(--border);border-radius:8px;padding:16px;overflow:auto}
                    .diff-panel-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border)}
                    .diff-panel-title{font-size:13px;font-weight:600;color:var(--text-primary)}
                    .diff-item{margin-bottom:12px;padding:10px;background:var(--bg-card);border-radius:6px}
                    .diff-item-label{font-size:11px;color:var(--text-muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
                    .diff-item-values{display:grid;grid-template-columns:1fr 1fr;gap:8px}
                    .diff-value{font-size:12px;padding:6px 8px;background:var(--bg-input);border-radius:4px;font-family:'JetBrains Mono',monospace;word-break:break-all}
                    .diff-value.original{color:var(--info)}
                    .diff-value.generated{color:var(--success)}
                    .diff-value.missing{color:var(--danger);background:rgba(239,68,68,.1)}
                    .diff-value.truncated{color:var(--warning);background:rgba(245,158,11,.1)}
                    .validation-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:500}
                    .validation-badge.pass{background:rgba(34,197,94,.15);color:var(--success)}
                    .validation-badge.fail{background:rgba(239,68,68,.15);color:var(--danger)}
                    .validation-badge.warn{background:rgba(245,158,11,.15);color:var(--warning)}
                    .log-stream{font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.8;max-height:100%;overflow-y:auto}
                    .log-entry{padding:4px 0;border-bottom:1px solid var(--border);display:flex;gap:8px;align-items:flex-start}
                    .log-entry .timestamp{color:var(--text-muted);flex-shrink:0;font-size:10px}
                    .log-entry .level{padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;flex-shrink:0}
                    .log-entry .level.info{background:rgba(59,130,246,.15);color:var(--info)}
                    .log-entry .level.warn{background:rgba(245,158,11,.15);color:var(--warning)}
                    .log-entry .level.error{background:rgba(239,68,68,.15);color:var(--danger)}
                    .log-entry .level.success{background:rgba(34,197,94,.15);color:var(--success)}
                    .log-entry .message{flex:1;word-break:break-all}
                    .log-entry.clickable{cursor:pointer}
                    .log-entry.clickable:hover{background:var(--bg-input)}
                    .stats-bar{display:flex;gap:16px;padding:8px 12px;background:var(--bg-input);border-radius:8px;font-size:12px}
                    .stat-item{display:flex;align-items:center;gap:6px}
                    .stat-item .label{color:var(--text-muted)}
                    .stat-item .value{font-weight:600;color:var(--text-primary)}
                    .stat-item .value.success{color:var(--success)}
                    .stat-item .value.error{color:var(--danger)}
                    .stat-item .value.warning{color:var(--warning)}
                    .export-btn{padding:6px 12px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);cursor:pointer;font-size:12px;transition:all .2s}
                    .export-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
                </style>
                <div class="pro-container">
                    <!-- 顶部工具栏 -->
                    <div class="pro-toolbar">
                        <div class="pro-toolbar-section">
                            <label>源目录</label>
                            <input type="text" id="proSourceDir" value="/workspace/test_movies" style="width:200px" placeholder="/path/to/nfo">
                            <label>输出目录</label>
                            <input type="text" id="proOutputDir" value="/workspace/test_movies" style="width:200px" placeholder="/path/to/vsmeta">
                        </div>
                        <div class="pro-toolbar-section">
                            <label>媒体类型</label>
                            <select id="proMediaType" style="width:120px">
                                <option value="movie">电影</option>
                                <option value="tvshow">电视剧</option>
                            </select>
                        </div>
                        <div class="pro-toolbar-section">
                            <label>冲突处理</label>
                            <select id="proConflictMode" style="width:140px">
                                <option value="skip">跳过</option>
                                <option value="overwrite">覆盖</option>
                                <option value="backup">备份旧文件</option>
                            </select>
                        </div>
                        <div class="pro-toolbar-actions">
                            <button class="btn btn-primary" id="proStartBtn" onclick="proStartConversion()">▶ 开始转换</button>
                            <button class="btn btn-danger" id="proStopBtn" onclick="proStopConversion()" style="display:none">⏹ 停止</button>
                            <button class="btn" onclick="proScanFiles()">🔍 扫描</button>
                            <button class="export-btn" onclick="proExportReport()">📥 导出报告</button>
                        </div>
                    </div>

                    <!-- 统计栏 -->
                    <div class="stats-bar" style="margin-bottom:12px">
                        <div class="stat-item">
                            <span class="label">总文件:</span>
                            <span class="value" id="proStatTotal">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">成功:</span>
                            <span class="value success" id="proStatSuccess">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">失败:</span>
                            <span class="value error" id="proStatFailed">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">跳过:</span>
                            <span class="value warning" id="proStatSkipped">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">耗时:</span>
                            <span class="value" id="proStatTime">0s</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">压缩节省:</span>
                            <span class="value" id="proStatSaved">0%</span>
                        </div>
                    </div>

                    <!-- 三栏主区域 -->
                    <div class="pro-main">
                        <!-- 左栏：文件树 -->
                        <div class="pro-panel">
                            <div class="pro-panel-header">
                                <h3>📁 文件列表</h3>
                                <span id="proFileCount" style="font-size:12px;color:var(--text-muted)">0 个文件</span>
                            </div>
                            <div class="pro-panel-content" id="proFileTree">
                                <div class="empty-state">
                                    <div class="icon">📂</div>
                                    <p>点击"扫描"加载文件</p>
                                </div>
                            </div>
                        </div>

                        <!-- 中栏：元数据对比 -->
                        <div class="pro-panel">
                            <div class="pro-panel-header">
                                <h3>🔄 元数据对比</h3>
                                <div id="proValidationStatus"></div>
                            </div>
                            <div class="pro-panel-content" id="proDiffView">
                                <div class="empty-state">
                                    <div class="icon">📊</div>
                                    <p>选择文件查看对比</p>
                                </div>
                            </div>
                        </div>

                        <!-- 右栏：实时日志 -->
                        <div class="pro-panel">
                            <div class="pro-panel-header">
                                <h3>📡 实时日志</h3>
                                <button class="export-btn" onclick="proClearLogs()" style="padding:4px 8px;font-size:11px">清除</button>
                            </div>
                            <div class="pro-panel-content">
                                <div class="log-stream" id="proLogStream">
                                    <div style="color:var(--text-muted);padding:20px;text-align:center">等待日志...</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

# 新的增强版专业模式页面
new_pro_page = '''            <!-- ========== 专业模式 ========== -->
            <div class="page" id="page-pro">
                <style>
                    .pro-container{display:flex;flex-direction:column;height:calc(100vh - 120px)}
                    .pro-toolbar{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
                    .pro-toolbar-section{display:flex;gap:12px;align-items:center;flex:1;min-width:250px}
                    .pro-toolbar-section label{font-size:12px;color:var(--text-muted);margin-bottom:0}
                    .pro-toolbar-section input,.pro-toolbar-section select{padding:8px 12px;background:var(--bg-input);border:1px solid var(--border);border-radius:8px;color:var(--text-primary);font-size:13px}
                    .pro-toolbar-actions{display:flex;gap:8px}
                    .pro-inner-tabs{display:flex;gap:8px;background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:8px;margin-bottom:12px;flex-wrap:wrap}
                    .pro-inner-tab{padding:8px 16px;border-radius:8px;cursor:pointer;transition:all .2s;font-size:13px;font-weight:500}
                    .pro-inner-tab:hover{background:var(--bg-input)}
                    .pro-inner-tab.active{background:var(--accent);color:#fff}
                    .pro-main{flex:1;min-height:0;overflow:hidden}
                    .pro-inner-page{display:none;height:100%}
                    .pro-inner-page.active{display:flex;flex-direction:column;height:100%}
                    .pro-layout-three{display:grid;grid-template-columns:280px 1fr 300px;gap:12px;flex:1;min-height:0}
                    .pro-layout-two{display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;min-height:0}
                    .pro-layout-full{flex:1;min-height:0;overflow:auto}
                    .pro-panel{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
                    .pro-panel-header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
                    .pro-panel-header h3{font-size:14px;font-weight:600;margin:0}
                    .pro-panel-content{flex:1;overflow:auto;padding:12px}
                    .file-tree-item{padding:10px 12px;border-radius:8px;cursor:pointer;margin-bottom:4px;transition:all .2s;border:2px solid transparent;display:flex;align-items:center;gap:10px}
                    .file-tree-item:hover{background:var(--bg-input)}
                    .file-tree-item.active{border-color:var(--accent);background:rgba(59,130,246,.08)}
                    .file-tree-item .status-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
                    .file-tree-item .status-dot.success{background:var(--success)}
                    .file-tree-item .status-dot.warning{background:var(--warning)}
                    .file-tree-item .status-dot.error{background:var(--danger)}
                    .file-tree-item .filename{flex:1;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
                    .file-tree-item .file-meta{font-size:11px;color:var(--text-muted)}
                    .diff-container{display:grid;grid-template-columns:1fr 1fr;gap:16px;height:100%}
                    .diff-panel{background:var(--bg-input);border:1px solid var(--border);border-radius:8px;padding:16px;overflow:auto}
                    .diff-panel-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border)}
                    .diff-panel-title{font-size:13px;font-weight:600;color:var(--text-primary)}
                    .diff-item{margin-bottom:12px;padding:10px;background:var(--bg-card);border-radius:6px}
                    .diff-item-label{font-size:11px;color:var(--text-muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
                    .diff-item-values{display:grid;grid-template-columns:1fr 1fr;gap:8px}
                    .diff-value{font-size:12px;padding:6px 8px;background:var(--bg-input);border-radius:4px;font-family:'JetBrains Mono',monospace;word-break:break-all}
                    .diff-value.original{color:var(--info)}
                    .diff-value.generated{color:var(--success)}
                    .diff-value.missing{color:var(--danger);background:rgba(239,68,68,.1)}
                    .diff-value.truncated{color:var(--warning);background:rgba(245,158,11,.1)}
                    .validation-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:500}
                    .validation-badge.pass{background:rgba(34,197,94,.15);color:var(--success)}
                    .validation-badge.fail{background:rgba(239,68,68,.15);color:var(--danger)}
                    .validation-badge.warn{background:rgba(245,158,11,.15);color:var(--warning)}
                    .log-stream{font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.8;max-height:100%;overflow-y:auto}
                    .log-entry{padding:4px 0;border-bottom:1px solid var(--border);display:flex;gap:8px;align-items:flex-start}
                    .log-entry .timestamp{color:var(--text-muted);flex-shrink:0;font-size:10px}
                    .log-entry .level{padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;flex-shrink:0}
                    .log-entry .level.info{background:rgba(59,130,246,.15);color:var(--info)}
                    .log-entry .level.warn{background:rgba(245,158,11,.15);color:var(--warning)}
                    .log-entry .level.error{background:rgba(239,68,68,.15);color:var(--danger)}
                    .log-entry .level.success{background:rgba(34,197,94,.15);color:var(--success)}
                    .log-entry .message{flex:1;word-break:break-all}
                    .log-entry.clickable{cursor:pointer}
                    .log-entry.clickable:hover{background:var(--bg-input)}
                    .stats-bar{display:flex;gap:16px;padding:8px 12px;background:var(--bg-input);border-radius:8px;font-size:12px}
                    .stat-item{display:flex;align-items:center;gap:6px}
                    .stat-item .label{color:var(--text-muted)}
                    .stat-item .value{font-weight:600;color:var(--text-primary)}
                    .stat-item .value.success{color:var(--success)}
                    .stat-item .value.error{color:var(--danger)}
                    .stat-item .value.warning{color:var(--warning)}
                    .export-btn{padding:6px 12px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);cursor:pointer;font-size:12px;transition:all .2s}
                    .export-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
                    .pro-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
                    .pro-card-header{font-size:14px;font-weight:600;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
                    .pro-compare-slider{position:relative;width:100%;aspect-ratio:16/9;background:var(--bg-input);border-radius:8px;overflow:hidden;margin-bottom:12px}
                    .pro-slider-before,.pro-slider-after{position:absolute;inset:0;background-size:cover;background-position:center}
                    .pro-slider-handle{position:absolute;top:0;bottom:0;width:4px;background:var(--accent);cursor:ew-resize;z-index:2}
                    .pro-slider-handle::before{content:'⇄';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:var(--accent);color:#fff;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 4px 12px rgba(0,0,0,.3)}
                </style>
                <div class="pro-container">
                    <!-- 顶部工具栏 -->
                    <div class="pro-toolbar">
                        <div class="pro-toolbar-section">
                            <label>源目录</label>
                            <input type="text" id="proSourceDir" value="/workspace/test_movies" style="width:200px" placeholder="/path/to/nfo">
                            <label>输出目录</label>
                            <input type="text" id="proOutputDir" value="/workspace/test_movies" style="width:200px" placeholder="/path/to/vsmeta">
                        </div>
                        <div class="pro-toolbar-section">
                            <label>媒体类型</label>
                            <select id="proMediaType" style="width:120px">
                                <option value="movie">电影</option>
                                <option value="tvshow">电视剧</option>
                            </select>
                        </div>
                        <div class="pro-toolbar-section">
                            <label>冲突处理</label>
                            <select id="proConflictMode" style="width:140px">
                                <option value="skip">跳过</option>
                                <option value="overwrite">覆盖</option>
                                <option value="backup">备份旧文件</option>
                            </select>
                        </div>
                        <div class="pro-toolbar-actions">
                            <button class="btn btn-primary" id="proStartBtn" onclick="proStartConversion()">▶ 开始转换</button>
                            <button class="btn btn-danger" id="proStopBtn" onclick="proStopConversion()" style="display:none">⏹ 停止</button>
                            <button class="btn" onclick="proScanFiles()">🔍 扫描</button>
                            <button class="export-btn" onclick="proExportReport()">📥 导出报告</button>
                        </div>
                    </div>

                    <!-- 统计栏 -->
                    <div class="stats-bar" style="margin-bottom:12px">
                        <div class="stat-item">
                            <span class="label">总文件:</span>
                            <span class="value" id="proStatTotal">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">成功:</span>
                            <span class="value success" id="proStatSuccess">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">失败:</span>
                            <span class="value error" id="proStatFailed">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">跳过:</span>
                            <span class="value warning" id="proStatSkipped">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">耗时:</span>
                            <span class="value" id="proStatTime">0s</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">压缩节省:</span>
                            <span class="value" id="proStatSaved">0%</span>
                        </div>
                    </div>

                    <!-- 内部标签页 -->
                    <div class="pro-inner-tabs">
                        <div class="pro-inner-tab active" data-pro-tab="workspace" onclick="proSwitchInnerTab('workspace')">🎯 工作区</div>
                        <div class="pro-inner-tab" data-pro-tab="config" onclick="proSwitchInnerTab('config')">⚙️ 完整配置</div>
                        <div class="pro-inner-tab" data-pro-tab="compare" onclick="proSwitchInnerTab('compare')">🎨 可视化对比</div>
                        <div class="pro-inner-tab" data-pro-tab="logs" onclick="proSwitchInnerTab('logs')">📋 日志详情</div>
                    </div>

                    <!-- 主内容区域 -->
                    <div class="pro-main">
                        <!-- 工作区页面 -->
                        <div class="pro-inner-page active" id="pro-page-workspace">
                            <div class="pro-layout-three">
                                <!-- 左栏：文件树 -->
                                <div class="pro-panel">
                                    <div class="pro-panel-header">
                                        <h3>📁 文件列表</h3>
                                        <span id="proFileCount" style="font-size:12px;color:var(--text-muted)">0 个文件</span>
                                    </div>
                                    <div class="pro-panel-content" id="proFileTree">
                                        <div class="empty-state">
                                            <div class="icon">📂</div>
                                            <p>点击"扫描"加载文件</p>
                                        </div>
                                    </div>
                                </div>

                                <!-- 中栏：元数据对比 -->
                                <div class="pro-panel">
                                    <div class="pro-panel-header">
                                        <h3>🔄 元数据对比</h3>
                                        <div id="proValidationStatus"></div>
                                    </div>
                                    <div class="pro-panel-content" id="proDiffView">
                                        <div class="empty-state">
                                            <div class="icon">📊</div>
                                            <p>选择文件查看对比</p>
                                        </div>
                                    </div>
                                </div>

                                <!-- 右栏：实时日志 -->
                                <div class="pro-panel">
                                    <div class="pro-panel-header">
                                        <h3>📡 实时日志</h3>
                                        <button class="export-btn" onclick="proClearLogs()" style="padding:4px 8px;font-size:11px">清除</button>
                                    </div>
                                    <div class="pro-panel-content">
                                        <div class="log-stream" id="proLogStream">
                                            <div style="color:var(--text-muted);padding:20px;text-align:center">等待日志...</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 完整配置页面 -->
                        <div class="pro-inner-page" id="pro-page-config">
                            <div class="pro-layout-full">
                                <div class="pro-panel" style="overflow:auto">
                                    <div class="pro-panel-header">
                                        <h3>⚙️ 完整配置</h3>
                                        <div style="display:flex;gap:8px">
                                            <button class="btn" onclick="loadConfigToPro()">📥 加载当前配置</button>
                                            <button class="btn btn-primary" onclick="saveConfigFromPro()">💾 保存配置</button>
                                        </div>
                                    </div>
                                    <div class="pro-panel-content">
                                        <div class="pro-card">
                                            <div class="pro-card-header">🎛️ 基础配置</div>
                                            <div class="form-row">
                                                <div class="form-group"><label>工作目录</label><input type="text" class="form-control" id="proCfgDir" placeholder="."></div>
                                            </div>
                                            <div class="form-row">
                                                <div class="form-group"><label>线程数</label><input type="number" class="form-control" id="proCfgThreads" value="4" min="1" max="32"></div>
                                                <div class="form-group"><label>批处理大小</label><input type="number" class="form-control" id="proCfgBatchSize" value="100" min="1"></div>
                                            </div>
                                            <div class="form-row">
                                                <div class="form-group"><label>超时时间(秒)</label><input type="number" class="form-control" id="proCfgTimeout" value="300" min="10"></div>
                                                <div class="form-group"><label>重试次数</label><input type="number" class="form-control" id="proCfgRetries" value="3" min="0"></div>
                                            </div>
                                            <div class="checkbox-group">
                                                <label><input type="checkbox" id="proCfgOverwrite"> 覆盖已存在的vsmeta</label>
                                                <label><input type="checkbox" id="proCfgBackup" checked> 启用备份</label>
                                                <label><input type="checkbox" id="proCfgDryRun"> 预演模式</label>
                                                <label><input type="checkbox" id="proCfgTvShow"> 电视剧模式</label>
                                            </div>
                                        </div>

                                        <div class="pro-card">
                                            <div class="pro-card-header">🖼️ 图片配置</div>
                                            <div class="form-row">
                                                <div class="form-group"><label>图片质量</label><input type="number" class="form-control" id="proCfgImageQuality" value="85" min="1" max="100"></div>
                                                <div class="form-group"><label>最大宽度</label><input type="number" class="form-control" id="proCfgMaxWidth" value="1920" min="100"></div>
                                            </div>
                                            <div class="form-row">
                                                <div class="form-group"><label>最大高度</label><input type="number" class="form-control" id="proCfgMaxHeight" value="1080" min="100"></div>
                                                <div class="form-group"><label>输出格式</label><select class="form-control" id="proCfgImageFormat"><option value="jpg">JPG</option><option value="png">PNG</option><option value="webp">WebP</option></select></div>
                                            </div>
                                            <div class="checkbox-group">
                                                <label><input type="checkbox" id="proCfgResizeImage" checked> 调整图片大小</label>
                                                <label><input type="checkbox" id="proCfgOptimizeImage" checked> 优化图片</label>
                                                <label><input type="checkbox" id="proCfgDownloadPoster"> 下载海报</label>
                                                <label><input type="checkbox" id="proCfgDownloadFanart"> 下载背景图</label>
                                            </div>
                                        </div>

                                        <div class="pro-card">
                                            <div class="pro-card-header">📋 文件过滤</div>
                                            <div class="form-group"><label>包含的扩展名</label><input type="text" class="form-control" id="proCfgIncludeExt" value="mkv,mp4,avi,ts,mov,wmv"></div>
                                            <div class="form-group"><label>排除模式</label><input type="text" class="form-control" id="proCfgExclude" placeholder="*.sample*, *.txt"></div>
                                            <div class="form-group"><label>文件名正则</label><input type="text" class="form-control" id="proCfgRegex" placeholder=".*1080p.*"></div>
                                            <div class="form-row">
                                                <div class="form-group"><label>最小大小(MB)</label><input type="number" class="form-control" id="proCfgMinSizeMB" value="0" min="0"></div>
                                                <div class="form-group"><label>最大大小(MB)</label><input type="number" class="form-control" id="proCfgMaxSizeMB" value="0" min="0"></div>
                                            </div>
                                        </div>

                                        <div class="pro-card">
                                            <div class="pro-card-header">🌍 中文转换</div>
                                            <div class="form-group"><label style="display:flex;align-items:center;gap:8px"><input type="checkbox" id="proCfgChineseConvert"> 启用中文简繁转换</label></div>
                                            <div class="form-group"><label>转换目标</label><select class="form-control" id="proCfgChineseTarget"><option value="zh-cn">简体中文 (zh-cn)</option><option value="zh-tw">繁体中文 (zh-tw)</option><option value="zh-hk">繁体中文 (zh-hk)</option><option value="zh-sg">简体中文 (zh-sg)</option></select></div>
                                        </div>

                                        <div class="pro-card">
                                            <div class="pro-card-header">🛡️ 安全设置</div>
                                            <div class="form-group"><label style="display:flex;align-items:center;gap:8px"><input type="checkbox" id="proCfgSafeWrite" checked> 事务性写入</label></div>
                                            <div class="form-group"><label style="display:flex;align-items:center;gap:8px"><input type="checkbox" id="proCfgSanitizeFilename"> 清理文件名</label></div>
                                            <div class="form-group"><label style="display:flex;align-items:center;gap:8px"><input type="checkbox" id="proCfgFixEncoding" checked> 自动修复编码</label></div>
                                        </div>

                                        <div class="pro-card">
                                            <div class="pro-card-header">📝 日志配置</div>
                                            <div class="form-row">
                                                <div class="form-group"><label>日志级别</label><select class="form-control" id="proCfgLogLevel"><option value="DEBUG">DEBUG</option><option value="INFO" selected>INFO</option><option value="WARNING">WARNING</option><option value="ERROR">ERROR</option></select></div>
                                                <div class="form-group"><label>日志文件</label><input type="text" class="form-control" id="proCfgLogFile" placeholder="converter.log"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 可视化对比页面 -->
                        <div class="pro-inner-page" id="pro-page-compare">
                            <div class="pro-layout-full">
                                <div class="pro-panel" style="overflow:auto">
                                    <div class="pro-panel-header">
                                        <h3>🎨 可视化对比</h3>
                                        <div style="display:flex;gap:8px;align-items:center">
                                            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px"><input type="checkbox" id="proGlobalRollbackMode"> 全局回滚模式</label>
                                            <button class="btn" onclick="proRefreshVisual()">🔄 刷新</button>
                                        </div>
                                    </div>
                                    <div class="pro-panel-content">
                                        <div style="display:grid;grid-template-columns:320px 1fr;gap:16px;min-height:600px">
                                            <!-- 文件树 -->
                                            <div class="pro-card" style="display:flex;flex-direction:column;overflow:hidden;margin:0">
                                                <div class="pro-card-header">📁 文件树</div>
                                                <div id="proVisualFileTree" style="flex:1;overflow:auto">
                                                    <div class="empty-state"><div class="icon">📁</div><p>点击"扫描"加载文件</p></div>
                                                </div>
                                            </div>
                                            
                                            <!-- 对比详情 -->
                                            <div class="pro-card" style="display:flex;flex-direction:column;overflow:hidden;margin:0">
                                                <div class="pro-card-header">🔍 对比详情</div>
                                                <div id="proVisualDiff" style="flex:1;overflow:auto">
                                                    <div class="empty-state"><div class="icon">📊</div><p>选择文件查看详细对比</p></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 日志详情页面 -->
                        <div class="pro-inner-page" id="pro-page-logs">
                            <div class="pro-layout-full">
                                <div class="pro-panel" style="overflow:hidden">
                                    <div class="pro-panel-header">
                                        <h3>📋 日志详情</h3>
                                        <div style="display:flex;gap:8px">
                                            <label style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-muted);cursor:pointer"><input type="checkbox" id="proAutoScroll" checked> 自动滚动</label>
                                            <button class="btn" onclick="proClearLogs()">🗑️ 清空</button>
                                            <button class="export-btn" onclick="proExportLogs()">📥 导出日志</button>
                                        </div>
                                    </div>
                                    <div class="pro-panel-content" style="padding:0">
                                        <div class="log-container" id="proLogContainer" style="height:100%;font-family:'JetBrains Mono',monospace">
                                            <div class="log-entry"><span class="time">[--:--:--]</span> 等待日志...</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

# 替换专业模式页面
if old_pro_page_start in content:
    content = content.replace(old_pro_page_start, new_pro_page)
    print("✅ 成功替换专业模式页面")
else:
    print("❌ 找不到要替换的专业模式页面")

# 现在添加专业模式的JavaScript函数 - 找到合适的位置插入
js_insert_marker = '        // === 专业模式 ==='
if js_insert_marker in content:
    pro_js_extension = '''
        // 专业模式内部标签页切换
        function proSwitchInnerTab(tabName){
            document.querySelectorAll('.pro-inner-tab').forEach(t=>{
                t.classList.toggle('active', t.dataset.proTab===tabName);
            });
            document.querySelectorAll('.pro-inner-page').forEach(p=>{
                p.classList.remove('active');
            });
            const page=document.getElementById('pro-page-'+tabName);
            if(page)page.classList.add('active');
        }

        // 加载配置到专业模式
        function loadConfigToPro(){
            const config=currentConfig||{};
            document.getElementById('proCfgDir').value=config.directory||'';
            document.getElementById('proCfgThreads').value=config.threads||4;
            document.getElementById('proCfgBatchSize').value=config.batch_size||100;
            document.getElementById('proCfgTimeout').value=config.timeout||300;
            document.getElementById('proCfgRetries').value=config.retries||3;
            document.getElementById('proCfgOverwrite').checked=config.overwrite||false;
            document.getElementById('proCfgBackup').checked=config.backup||true;
            document.getElementById('proCfgDryRun').checked=config.dry_run||false;
            document.getElementById('proCfgTvShow').checked=config.tv_show||false;
            document.getElementById('proCfgImageQuality').value=config.image_quality||85;
            document.getElementById('proCfgMaxWidth').value=config.max_width||1920;
            document.getElementById('proCfgMaxHeight').value=config.max_height||1080;
            document.getElementById('proCfgImageFormat').value=config.image_format||'jpg';
            document.getElementById('proCfgResizeImage').checked=config.resize_image||true;
            document.getElementById('proCfgOptimizeImage').checked=config.optimize_image||true;
            document.getElementById('proCfgDownloadPoster').checked=config.download_poster||false;
            document.getElementById('proCfgDownloadFanart').checked=config.download_fanart||false;
            document.getElementById('proCfgIncludeExt').value=config.include_extensions||'mkv,mp4,avi,ts,mov,wmv';
            document.getElementById('proCfgExclude').value=config.exclude_patterns||'';
            document.getElementById('proCfgRegex').value=config.regex_filter||'';
            document.getElementById('proCfgMinSizeMB').value=config.min_size_mb||0;
            document.getElementById('proCfgMaxSizeMB').value=config.max_size_mb||0;
            document.getElementById('proCfgChineseConvert').checked=config.chinese_convert||false;
            document.getElementById('proCfgChineseTarget').value=config.chinese_target||'zh-cn';
            document.getElementById('proCfgSafeWrite').checked=config.safe_write||true;
            document.getElementById('proCfgSanitizeFilename').checked=config.sanitize_filename||false;
            document.getElementById('proCfgFixEncoding').checked=config.fix_encoding||true;
            document.getElementById('proCfgLogLevel').value=config.log_level||'INFO';
            document.getElementById('proCfgLogFile').value=config.log_file||'';
            showToast('配置已加载','success');
        }

        // 保存专业模式配置
        async function saveConfigFromPro(){
            const newConfig={
                directory:document.getElementById('proCfgDir').value||'.',
                threads:parseInt(document.getElementById('proCfgThreads').value)||4,
                batch_size:parseInt(document.getElementById('proCfgBatchSize').value)||100,
                timeout:parseInt(document.getElementById('proCfgTimeout').value)||300,
                retries:parseInt(document.getElementById('proCfgRetries').value)||3,
                overwrite:document.getElementById('proCfgOverwrite').checked,
                backup:document.getElementById('proCfgBackup').checked,
                dry_run:document.getElementById('proCfgDryRun').checked,
                tv_show:document.getElementById('proCfgTvShow').checked,
                image_quality:parseInt(document.getElementById('proCfgImageQuality').value)||85,
                max_width:parseInt(document.getElementById('proCfgMaxWidth').value)||1920,
                max_height:parseInt(document.getElementById('proCfgMaxHeight').value)||1080,
                image_format:document.getElementById('proCfgImageFormat').value||'jpg',
                resize_image:document.getElementById('proCfgResizeImage').checked,
                optimize_image:document.getElementById('proCfgOptimizeImage').checked,
                download_poster:document.getElementById('proCfgDownloadPoster').checked,
                download_fanart:document.getElementById('proCfgDownloadFanart').checked,
                include_extensions:document.getElementById('proCfgIncludeExt').value||'mkv,mp4,avi,ts,mov,wmv',
                exclude_patterns:document.getElementById('proCfgExclude').value||'',
                regex_filter:document.getElementById('proCfgRegex').value||'',
                min_size_mb:parseInt(document.getElementById('proCfgMinSizeMB').value)||0,
                max_size_mb:parseInt(document.getElementById('proCfgMaxSizeMB').value)||0,
                chinese_convert:document.getElementById('proCfgChineseConvert').checked,
                chinese_target:document.getElementById('proCfgChineseTarget').value||'zh-cn',
                safe_write:document.getElementById('proCfgSafeWrite').checked,
                sanitize_filename:document.getElementById('proCfgSanitizeFilename').checked,
                fix_encoding:document.getElementById('proCfgFixEncoding').checked,
                log_level:document.getElementById('proCfgLogLevel').value||'INFO',
                log_file:document.getElementById('proCfgLogFile').value||''
            };
            try{
                await api('/api/config','POST',newConfig);
                currentConfig=newConfig;
                showToast('配置已保存','success');
                if(typeof loadConfigToForm==='function')loadConfigToForm();
            }catch(e){
                showToast('保存配置失败: '+e.message,'error');
            }
        }

        // 刷新可视化对比
        function proRefreshVisual(){
            proScanFiles().then(()=>{
                proRenderVisualFileTree();
            });
        }

        // 渲染可视化文件树
        function proRenderVisualFileTree(){
            const container=document.getElementById('proVisualFileTree');
            if(!container)return;
            if(!proFiles||proFiles.length===0){
                container.innerHTML='<div class="empty-state"><div class="icon">📁</div><p>没有文件可显示</p></div>';
                return;
            }
            container.innerHTML=proFiles.map((f,idx)=>{
                const statusClass=f.status||'warning';
                const statusDotClass={success:'success',warning:'warning',error:'error'}[statusClass];
                return `<div class="file-tree-item" onclick="proSelectVisualFile(${idx})">
                    <div class="status-dot ${statusDotClass}"></div>
                    <div style="flex:1;min-width:0">
                        <div class="filename">${escHtml(f.name)}</div>
                        <div class="file-meta">${escHtml(f.directory||'')}</div>
                    </div>
                </div>`;
            }).join('');
        }

        // 选择可视化对比文件
        async function proSelectVisualFile(idx){
            if(!proFiles||!proFiles[idx])return;
            proSelectedFile=proFiles[idx].path;
            proRenderFileTree();
            proRenderVisualFileTree();
            await proRenderVisualDiff(proFiles[idx]);
        }

        // 渲染可视化对比详情
        async function proRenderVisualDiff(fileInfo){
            const container=document.getElementById('proVisualDiff');
            if(!container)return;
            try{
                const data=await api('/api/pro/file-detail','POST',{filepath:fileInfo.path});
                let html='';
                // 文件基本信息
                html+=`<div class="pro-card" style="margin-bottom:12px">
                    <div class="pro-card-header">📄 文件信息</div>
                    <div style="display:flex;flex-wrap:wrap;gap:12px">
                        <span class="validation-badge ${data.has_nfo?'pass':'fail'}">${data.has_nfo?'✓':'✗'} NFO</span>
                        <span class="validation-badge ${data.has_vsmeta?'pass':'fail'}">${data.has_vsmeta?'✓':'✗'} VSMETA</span>
                        <span class="validation-badge ${data.has_poster?'pass':'fail'}">${data.has_poster?'✓':'✗'} 海报</span>
                        <span class="validation-badge ${data.has_backdrop?'pass':'fail'}">${data.has_backdrop?'✓':'✗'} 背景图</span>
                    </div>
                </div>`;
                // 元数据对比
                if(data.nfo_metadata||data.vsmeta_metadata){
                    const nfo=data.nfo_metadata||{};
                    const vsmeta=data.vsmeta_metadata||{};
                    html+=`<div class="pro-card" style="margin-bottom:12px">
                        <div class="pro-card-header">🔄 元数据对比</div>
                        <div class="diff-container">
                            <div class="diff-panel">
                                <div class="diff-panel-header">
                                    <span class="diff-panel-title">📄 NFO 原始数据</span>
                                </div>
                                ${renderDiffItem('标题',nfo.title,vsmeta.title)}
                                ${renderDiffItem('年份',nfo.year,vsmeta.year)}
                                ${renderDiffItem('评分',nfo.rating,vsmeta.rating)}
                                ${renderDiffItem('类型',(nfo.genres||[]).join(', '),(vsmeta.genres||[]).join(', '))}
                                ${renderDiffItem('导演',(nfo.directors||[]).join(', '),(vsmeta.directors||[]).join(', '))}
                            </div>
                            <div class="diff-panel">
                                <div class="diff-panel-header">
                                    <span class="diff-panel-title">📦 VSMETA 生成数据</span>
                                </div>
                                <div style="padding:10px;background:var(--bg-card);border-radius:6px;font-size:12px;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;word-break:break-all">
                                    ${vsmeta.raw?escHtml(vsmeta.raw):'暂无数据'}
                                </div>
                            </div>
                        </div>
                    </div>`;
                }
                // 回滚按钮
                if(data.has_vsmeta){
                    html+=`<div class="pro-card">
                        <div class="pro-card-header">🔄 回滚操作</div>
                        <p style="color:var(--text-secondary);margin-bottom:12px;font-size:13px">删除生成的vsmeta文件，恢复原始状态。</p>
                        <div style="display:flex;gap:12px">
                            <button class="btn btn-danger" onclick="proRollbackFile('${escHtml(fileInfo.path)}')">↩️ 回滚此文件</button>
                        </div>
                    </div>`;
                }
                container.innerHTML=html;
            }catch(e){
                container.innerHTML=`<div class="empty-state"><div class="icon">❌</div><p>加载对比数据失败: ${escHtml(e.message)}</p></div>`;
            }
        }

        // 渲染单个对比项
        function renderDiffItem(label,nfoVal,vsVal){
            const isSame=String(nfoVal||'')===String(vsVal||'');
            const cls=isSame?'':'missing';
            const vsCls=isSame?'generated':(vsVal?'generated':'missing');
            return `<div class="diff-item">
                <div class="diff-item-label">${escHtml(label)}</div>
                <div class="diff-item-values">
                    <div class="diff-value original ${!nfoVal?'missing':''}">${escHtml(String(nfoVal||'N/A'))}</div>
                    <div class="diff-value ${vsCls}">${escHtml(String(vsVal||'N/A'))}</div>
                </div>
            </div>`;
        }

        // 导出日志
        function proExportLogs(){
            const container=document.getElementById('proLogStream');
            if(!container)return;
            const text=Array.from(container.children).map(el=>el.textContent||'').join('\\n');
            const blob=new Blob([text],{type:'text/plain;charset=utf-8'});
            const url=URL.createObjectURL(blob);
            const a=document.createElement('a');
            a.href=url;
            a.download='pro_logs_'+new Date().toISOString().slice(0,10)+'.txt';
            a.click();
            URL.revokeObjectURL(url);
            showToast('日志已导出','success');
        }

        // 增强版回滚函数
        async function proRollbackFile(filepath){
            if(!confirm('确定要回滚此文件吗？这将删除vsmeta文件。'))return;
            try{
                await api('/api/pro/rollback','POST',{filepath:filepath});
                showToast('回滚成功','success');
                proScanFiles();
            }catch(e){
                showToast('回滚失败: '+e.message,'error');
            }
        }
'''
    # 在专业模式函数定义后添加
    content = content.replace(js_insert_marker, js_insert_marker + pro_js_extension)
    print("✅ 成功添加专业模式JavaScript函数")
else:
    print("❌ 找不到JavaScript插入点")

# 写回文件
with open('web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 专业模式重构完成！")
