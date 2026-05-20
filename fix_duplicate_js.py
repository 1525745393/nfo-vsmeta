#!/usr/bin/env python3
# -*- coding: utf-8 -*-
with open('/workspace/web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 我们需要找到"// === 专业模式 ===" 这个标记出现的位置
marker = '        // === 专业模式 ==='
parts = content.split(marker)

if len(parts) > 2:
    # 保留第一部分，加上第一份专业模式JS，然后跳过第二份，把后面的加上
    # 找到第二份JS之后的"// === 极简模式 ===" 或者其他部分的开始
    new_content = parts[0] + marker + parts[1]
    
    # 在parts[2]中找到"// === 极简模式 ==="这个标记
    simple_marker = '        // === 极简模式 ==='
    if simple_marker in parts[2]:
        idx = parts[2].find(simple_marker)
        new_content += parts[2][idx:]
    else:
        # 如果找不到，直接用原来的
        new_content = content
    
    with open('/workspace/web_ui.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ 成功修复重复的JavaScript代码')
else:
    print('❌ 未找到重复的JavaScript代码')
