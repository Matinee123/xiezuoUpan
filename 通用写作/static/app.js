let currentDocId = null, allDocs = [], currentVersion = null, currentTemplate = null;

// ======== 初始化 ========
async function init() {
  document.getElementById("homePage").style.display = "flex";
  document.getElementById("editorPage").style.display = "none";
  loadVersions();
  fetch("/api/version").then(r=>r.json()).then(d=>{ document.getElementById("verBadge").textContent="v"+d.version; }).catch(()=>{});
}
init();

// ======== 版本选择 ========
async function loadVersions() {
  try {
    const r = await fetch("/api/versions");
    renderCards(await r.json());
  } catch(e) {}
}

function renderCards(versions) {
  const grid = document.getElementById("cardGrid");
  grid.innerHTML = versions.map(v =>
    '<div class="version-card" onclick="switchVersion(\''+v.id+'\',\''+v.name+'\',\''+v.theme+'\')"><div class="card-icon">'+v.icon+'</div><div class="card-name">'+v.name+'</div><div class="card-desc">'+v.desc+'</div></div>'
  ).join("");
}

function switchVersion(id, name, theme) {
  currentVersion = id; currentTemplate = null;
  document.getElementById("homePage").style.display = "none";
  document.getElementById("editorPage").style.display = "flex";
  document.getElementById("verTitle").textContent = name;
  document.getElementById("app").setAttribute("data-theme", id);
  fetch("/api/config").then(r=>r.json()).then(d=>{ document.getElementById("engineStatus").textContent="引擎: "+d.engine; }).catch(()=>{});
  loadDocs(); loadTemplates(); switchSidebar("wizard");
  document.getElementById("aiMessages").innerHTML = "";
  addSystemMsg("欢迎使用"+name+"。选择左侧模板，填写信息后点智能生成。");
}

function goHome() {
  currentVersion = null; currentTemplate = null;
  document.getElementById("editorPage").style.display = "none";
  document.getElementById("homePage").style.display = "flex";
  document.getElementById("app").removeAttribute("data-theme");
}

function switchSidebar(tab) {
  document.getElementById("wizardPanel").style.display = (tab==="wizard")?"block":"none";
  document.getElementById("docsPanel").style.display = (tab==="docs")?"flex":"none";
  document.getElementById("tabWizard").classList.toggle("active", tab==="wizard");
  document.getElementById("tabDocs").classList.toggle("active", tab==="docs");
}

// ======== 写作向导 ========
async function loadTemplates() {
  try {
    const url = "/api/templates?v="+(currentVersion||"general");
    const r = await fetch(url); const data = await r.json();
    const sel = document.getElementById("templateSelect");
    sel.innerHTML = '<option value="">自由写作</option>';
    data.forEach(t => { sel.innerHTML += '<option value="'+t.name+'">'+t.name+'</option>'; });
    onTemplateChange();
  } catch(e) {}
}

function onTemplateChange() {
  const name = document.getElementById("templateSelect").value;
  if (!name) { document.getElementById("wizardFields").innerHTML=""; document.getElementById("wizardGenerateBtn").style.display="none"; currentTemplate=null; return; }
  const url = "/api/template/"+encodeURIComponent(name)+"?v="+(currentVersion||"general");
  fetch(url).then(r=>r.json()).then(t => {
    if (t.fields) { currentTemplate = {name:name,fields:t.fields}; renderFields(t.fields, t.example); }
    else { document.getElementById("wizardFields").innerHTML=""; document.getElementById("wizardGenerateBtn").style.display="none"; }
  }).catch(()=>{ document.getElementById("wizardFields").innerHTML='<div class="wizard-field-hint" style="text-align:center;padding:20px;">加载失败</div>'; });
}

