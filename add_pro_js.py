#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# 读取web_ui.py
with open('web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 更新switchTab函数
old_switchtab = "function switchTab(name){document.querySelectorAll('.tab').forEach(t=>{t.classList.toggle('active',t.dataset.tab===name)});document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));const page=document.getElementById('page-'+name);if(page)page.classList.add('active');if(name==='convert')refreshScanResults();if(name==='checkpoint')refreshCheckpoint();if(name==='backup')refreshBackups();if(name==='visual'){startVisualMonitor()}}"

new_switchtab = "function switchTab(name){document.querySelectorAll('.tab').forEach(t=>{t.classList.toggle('active',t.dataset.tab===name)});document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));const page=document.getElementById('page-'+name);if(page)page.classList.add('active');if(name==='convert')refreshScanResults();if(name==='checkpoint')refreshCheckpoint();if(name==='backup')refreshBackups();if(name==='visual'){startVisualMonitor()};if(name==='pro'){proStartPolling()}}"

content = content.replace(old_switchtab, new_switchtab)

# 2. 添加专业模式的JavaScript函数（在"// === 极简模式 ==="之前）
pro_js = '''
        // === 专业模式 ===
        let proPollTimer=null;
        let proSelectedFile=null;
        let proFiles=[];
        let proStartTime=null;

        async function proScanFiles(){
            const sourceDir=document.getElementById('proSourceDir').value;
            const outputDir=document.getElementById('proOutputDir').value;
            if(!sourceDir){
                showToast('请输入源目录','warning');
                return;
            }
            showToast('扫描中...','info');
            try{
                const data=await api('/api/pro/scan','POST',{source_dir:sourceDir,output_dir:outputDir});
                proFiles=data.files||[];
                document.getElementById('proFileCount').textContent=proFiles.length+' 个文件';
                document.getElementById('proStatTotal').textContent=proFiles.length;
                proRenderFileTree();
                showToast('扫描完成，找到 '+proFiles.length+' 个文件','success');
            }catch(e){
                showToast('扫描失败: '+e.message,'error');
            }
        }

        function proRenderFileTree(){
            const container=document.getElementById('proFileTree');
            if(proFiles.length===0){
                container.innerHTML='<div class="empty-state"><div class="icon">📂</div><p>没有找到视频文件</p></div>';
                return;
            }
            container.innerHTML=proFiles.map((f,idx)=>{
                const statusClass=f.status||'warning';
                const statusText={success:'成功',warning:'警告',error:'失败'}[statusClass]||'未知';
                return '<div class="file-tree-item '+(proSelectedFile===f.path?'active':'')+'" onclick="proSelectFile('+idx+')"><div class="status-dot '+statusClass+'"></div><div style="flex:1;min-width:0"><div class="filename">'+escHtml(f.name)+'</div><div class="file-meta">'+escHtml(f.directory||'')+'</div></div></div>';
            }).join('');
        }

        async function proSelectFile(idx){
            proSelectedFile=proFiles[idx].path;
            proRenderFileTree();
            try{
                const data=await api('/api/pro/file-detail','POST',{filepath:proSelectedFile});
                proRenderDiff(data);
            }catch(e){
                showToast('获取详情失败: '+e.message,'error');
            }
        }

        function proRenderDiff(data){
            const container=document.getElementById('proDiffView');
            const validation=[];
            let html='<div style="display:flex;flex-direction:column;gap:12px;height:100%">';
            
            // 文件基本信息
            html+='<div style="background:var(--bg-input);border-radius:8px;padding:16px">';
            html+='<div style="font-size:15px;font-weight:600;margin-bottom:12px">'+escHtml(data.filename)+'</div>';
            html+='<div style="display:flex;gap:8px;flex-wrap:wrap">';
            html+='<span class="validation-badge '+(data.has_nfo?'pass':'fail')+'">'+(data.has_nfo?'✓':'✗')+' NFO</span>';
            html+='<span class="validation-badge '+(data.has_vsmeta?'pass':'fail')+'">'+(data.has_vsmeta?'✓':'✗')+' VSMETA</span>';
            html+='<span class="validation-badge '+(data.has_poster?'pass':'fail')+'">'+(data.has_poster?'✓':'✗')+' 海报</span>';
            html+='<span class="validation-badge '+(data.has_backdrop?'pass':'fail')+'">'+(data.has_backdrop?'✓':'✗')+' 背景图</span>';
            html+='</div></div>';
            
            if(data.nfo_metadata&&data.vsmeta_metadata){
                const nfo=data.nfo_metadata;
                const vsmeta=data.vsmeta_metadata;
                
                // 对比表格
                const fields=[
                    {label:'标题',nfo:nfo.title,vsmeta:vsmeta.title,key:'title'},
                    {label:'年份',nfo:nfo.year,vsmeta:vsmeta.year,key:'year'},
                    {label:'评分',nfo:nfo.rating,vsmeta:vsmeta.rating,key:'rating'},
                    {label:'类型',nfo:(nfo.genres||[]).join(', '),vsmeta:(vsmeta.genres||[]).join(', '),key:'genres'},
                    {label:'导演',nfo:(nfo.directors||[]).join(', '),vsmeta:(vsmeta.directors||[]).join(', '),key:'directors'},
                ];
                
                html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;min-height:0;overflow:auto">';
                html+='<div style="background:var(--bg-input);border-radius:8px;padding:12px;overflow:auto">';
                html+='<div style="font-size:12px;font-weight:600;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)">📄 原始 NFO</div>';
                fields.forEach(field=>{
                    const isSame=String(field.nfo||'')===String(field.vsmeta||'');
                    const cls=isSame?'generated':'missing';
                    html+='<div style="margin-bottom:8px"><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-bottom:2px">'+field.label+'</div><div class="diff-value original '+cls+'" style="font-size:12px">'+escHtml(String(field.nfo||'N/A'))+'</div></div>';
                });
                html+='</div>';
                
                html+='<div style="background:var(--bg-input);border-radius:8px;padding:12px;overflow:auto">';
                html+='<div style="font-size:12px;font-weight:600;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)">📦 生成 VSMETA</div>';
                fields.forEach(field=>{
                    const isSame=String(field.nfo||'')===String(field.vsmeta||'');
                    const cls=isSame?'generated':'missing';
                    html+='<div style="margin-bottom:8px"><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-bottom:2px">'+field.label+'</div><div class="diff-value generated '+cls+'" style="font-size:12px">'+escHtml(String(field.vsmeta||'N/A'))+'</div></div>';
                });
                html+='</div></div>';
            }else{
                html+='<div class="empty-state"><div class="icon">📊</div><p>无法对比：缺少元数据</p></div>';
            }
            
            html+='</div>';
            container.innerHTML=html;
        }

        async function proStartConversion(){
            const sourceDir=document.getElementById('proSourceDir').value;
            const outputDir=document.getElementById('proOutputDir').value;
            const mediaType=document.getElementById('proMediaType').value;
            const conflictMode=document.getElementById('proConflictMode').value;
            
            if(!sourceDir){
                showToast('请输入源目录','warning');
                return;
            }
            
            document.getElementById('proStartBtn').style.display='none';
            document.getElementById('proStopBtn').style.display='';
            proStartTime=Date.now();
            
            try{
                const data=await api('/api/pro/start','POST',{
                    source_dir:sourceDir,
                    output_dir:outputDir,
                    media_type:mediaType,
                    conflict_mode:conflictMode
                });
                proPollTimer=setInterval(proPollStatus,500);
                showToast('转换已启动','success');
                proAddLog('info','转换任务已启动');
            }catch(e){
                showToast('启动失败: '+e.message,'error');
                document.getElementById('proStartBtn').style.display='';
                document.getElementById('proStopBtn').style.display='none';
            }
        }

        async function proStopConversion(){
            try{
                await api('/api/pro/stop','POST',{});
                if(proPollTimer){
                    clearInterval(proPollTimer);
                    proPollTimer=null;
                }
                document.getElementById('proStartBtn').style.display='';
                document.getElementById('proStopBtn').style.display='none';
                showToast('转换已停止','warning');
                proAddLog('warn','用户停止了转换任务');
            }catch(e){
                showToast('停止失败: '+e.message,'error');
            }
        }

        async function proPollStatus(){
            try{
                const data=await api('/api/status');
                const p=data.progress||{};
                document.getElementById('proStatSuccess').textContent=p.success||0;
                document.getElementById('proStatFailed').textContent=p.failed||0;
                document.getElementById('proStatSkipped').textContent=p.skipped||0;
                
                if(proStartTime){
                    const elapsed=Math.round((Date.now()-proStartTime)/1000);
                    document.getElementById('proStatTime').textContent=elapsed+'s';
                }
                
                if(!data.is_running&&proPollTimer){
                    clearInterval(proPollTimer);
                    proPollTimer=null;
                    document.getElementById('proStartBtn').style.display='';
                    document.getElementById('proStopBtn').style.display='none';
                    showToast('转换完成！','success');
                    proAddLog('success','转换任务已完成');
                    proScanFiles();
                }
            }catch(e){
                console.error(e);
            }
        }

        function proStartPolling(){
            if(proPollTimer)return;
            proPollTimer=setInterval(async()=>{
                try{
                    const data=await api('/api/logs');
                    if(data.logs&&data.logs.length>0){
                        const recent=data.logs.slice(-10);
                        proUpdateLogStream(recent);
                    }
                }catch(e){
                    console.error(e);
                }
            },2000);
        }

        function proAddLog(level,message){
            const timestamp=new Date().toLocaleTimeString();
            const container=document.getElementById('proLogStream');
            const entry=document.createElement('div');
            entry.className='log-entry';
            entry.innerHTML='<span class="timestamp">'+timestamp+'</span><span class="level '+level+'">'+level.toUpperCase()+'</span><span class="message">'+escHtml(message)+'</span>';
            container.appendChild(entry);
            container.scrollTop=container.scrollHeight;
        }

        function proUpdateLogStream(logs){
            const container=document.getElementById('proLogStream');
            container.innerHTML=logs.map(log=>{
                const time=new Date(log.time||Date.now()).toLocaleTimeString();
                return '<div class="log-entry"><span class="timestamp">'+time+'</span><span class="level '+log.level+'">'+log.level.toUpperCase()+'</span><span class="message">'+escHtml(log.message||'')+'</span></div>';
            }).join('');
            container.scrollTop=container.scrollHeight;
        }

        function proClearLogs(){
            document.getElementById('proLogStream').innerHTML='<div style="color:var(--text-muted);padding:20px;text-align:center">日志已清除</div>';
        }

        async function proExportReport(){
            try{
                const data=await api('/api/pro/report','POST',{});
                const blob=new Blob([data.csv],{type:'text/csv;charset=utf-8'});
                const url=URL.createObjectURL(blob);
                const a=document.createElement('a');
                a.href=url;
                a.download='conversion_report_'+new Date().toISOString().slice(0,10)+'.csv';
                a.click();
                URL.revokeObjectURL(url);
                showToast('报告已导出','success');
            }catch(e){
                showToast('导出失败: '+e.message,'error');
            }
        }

'''

# 在"// === 极简模式 ==="之前插入
insert_marker = "        // === 极简模式 ==="
if insert_marker in content:
    content = content.replace(insert_marker, pro_js + "\n" + insert_marker)
    print("✅ 专业模式JavaScript已添加")
else:
    print("❌ 未找到插入标记")

# 写回文件
with open('web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)
