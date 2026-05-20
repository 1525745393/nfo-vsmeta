#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# 读取web_ui.py
with open('web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加专业模式API（在极简模式API之后）
pro_api = '''

# ============================================================================
# 专业模式 API
# ============================================================================


@app.route("/api/pro/scan", methods=["POST"])
@require_api_token
@require_csrf
def api_pro_scan() -> Tuple:
    """专业模式 - 扫描目录"""
    data = request.get_json(silent=True) or {}
    source_dir = str(data.get("source_dir", ".")).strip()
    output_dir = str(data.get("output_dir", source_dir)).strip()
    
    if not source_dir:
        return jsonify({"error": "源目录不能为空"}), 400
    if not _validate_path(source_dir, allow_absolute=True):
        return jsonify({"error": "源目录路径不安全"}), 403
    if not os.path.isdir(source_dir):
        return jsonify({"error": "源目录不存在"}), 404
    
    try:
        from nfo_to_vsmeta_converter_complete import Config
        
        config = Config()
        video_extensions = getattr(config, "video_extensions", [".mp4", ".mkv", ".avi", ".ts", ".wmv", ".rmvb", ".mov", ".m4v"])
        nfo_extensions = getattr(config, "nfo_extensions", [".nfo"])
        vsmeta_extension = getattr(config, "vsmeta_extension", ".vsmeta")
        
        files = []
        for root, dirs, filenames in os.walk(source_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in video_extensions:
                    filepath = os.path.join(root, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    # 检查NFO
                    has_nfo = any(os.path.exists(os.path.join(root, base_name + nfo_ext)) for nfo_ext in nfo_extensions)
                    
                    # 检查VSMETA（在输出目录）
                    out_dir = output_dir if os.path.exists(output_dir) else root
                    has_vsmeta = os.path.exists(os.path.join(out_dir, base_name + vsmeta_extension))
                    
                    # 检查海报和背景图
                    poster_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                    poster_names = [base_name + "-poster", base_name, "poster", "folder"]
                    has_poster = any(os.path.exists(os.path.join(root, name + ext)) for name in poster_names for ext in poster_exts)
                    
                    backdrop_names = [base_name + "-fanart", base_name + "-backdrop", "fanart", "backdrop"]
                    has_backdrop = any(os.path.exists(os.path.join(root, name + ext)) for name in backdrop_names for ext in poster_exts)
                    
                    # 确定状态
                    if has_nfo and has_vsmeta:
                        status = "success"
                    elif not has_nfo:
                        status = "error"
                    else:
                        status = "warning"
                    
                    files.append({
                        "name": filename,
                        "path": filepath,
                        "directory": root,
                        "status": status,
                        "has_nfo": has_nfo,
                        "has_vsmeta": has_vsmeta,
                        "has_poster": has_poster,
                        "has_backdrop": has_backdrop,
                    })
        
        files.sort(key=lambda x: x["name"])
        _add_log("info", f"扫描完成，找到 {len(files)} 个视频文件")
        return jsonify({"files": files})
    except Exception as e:
        _add_log("error", f"扫描失败: {e}")
        return jsonify({"error": f"扫描失败: {e}"}), 500


@app.route("/api/pro/file-detail", methods=["POST"])
@require_api_token
@require_csrf
def api_pro_file_detail() -> Tuple:
    """专业模式 - 获取文件详情和对比"""
    data = request.get_json(silent=True) or {}
    filepath = str(data.get("filepath", "")).strip()
    
    if not filepath or not os.path.isfile(filepath):
        return jsonify({"error": "文件不存在"}), 404
    if not _validate_path(filepath, allow_absolute=True):
        return jsonify({"error": "路径不安全"}), 403
    
    try:
        from nfo_to_vsmeta_converter_complete import Config, NFOParser
        
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        
        config = Config()
        nfo_extensions = getattr(config, "nfo_extensions", [".nfo"])
        vsmeta_extension = getattr(config, "vsmeta_extension", ".vsmeta")
        
        # 检查NFO
        nfo_path = None
        has_nfo = False
        for nfo_ext in nfo_extensions:
            candidate = os.path.join(directory, base_name + nfo_ext)
            if os.path.exists(candidate):
                nfo_path = candidate
                has_nfo = True
                break
        
        # 检查VSMETA
        has_vsmeta = os.path.exists(filepath + vsmeta_extension)
        
        # 检查海报和背景图
        poster_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        poster_names = [base_name + "-poster", base_name, "poster", "folder"]
        has_poster = any(os.path.exists(os.path.join(directory, name + ext)) for name in poster_names for ext in poster_exts)
        
        backdrop_names = [base_name + "-fanart", base_name + "-backdrop", "fanart", "backdrop"]
        has_backdrop = any(os.path.exists(os.path.join(directory, name + ext)) for name in backdrop_names for ext in poster_exts)
        
        result = {
            "filepath": filepath,
            "filename": filename,
            "directory": directory,
            "has_nfo": has_nfo,
            "has_vsmeta": has_vsmeta,
            "has_poster": has_poster,
            "has_backdrop": has_backdrop,
            "nfo_metadata": None,
            "vsmeta_metadata": None,
        }
        
        # 解析NFO
        if has_nfo and nfo_path:
            try:
                parser = NFOParser(config)
                metadata = parser.parse(nfo_path)
                if metadata:
                    result["nfo_metadata"] = {
                        "title": metadata.title,
                        "year": metadata.year,
                        "rating": metadata.rating,
                        "plot": metadata.plot,
                        "genres": metadata.genres,
                        "directors": metadata.directors,
                        "actors": metadata.actors,
                    }
            except Exception as e:
                logger.warning(f"解析NFO失败: {e}")
        
        # 读取VSMETA
        if has_vsmeta:
            try:
                vsmeta_path = filepath + vsmeta_extension
                with open(vsmeta_path, 'r', encoding='utf-8', errors='ignore') as f:
                    vsmeta_content = f.read()
                
                # 简单解析VSMETA
                import re
                result["vsmeta_metadata"] = {
                    "title": re.search(r'Title[=<>"\\s]+([^<>"\\n]+)', vsmeta_content) or re.search(r'title[=<>"\\s]+([^<>"\\n]+)', vsmeta_content, re.I),
                    "year": re.search(r'Year[=<>"\\s]+(\\d{4})', vsmeta_content) or re.search(r'year[=<>"\\s]+(\\d{4})', vsmeta_content, re.I),
                    "rating": re.search(r'Rating[=<>"\\s]+([\\d.]+)', vsmeta_content),
                    "plot": re.search(r'Plot[=<>"\\s]+([^<>"\\n]+)', vsmeta_content, re.I) or re.search(r'plot[=<>"\\s]+([^<>"\\n]+)', vsmeta_content, re.I),
                }
            except Exception as e:
                logger.warning(f"读取VSMETA失败: {e}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取详情失败: {e}")
        return jsonify({"error": f"获取详情失败: {e}"}), 500


@app.route("/api/pro/start", methods=["POST"])
@require_api_token
@require_csrf
def api_pro_start() -> Tuple:
    """专业模式 - 开始转换"""
    data = request.get_json(silent=True) or {}
    source_dir = str(data.get("source_dir", ".")).strip()
    output_dir = str(data.get("output_dir", source_dir)).strip()
    media_type = str(data.get("media_type", "movie")).strip()
    conflict_mode = str(data.get("conflict_mode", "skip")).strip()
    
    if not source_dir:
        return jsonify({"error": "源目录不能为空"}), 400
    if not _validate_path(source_dir, allow_absolute=True):
        return jsonify({"error": "源目录路径不安全"}), 403
    
    try:
        from nfo_to_vsmeta_converter_complete import Config, NFOToVSMETAConverter
        
        config = Config(
            directory=source_dir,
            overwrite_existing=conflict_mode == "overwrite",
            enable_backup=conflict_mode == "backup",
            safe_write_mode=True,
        )
        
        converter = NFOToVSMETAConverter(config)
        _set_state("converter", converter)
        _set_state("config", config)
        
        _add_log("info", f"专业模式启动: {source_dir}")
        
        def run_conversion():
            try:
                converter.convert_all()
            except Exception as e:
                _add_log("error", f"转换失败: {e}")
            finally:
                _set_state("converter", None)
        
        thread = threading.Thread(target=run_conversion, daemon=True)
        thread.start()
        
        return jsonify({"success": True})
    except Exception as e:
        _add_log("error", f"启动失败: {e}")
        return jsonify({"error": f"启动失败: {e}"}), 500


@app.route("/api/pro/stop", methods=["POST"])
@require_api_token
@require_csrf
def api_pro_stop() -> Tuple:
    """专业模式 - 停止转换"""
    try:
        converter = _get_state("converter")
        if converter and hasattr(converter, 'stop'):
            converter.stop()
        _set_state("converter", None)
        _add_log("info", "转换任务已停止")
        return jsonify({"success": True})
    except Exception as e:
        _add_log("error", f"停止失败: {e}")
        return jsonify({"error": f"停止失败: {e}"}), 500


@app.route("/api/pro/report", methods=["POST"])
@require_api_token
@require_csrf
def api_pro_report() -> Tuple:
    """专业模式 - 导出CSV报告"""
    try:
        from nfo_to_vsmeta_converter_complete import Config
        
        config = Config()
        source_dir = getattr(config, "directory", ".")
        video_extensions = getattr(config, "video_extensions", [".mp4", ".mkv", ".avi", ".ts", ".wmv", ".rmvb", ".mov", ".m4v"])
        nfo_extensions = getattr(config, "nfo_extensions", [".nfo"])
        vsmeta_extension = getattr(config, "vsmeta_extension", ".vsmeta")
        
        # 生成CSV
        csv = "文件名,目录,NFO,VSMETA,海报,背景图,状态\\n"
        
        for root, dirs, filenames in os.walk(source_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in video_extensions:
                    filepath = os.path.join(root, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    has_nfo = any(os.path.exists(os.path.join(root, base_name + nfo_ext)) for nfo_ext in nfo_extensions)
                    has_vsmeta = os.path.exists(filepath + vsmeta_extension)
                    
                    poster_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                    poster_names = [base_name + "-poster", base_name, "poster", "folder"]
                    has_poster = any(os.path.exists(os.path.join(root, name + ext)) for name in poster_names for ext in poster_exts)
                    
                    backdrop_names = [base_name + "-fanart", base_name + "-backdrop", "fanart", "backdrop"]
                    has_backdrop = any(os.path.exists(os.path.join(root, name + ext)) for name in backdrop_names for ext in poster_exts)
                    
                    if has_nfo and has_vsmeta:
                        status = "成功"
                    elif not has_nfo:
                        status = "失败-无NFO"
                    else:
                        status = "警告-无VSMETA"
                    
                    csv += f'"{filename}","{root}",{"有" if has_nfo else "无"},{"有" if has_vsmeta else "无"},{"有" if has_poster else "无"},{"有" if has_backdrop else "无"},"{status}"\\n'
        
        return jsonify({"csv": csv})
    except Exception as e:
        _add_log("error", f"生成报告失败: {e}")
        return jsonify({"error": f"生成报告失败: {e}"}), 500


'''

# 在极简模式API之后，启动部分之前插入
insert_marker = "# ============================================================================\n# 启动\n# ============================================================================"
if insert_marker in content:
    content = content.replace(insert_marker, pro_api + "\n" + insert_marker)
    print("✅ 专业模式API已添加")
else:
    print("❌ 未找到插入标记")

# 写回文件
with open('web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)