function renderFields(fields, example) {
  const TEXTAREA_IDS = "body items points actions problems plan agenda decisions tasks requirements background reason content features rights understanding claims facts evidence defense_points counter_evidence demands analysis risks suggestions missing legal_analysis evidence_analysis rebuttal grounds errors evidence_groups evidence_items scope legal_basis opinion appeal_claims";
  const container = document.getElementById("wizardFields");
  let html = fields.map(f => {
    let inputHtml;
    if (f.type === "select") {
      inputHtml = '<select class="wizard-field-input" id="wf_'+f.id+'">'+f.options.map(o=>'<option value="'+o+'">'+o+'</option>').join("")+'</select>';
    } else if (TEXTAREA_IDS.indexOf(f.id) >= 0) {
      inputHtml = '<textarea class="wizard-field-input" id="wf_'+f.id+'" rows="3" placeholder="'+(f.hint||"")+'"></textarea>';
    } else {
      inputHtml = '<input type="text" class="wizard-field-input" id="wf_'+f.id+'" placeholder="'+(f.hint||"")+'">';
    }
    return '<div class="wizard-field"><label class="wizard-field-label">'+f.label+(f.required?'<span class="required">*</span>':"")+'</label>'+inputHtml+(f.hint?'<div class="wizard-field-hint">'+f.hint+'</div>':"")+'</div>';
  }).join("");
  if (example) {
    html += '<div class="wizard-example" onclick="this.classList.toggle(\'open\')"><div class="wizard-example-header">💡 参考范例（点击展开）</div><div class="wizard-example-content">'+example.replace(/\n/g,"<br>")+'</div></div>';
  }
  container.innerHTML = html;
  document.getElementById("wizardGenerateBtn").style.display = "block";
}

async function aiGenerateWizard() {
  if (!currentTemplate) return;
  let prompt = "请根据以下信息撰写一份专业的【"+currentTemplate.name+"】：\n\n";
  let wordCountHint = "";
  currentTemplate.fields.forEach(f => {
    const el = document.getElementById("wf_"+f.id);
    if (!el) return;
    const val = el.tagName==="SELECT"?el.options[el.selectedIndex].text:el.value.trim();
    if (!val) return;
    if (f.id==="word_count") { wordCountHint = "\n请将篇幅控制在"+val+"左右。\n"; prompt += f.label+"："+val+"\n"; }
    else if (f.id==="tone") { prompt += f.label+"：采用【"+val+"】的语言风格\n"; }
    else if (f.id==="perspective") { prompt += "写作视角：以【"+val+"】的角度撰写\n"; }
    else { prompt += f.label+"："+val+"\n"; }
  });
  prompt += wordCountHint + "\n要求：格式规范，内容完整，直接输出成文。";
  document.getElementById("editor").value = prompt;
  setLoading(true); addUserMsg("智能生成【"+currentTemplate.name+"】");
  try {
    const r = await fetch("/api/generate", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({prompt, version:currentVersion, template:currentTemplate.name}) });
    const data = await r.json();
    if (data.content) { document.getElementById("editor").value=data.content; addAssistantMsg("【"+currentTemplate.name+"】生成完成。"); await saveDoc(); }
    else if (data.error) addAssistantMsg("错误："+data.error);
  } catch(e) { addAssistantMsg("请求失败："+e.message); }
  setLoading(false);
}

