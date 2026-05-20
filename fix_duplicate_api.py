#!/usr/bin/env python3
# -*- coding: utf-8 -*-
with open('/workspace/web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到第一组专业模式API的结束位置和第二组的开始位置
# 我们需要保留第一组，删除第二组
start_marker = '# ============================================================================\n# 专业模式 API\n# ============================================================================'

# 查找这个marker出现的位置
import re
parts = content.split(start_marker)

if len(parts) > 2:
    # 合并第一部分和第一组API，然后跳过第二组，加上后面的
    new_content = parts[0] + start_marker + parts[1]
    # 找到第二组API结束后"启动"部分的开始位置
    startup_marker = '# ============================================================================\n# 启动\n# ============================================================================'
    # 找到parts[2]中startup_marker的位置
    if startup_marker in parts[2]:
        idx = parts[2].find(startup_marker)
        new_content += parts[2][idx:]
    else:
        new_content += parts[2]
    
    with open('/workspace/web_ui.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ 成功修复重复的API')
else:
    print('❌ 未找到重复的API')