// ======== 文档管理 ========
async function loadDocs() { try { const r=await fetch("/api/documents"); allDocs=await r.json(); renderDocList(); } catch(e){} }
function renderDocList() {
  const list = document.getElementById("docList");
  list.innerHTML = allDocs.map(d => '<div class="doc-item'+(d.id===currentDocId?" active":"")+'" onclick="openDoc(\''+d.id+'\')"><span class="doc-title-text">'+escapeHtml(d.title)+'</span><span class="doc-meta">'+formatTime(d.updated_at)+'</span></div>').join("");
}
async function newDoc() {
  try { const r=await fetch("/api/documents",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:"未命名文档",content:""})}); const d=await r.json(); if(d.id){currentDocId=d.id;document.getElementById("docTitle").value="未命名文档";document.getElementById("editor").value="";await loadDocs();} } catch(e){alert("新建失败:"+e.message);}
}
async function openDoc(id) { try { const r=await fetch("/api/documents/"+id); const d=await r.json(); if(d.error)return; currentDocId=d.id; document.getElementById("docTitle").value=d.title; document.getElementById("editor").value=d.content; renderDocList(); } catch(e){} }
async function saveDoc() { if(!currentDocId){await newDoc();} const title=document.getElementById("docTitle").value||"未命名文档"; const content=document.getElementById("editor").value; try { const r=await fetch("/api/documents/"+currentDocId+"/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title,content})}); const d=await r.json(); if(d.id){showToast("已保存");await loadDocs();} } catch(e){alert("保存失败:"+e.message);} }
async function deleteDoc() { if(!currentDocId)return; if(!confirm("确定删除此文档？"))return; try { await fetch("/api/documents/"+currentDocId+"/delete",{method:"POST"}); currentDocId=null; document.getElementById("docTitle").value="未命名文档"; document.getElementById("editor").value="";await loadDocs(); } catch(e){alert("删除失败:"+e.message);} }

// ======== AI 功能 ========
async function aiGenerate() {
  const prompt = document.getElementById("editor").value.trim();
  if (!prompt) { addSystemMsg("请先在编辑区输入写作需求。"); return; }
  setLoading(true); addUserMsg("生成文章："+prompt.substring(0,100));
  try { const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt,version:currentVersion})}); const d=await r.json(); if(d.content){document.getElementById("editor").value=d.content;addAssistantMsg("文章生成完成。");await saveDoc();}else if(d.error)addAssistantMsg("错误："+d.error); } catch(e){addAssistantMsg("请求失败："+e.message);}
  setLoading(false);
}
async function aiContinue() {
  const content=document.getElementById("editor").value.trim(); if(!content){addSystemMsg("请先写一些内容。");return;}
  setLoading(true); addUserMsg("续写当前内容...");
  try { const r=await fetch("/api/continue",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:content.substring(0,3000)})}); const d=await r.json(); if(d.content){document.getElementById("editor").value+="\n\n"+d.content;addAssistantMsg("续写完成。");await saveDoc();}else if(d.error)addAssistantMsg("错误："+d.error); } catch(e){addAssistantMsg("请求失败："+e.message);}
  setLoading(false);
}
async function aiRewrite() {
  const content=document.getElementById("editor").value.trim(); if(!content){addSystemMsg("请先写一些内容。");return;}
  const style=prompt("请输入改写要求","更通顺流畅"); if(!style)return;
  setLoading(true); addUserMsg("改写："+style);
  try { const r=await fetch("/api/rewrite",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:content.substring(0,3000),style})}); const d=await r.json(); if(d.content){document.getElementById("editor").value=d.content;addAssistantMsg("改写完成。");await saveDoc();}else if(d.error)addAssistantMsg("错误："+d.error); } catch(e){addAssistantMsg("请求失败："+e.message);}
  setLoading(false);
}
async function aiChat() {
  const input=document.getElementById("aiInput"); const text=input.value.trim(); if(!text)return; input.value=""; addUserMsg(text); setLoading(true);
  const content=document.getElementById("editor").value.trim();
  const messages=[{role:"system",content:"你是一个专业的写作助手。"}];
  if(content) messages.push({role:"user",content:"当前正在写的文章：\n"+content.substring(0,1000)});
  messages.push({role:"user",content:text});
  try { const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages})}); const d=await r.json(); if(d.reply)addAssistantMsg(d.reply);else if(d.error)addAssistantMsg("错误："+d.error); } catch(e){addAssistantMsg("请求失败："+e.message);}
  setLoading(false);
}

// ======== 导出 ========
async function doExport(format, style) {
  const title=document.getElementById("docTitle").value||"未命名"; const content=document.getElementById("editor").value;
  if(!content){alert("没有内容可导出");return;}
  const body={title,content,format}; if(style)body.style=style;
  try {
    const r=await fetch("/api/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); const d=await r.json();
    if(format==="docx"||format==="pdf"){ if(d.download_url){window.open(d.download_url,"_blank");}else if(d.error)alert(d.error); }
    else if(d.content){ document.getElementById("exportContent").value=d.content; document.getElementById("exportResult").style.display="block";
      if(format==="wechat"){document.getElementById("exportPreview").srcdoc=d.content;document.getElementById("exportPreviewWrap").style.display="block";document.getElementById("exportContent").style.display="none";}
      else{document.getElementById("exportPreviewWrap").style.display="none";document.getElementById("exportContent").style.display="block";}
    }else if(d.error)alert("导出失败:"+d.error);
  }catch(e){alert("导出失败:"+e.message);}
}
function showWechatStyle(){document.getElementById("exportResult").style.display="none";document.getElementById("wechatStylePanel").style.display="block";}
function showExport(){document.getElementById("exportResult").style.display="none";document.getElementById("wechatStylePanel").style.display="none";document.getElementById("exportModal").style.display="flex";}
function closeExport(){document.getElementById("exportModal").style.display="none";}
function copyExport(){const el=document.getElementById("exportContent");el.select();document.execCommand("copy");showToast("已复制到剪贴板");}
function searchDocs(){const q=document.getElementById("searchInput").value.trim();if(!q){loadDocs();return;}fetch("/api/search?q="+encodeURIComponent(q)).then(r=>r.json()).then(d=>{allDocs=d;renderDocList();}).catch(()=>{});}

// ======== 预览 ========
function previewDoc(){const t=document.getElementById("docTitle").value||"未命名";const c=document.getElementById("editor").value;document.getElementById("previewContent").innerHTML="<h2>"+escapeHtml(t)+"</h2><hr>"+c.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");document.getElementById("previewModal").style.display="flex";}
function closePreview(){document.getElementById("previewModal").style.display="none";}

// ======== 设置 ========
function showSettings(){document.getElementById("settingsModal").style.display="flex";fetch("/api/config").then(r=>r.json()).then(d=>{document.getElementById("engineSelect").value=d.engine;document.getElementById("deepseekApiKey").value=d.deepseek_api_key||"";document.getElementById("deepseekModel").value=d.deepseek_model||"";document.getElementById("greenapiApiKey").value=d.greenapi_api_key||"";document.getElementById("greenapiModel").value=d.greenapi_model||"";document.getElementById("greenapiBaseUrl").value=d.greenapi_base_url||"";document.getElementById("ollamaModel").value=d.ollama_model||"";document.getElementById("customBaseUrl").value=d.custom_base_url||"";document.getElementById("customApiKey").value=d.custom_api_key||"";document.getElementById("customModel").value=d.custom_model||"";onEngineChange();}).catch(()=>{});fetch("/api/local-status").then(r=>r.json()).then(d=>{var s=document.getElementById("localModelStatus");if(s)s.innerHTML=(d.available?"模型: "+d.model_name+"<br>运行: "+(d.running?"✅ 已启动":"❌ 未启动"):"未检测到模型文件 (放入 _models/)")+"<br><span style='font-size:11px;color:var(--text-dim);'>端口: "+d.port+"</span>";}).catch(()=>{});}
function onEngineChange(){const e=document.getElementById("engineSelect").value;document.querySelectorAll(".engine-fields").forEach(el=>el.style.display="none");const m={deepseek:"fieldsDeepseek",greenapi:"fieldsGreenapi",ollama:"fieldsOllama",custom:"fieldsCustom",local:"fieldsLocal"};const t=document.getElementById(m[e]);if(t)t.style.display="block";}
function closeSettings(){document.getElementById("settingsModal").style.display="none";}
async function saveSettings(){const e=document.getElementById("engineSelect").value;const b={engine:e};if(e==="deepseek"){b.api_key=document.getElementById("deepseekApiKey").value.trim();b.model=document.getElementById("deepseekModel").value.trim();}else if(e==="greenapi"){b.base_url=document.getElementById("greenapiBaseUrl").value.trim();b.api_key=document.getElementById("greenapiApiKey").value.trim();b.model=document.getElementById("greenapiModel").value.trim();}else if(e==="ollama")b.model=document.getElementById("ollamaModel").value.trim();else if(e==="custom"){b.base_url=document.getElementById("customBaseUrl").value.trim();b.api_key=document.getElementById("customApiKey").value.trim();b.model=document.getElementById("customModel").value.trim();}try{const r=await fetch("/api/switch-engine",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});const d=await r.json();if(d.ok){document.getElementById("engineStatus").textContent="引擎: "+e;showToast("已切换到: "+e);closeSettings();}else if(d.error)alert(d.error);}catch(er){alert("切换失败:"+er.message);}}

// ======== 升级 ========
let upgradeData=null;
function showUpgrade(){document.getElementById("upgradeModal").style.display="flex";document.getElementById("upgHasUpdate").style.display="none";document.getElementById("upgNoUpdate").style.display="block";document.getElementById("upgCheckBtn").style.display="";document.getElementById("upgApplyBtn").style.display="none";document.getElementById("upgConfirm").checked=false;document.getElementById("upgProgress").style.display="none";upgradeData=null;fetch("/api/version").then(r=>r.json()).then(d=>{document.getElementById("upgCurrent").textContent="v"+d.version;}).catch(()=>{});}
function closeUpgrade(){document.getElementById("upgradeModal").style.display="none";}
async function checkUpdate(){const btn=document.getElementById("upgCheckBtn");btn.innerHTML='<span class="spinner"></span>检查中...';btn.disabled=true;try{const r=await fetch("/api/check-update");const d=await r.json();if(d.has_update){upgradeData=d;document.getElementById("upgLatest").textContent="v"+d.latest;document.getElementById("upgChangelog").textContent=d.changelog||"";document.getElementById("upgHasUpdate").style.display="block";document.getElementById("upgNoUpdate").style.display="none";document.getElementById("upgCheckBtn").style.display="none";document.getElementById("upgApplyBtn").style.display="";}else{document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--green);">✅ '+(d.message||"已是最新版本")+'</p>';}}catch(e){document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--red);">❌ 检查失败</p>';}btn.innerHTML="🔍 检查更新";btn.disabled=false;}
function toggleUpgradeBtn(){const b=document.getElementById("upgApplyBtn");const c=document.getElementById("upgConfirm").checked;b.disabled=!c;b.style.opacity=c?"1":"0.4";}
async function doUpgrade(){if(!upgradeData||!upgradeData.download_url)return;document.getElementById("upgProgress").style.display="block";document.getElementById("upgApplyBtn").disabled=true;document.getElementById("upgConfirm").disabled=true;const bar=document.getElementById("upgBar");const st=document.getElementById("upgStatus");st.textContent="正在下载...";bar.style.width="30%";try{const r=await fetch("/api/apply-update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({download_url:upgradeData.download_url})});const d=await r.json();if(d.ok){bar.style.width="100%";st.textContent=d.message;st.style.color="var(--green)";document.getElementById("upgHasUpdate").style.display="none";document.getElementById("upgNoUpdate").style.display="block";document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--green);">✅ 升级完成！请重启写作台</p>';}else{bar.style.width="0";st.textContent="升级失败: "+(d.error||"未知错误");st.style.color="var(--red)";}}catch(e){bar.style.width="0";st.textContent="升级失败: "+e.message;st.style.color="var(--red)";}}

// ======== AI 面板 ========
function toggleAIPanel(){const b=document.getElementById("aiPanelBody");const s=document.getElementById("aiPanel");const btn=document.getElementById("aiToggleBtn");if(b.style.display==="none"){b.style.display="flex";s.style.width="360px";s.style.minWidth="";btn.innerHTML="收起 ▲";}else{b.style.display="none";s.style.width="40px";s.style.minWidth="40px";btn.innerHTML="展开 ▼";}}
function addUserMsg(text){const m=document.getElementById("aiMessages");m.innerHTML+='<div class="ai-msg user"><span class="msg-label">你</span>'+escapeHtml(text)+'</div>';m.scrollTop=m.scrollHeight;}
function addAssistantMsg(text){const m=document.getElementById("aiMessages");m.innerHTML+='<div class="ai-msg assistant"><span class="msg-label">AI</span>'+escapeHtml(text)+'</div>';m.scrollTop=m.scrollHeight;}
function addSystemMsg(text){const m=document.getElementById("aiMessages");m.innerHTML+='<div class="ai-msg" style="background:transparent;text-align:center;color:var(--text-dim);font-size:12px;">'+escapeHtml(text)+'</div>';m.scrollTop=m.scrollHeight;}

// ======== 工具 ========
function setLoading(loading){document.querySelectorAll(".editor-actions .btn,.ai-input-row .btn-primary").forEach(b=>b.disabled=loading);const gb=document.querySelectorAll(".editor-actions .btn-primary")[0];if(gb)gb.innerHTML=loading?'<span class="spinner"></span>AI 生成中...':"🤖 AI 生成";}
function escapeHtml(text){const div=document.createElement("div");div.textContent=text;return div.innerHTML;}
function formatTime(iso){if(!iso)return"";const d=new Date(iso);return d.toLocaleString("zh-CN",{month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});}
function showToast(msg){const el=document.createElement("div");el.style.cssText="position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--accent);color:#fff;padding:8px 20px;border-radius:8px;font-size:14px;z-index:200;";el.textContent=msg;document.body.appendChild(el);setTimeout(()=>{el.style.opacity="0";setTimeout(()=>el.remove(),300);},2000);}
document.addEventListener("keydown",function(e){if((e.ctrlKey||e.metaKey)&&e.key==="s"){e.preventDefault();saveDoc();}});

// ======== 拖拽 ========
(function(){const W=150,X=500;let h=null,t=null,sx=0,sw=0;[{hid:"resizeLeft",tid:"sidebar"},{hid:"resizeRight",tid:"aiPanel"}].forEach(c=>{const el=document.getElementById(c.hid);if(!el)return;el.addEventListener("mousedown",function(e){e.preventDefault();h=el;t=document.getElementById(c.tid);t._minW=W;t._maxW=X;sx=e.clientX;sw=t.offsetWidth;h.classList.add("active");document.body.style.cursor="col-resize";document.body.style.userSelect="none";});});document.addEventListener("mousemove",function(e){if(!h||!t)return;const d=e.clientX-sx;let nw=(h.id==="resizeRight")?sw-d:sw+d;nw=Math.max(t._minW,Math.min(t._maxW,nw));t.style.width=nw+"px";t.style.minWidth=nw+"px";});document.addEventListener("mouseup",function(){if(h)h.classList.remove("active");h=null;t=null;document.body.style.cursor="";document.body.style.userSelect="";});})();

function fetchGreenModels(){const url=document.getElementById("greenapiBaseUrl").value.trim();const key=document.getElementById("greenapiApiKey").value.trim();if(!url||!key){alert("请先填写接口地址和API密钥");return;}fetch("/api/proxy-models?url="+encodeURIComponent(url)+"&key="+encodeURIComponent(key)).then(r=>r.json()).then(d=>{if(d.models&&d.models.length){var sel=document.getElementById("greenapiModel");sel.value="";var list=d.models.slice(0,50).map(function(m){return'<option value="'+m+'">'+m+'</option>';}).join("");sel.outerHTML='<select id="greenapiModel" class="wizard-field-input" style="width:100%;">'+list+'</select>';showToast("找到 "+d.models.length+" 个模型");}else{alert(d.error||"未找到模型");}}).catch(function(e){alert("请求失败: "+e.message);});}
function fetchCustomModels(){const url=document.getElementById("customBaseUrl").value.trim();const key=document.getElementById("customApiKey").value.trim();if(!url||!key){alert("请先填写接口地址和API密钥");return;}fetch("/api/proxy-models?url="+encodeURIComponent(url)+"&key="+encodeURIComponent(key)).then(r=>r.json()).then(d=>{if(d.models&&d.models.length){var sel=document.getElementById("customModel");sel.value="";var list=d.models.slice(0,50).map(function(m){return'<option value="'+m+'">'+m+'</option>';}).join("");sel.outerHTML='<select id="customModel" class="wizard-field-input" style="width:100%;">'+list+'</select>';showToast("找到 "+d.models.length+" 个模型");}else{alert(d.error||"未找到模型");}}).catch(function(e){alert("请求失败: "+e.message);});}