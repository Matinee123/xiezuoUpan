let currentDocId = null;
let allDocs = [];
let currentVersion = null;
let currentTemplate = null;

// ======== 初始化 ========
async function init() {
  await loadVersions();
  document.getElementById("homePage").style.display = "flex";
  document.getElementById("editorPage").style.display = "none";
}
init();

// ======== 版本选择 ========
async function loadVersions() {
  try {
    const r = await fetch("/api/versions");
    const data = await r.json();
    renderCards(data);
  } catch(e) {}
}

function renderCards(versions) {
  const grid = document.getElementById("cardGrid");
  grid.innerHTML = versions.map(v => 
    `<div class="version-card" onclick="switchVersion('${v.id}','${v.name}','${v.theme}')">
      <div class="card-icon">${v.icon}</div>
      <div class="card-name">${v.name}</div>
      <div class="card-desc">${v.desc}</div>
    </div>`
  ).join("");
}

function switchVersion(id, name, theme) {
  currentVersion = id;
  currentTemplate = null;
  document.getElementById("homePage").style.display = "none";
  document.getElementById("editorPage").style.display = "flex";
  document.getElementById("verTitle").textContent = name;
  document.getElementById("app").setAttribute("data-theme", id);
  loadVersionBadge();
  loadConfig();
  loadDocs();
  loadTemplates();
  switchSidebar("wizard");
  document.getElementById("aiMessages").innerHTML = "";
  addSystemMsg("欢迎使用" + name + "。选择左侧模板，填写信息后点「智能生成」。");
}

function goHome() {
  currentVersion = null;
  currentTemplate = null;
  document.getElementById("editorPage").style.display = "none";
  document.getElementById("homePage").style.display = "flex";
  document.getElementById("app").removeAttribute("data-theme");
}

// ======== 侧边栏切换 ========
function switchSidebar(tab) {
  document.getElementById("wizardPanel").style.display = (tab === "wizard") ? "block" : "none";
  document.getElementById("docsPanel").style.display = (tab === "docs") ? "flex" : "none";
  document.getElementById("tabWizard").classList.toggle("active", tab === "wizard");
  document.getElementById("tabDocs").classList.toggle("active", tab === "docs");
}

// ======== 写作向导 ========
async function loadTemplates() {
  try {
    const url = "/api/templates?v=" + (currentVersion || "general");
    const r = await fetch(url);
    const data = await r.json();
    const sel = document.getElementById("templateSelect");
    sel.innerHTML = '<option value="">自由写作</option>';
    data.forEach(t => {
      sel.innerHTML += `<option value="${t.name}">${t.name}</option>`;
    });
    onTemplateChange();
  } catch(e) {}
}

function onTemplateChange() {
  const name = document.getElementById("templateSelect").value;
  if (!name) {
    document.getElementById("wizardFields").innerHTML = "";
    document.getElementById("wizardGenerateBtn").style.display = "none";
    currentTemplate = null;
    return;
  }
  const url = "/api/template/" + encodeURIComponent(name) + "?v=" + (currentVersion || "general");
  fetch(url).then(r => r.json()).then(t => {
    if (t.fields) {
      currentTemplate = { name: name, fields: t.fields, example: t.example || null };
      renderFields(t.fields, t.example);
    } else {
      document.getElementById("wizardFields").innerHTML = "";
      document.getElementById("wizardGenerateBtn").style.display = "none";
    }
  }).catch(() => {
    document.getElementById("wizardFields").innerHTML = '<div class="wizard-field-hint" style="text-align:center;padding:20px;">加载失败，请重试</div>';
  });
}

function renderFields(fields, example) {
  const container = document.getElementById("wizardFields");
  let html = fields.map(f => {
    let inputHtml;
    if (f.type === 'select') {
      inputHtml = `<select class="wizard-field-input" id="wf_${f.id}">${f.options.map(o => `<option value="${o}">${o}</option>`).join('')}</select>`;
    } else if (f.id === 'body' || f.id === 'items' || f.id === 'points' || f.id === 'actions' || f.id === 'problems' || f.id === 'plan' || f.id === 'agenda' || f.id === 'decisions' || f.id === 'tasks' || f.id === 'requirements' || f.id === 'background' || f.id === 'reason' || f.id === 'content' || f.id === 'features' || f.id === 'rights' || f.id === 'understanding' || f.id === 'claims' || f.id === 'facts' || f.id === 'evidence' || f.id === 'defense_points' || f.id === 'counter_evidence' || f.id === 'demands' || f.id === 'analysis' || f.id === 'risks' || f.id === 'suggestions' || f.id === 'missing' || f.id === 'legal_analysis' || f.id === 'evidence_analysis' || f.id === 'rebuttal' || f.id === 'grounds' || f.id === 'errors' || f.id === 'evidence_groups' || f.id === 'evidence_items' || f.id === 'scope' || f.id === 'legal_basis' || f.id === 'opinion' || f.id === 'appeal_claims') {
      inputHtml = `<textarea class="wizard-field-input" id="wf_${f.id}" rows="3" placeholder="${f.hint || ''}"></textarea>`;
    } else {
      inputHtml = `<input type="text" class="wizard-field-input" id="wf_${f.id}" placeholder="${f.hint || ''}">`;
    }
    return `<div class="wizard-field">
      <label class="wizard-field-label">${f.label}${f.required ? '<span class="required">*</span>' : ''}</label>
      ${inputHtml}
      ${f.hint ? `<div class="wizard-field-hint">${f.hint}</div>` : ''}
    </div>`;
  }).join('');

  if (example) {
    html += `<div class="wizard-example" onclick="this.classList.toggle('open')">
      <div class="wizard-example-header">💡 参考范例（点击展开）</div>
      <div class="wizard-example-content">${example.replace(/\n/g,'<br>')}</div>
    </div>`;
  }

  container.innerHTML = html;
  document.getElementById("wizardGenerateBtn").style.display = "block";
}

async function aiGenerateWizard() {
  if (!currentTemplate) return;
  
  let prompt = `请根据以下信息撰写一份专业的【${currentTemplate.name}】：\n\n`;
  let wordCountHint = "";
  
  currentTemplate.fields.forEach(f => {
    const el = document.getElementById("wf_" + f.id);
    if (!el) return;
    const val = el.tagName === 'SELECT' ? el.options[el.selectedIndex].text : el.value.trim();
    if (!val) return;
    
    if (f.id === 'word_count') {
      wordCountHint = `\n请将篇幅控制在${val}左右。\n`;
      prompt += `${f.label}：${val}\n`;
    } else if (f.id === 'tone') {
      prompt += `${f.label}：采用【${val}】的语言风格\n`;
    } else if (f.id === 'perspective') {
      prompt += `写作视角：以【${val}】的角度撰写\n`;
    } else {
      prompt += `${f.label}：${val}\n`;
    }
  });
  
  prompt += wordCountHint;
  prompt += "\n要求：格式规范，内容完整，直接输出成文，不需要额外说明。";
  if (currentTemplate.name === '商务邮件') {
    prompt += "\n请包含邮件标准格式（称呼、正文、署名）。";
  }
  if (currentTemplate.name === '合同协议') {
    prompt += "\n请使用标准的合同条款格式，包含甲乙双方信息、逐条约定。";
  }

  document.getElementById("editor").value = prompt;
  
  setLoading(true);
  addUserMsg("智能生成【" + currentTemplate.name + "】");
  try {
    const body = { prompt, version: currentVersion, template: currentTemplate.name };
    const r = await fetch("/api/generate", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    const data = await r.json();
    if (data.content) {
      document.getElementById("editor").value = data.content;
      addAssistantMsg("【" + currentTemplate.name + "】生成完成。");
      await saveDoc();
    } else if (data.error) {
      addAssistantMsg("错误：" + data.error);
    }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

function apiGet(path) {
  if (currentVersion) {
    path += (path.includes("?") ? "&" : "?") + "v=" + currentVersion;
  }
  return fetch(path);
}

function apiPost(path, body) {
  if (currentVersion) body.version = currentVersion;
  return fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
}

// ======== 版本号 ========
async function loadVersionBadge() {
  try {
    const r = await fetch("/api/version");
    const data = await r.json();
    document.getElementById("verBadge").textContent = "v" + data.version;
  } catch(e) {}
}

// ======== 配置 ========
async function loadConfig() {
  try {
    const r = await fetch("/api/config");
    const data = await r.json();
    document.getElementById("engineStatus").textContent = "引擎: " + data.engine;
  } catch(e) {}
}

// ======== 文档管理 ========
async function loadDocs() {
  try {
    const r = await fetch("/api/documents");
    allDocs = await r.json();
    renderDocList();
  } catch(e) {}
}

function renderDocList() {
  const list = document.getElementById("docList");
  list.innerHTML = allDocs.map(d => 
    `<div class="doc-item ${d.id === currentDocId ? "active" : ""}" onclick="openDoc('${d.id}')">
      <span class="doc-title-text">${escapeHtml(d.title)}</span>
      <span class="doc-meta">${formatTime(d.updated_at)}</span>
    </div>`
  ).join("");
}

async function newDoc() {
  try {
    const r = await fetch("/api/documents", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({title:"未命名文档",content:""}) });
    const data = await r.json();
    if (data.id) { currentDocId = data.id; document.getElementById("docTitle").value = "未命名文档"; document.getElementById("editor").value = ""; await loadDocs(); }
  } catch(e) { alert("新建失败: " + e.message); }
}

async function openDoc(id) {
  try {
    const r = await fetch("/api/documents/" + id);
    const doc = await r.json();
    if (doc.error) return;
    currentDocId = doc.id; document.getElementById("docTitle").value = doc.title; document.getElementById("editor").value = doc.content; renderDocList();
  } catch(e) {}
}

async function saveDoc() {
  if (!currentDocId) { await newDoc(); }
  const title = document.getElementById("docTitle").value || "未命名文档";
  const content = document.getElementById("editor").value;
  try {
    const r = await fetch("/api/documents/" + currentDocId + "/save", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({title,content}) });
    const data = await r.json();
    if (data.id) { showToast("已保存"); await loadDocs(); }
  } catch(e) { alert("保存失败: " + e.message); }
}

async function deleteDoc() {
  if (!currentDocId) return;
  if (!confirm("确定删除此文档？")) return;
  try { await fetch("/api/documents/" + currentDocId + "/delete", {method:"POST"}); currentDocId = null; document.getElementById("docTitle").value = "未命名文档"; document.getElementById("editor").value = ""; await loadDocs(); } catch(e) { alert("删除失败: " + e.message); }
}

// ======== AI 功能 ========
async function aiGenerate() {
  const prompt = document.getElementById("editor").value.trim();
  if (!prompt) { addSystemMsg("请先在编辑区输入写作需求，或在 AI 对话中输入。"); return; }
  setLoading(true); addUserMsg("生成文章：" + prompt.substring(0, 100));
  try {
    const body = { prompt };
    if (currentVersion) body.version = currentVersion;
    const r = await fetch("/api/generate", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    const data = await r.json();
    if (data.content) { document.getElementById("editor").value = data.content; addAssistantMsg("文章生成完成。"); await saveDoc(); }
    else if (data.error) { addAssistantMsg("错误：" + data.error); }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

async function aiContinue() {
  const content = document.getElementById("editor").value.trim();
  if (!content) { addSystemMsg("请先写一些内容，再使用续写功能。"); return; }
  setLoading(true); addUserMsg("续写当前内容...");
  try {
    const r = await fetch("/api/continue", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({content:content.substring(0,3000)}) });
    const data = await r.json();
    if (data.content) { document.getElementById("editor").value += "\n\n" + data.content; addAssistantMsg("续写完成。"); await saveDoc(); }
    else if (data.error) { addAssistantMsg("错误：" + data.error); }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

async function aiRewrite() {
  const content = document.getElementById("editor").value.trim();
  if (!content) { addSystemMsg("请先写一些内容，再使用改写功能。"); return; }
  const style = prompt("请输入改写要求（如：更正式、更简洁、更生动等）", "更通顺流畅");
  if (!style) return;
  setLoading(true); addUserMsg("改写：" + style);
  try {
    const r = await fetch("/api/rewrite", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({content:content.substring(0,3000), style}) });
    const data = await r.json();
    if (data.content) { document.getElementById("editor").value = data.content; addAssistantMsg("改写完成。"); await saveDoc(); }
    else if (data.error) { addAssistantMsg("错误：" + data.error); }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

async function aiChat() {
  const input = document.getElementById("aiInput");
  const text = input.value.trim();
  if (!text) return;
  input.value = ""; addUserMsg(text); setLoading(true);
  const content = document.getElementById("editor").value.trim();
  const messages = [{role:"system",content:"你是一个专业的写作助手。请根据用户的需求提供写作建议、修改意见或直接撰写内容。"}];
  if (content) messages.push({role:"user",content:"当前正在写的文章：\n" + content.substring(0,1000)});
  messages.push({role:"user",content:text});
  try {
    const r = await fetch("/api/chat", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({messages}) });
    const data = await r.json();
    if (data.reply) addAssistantMsg(data.reply);
    else if (data.error) addAssistantMsg("错误：" + data.error);
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

// ======== 导出 ========
async function doExport(format, style) {
  const title = document.getElementById("docTitle").value || "未命名";
  const content = document.getElementById("editor").value;
  if (!content) { alert("没有内容可导出"); return; }
  const body = { title, content, format };
  if (style) body.style = style;
  try {
    const r = await fetch("/api/export", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    const data = await r.json();
    if (data.content) {
      document.getElementById("exportContent").value = data.content;
      document.getElementById("exportResult").style.display = "block";
      if (format === 'wechat') {
        var iframe = document.getElementById("exportPreview");
        iframe.srcdoc = data.content;
        document.getElementById("exportPreviewWrap").style.display = "block";
        document.getElementById("exportContent").style.display = "none";
      } else {
        document.getElementById("exportPreviewWrap").style.display = "none";
        document.getElementById("exportContent").style.display = "block";
      }
    } else if (data.error) alert("导出失败: " + data.error);
  } catch(e) { alert("导出失败: " + e.message); }
}

function showWechatStyle() {
  document.getElementById("exportResult").style.display = "none";
  document.getElementById("wechatStylePanel").style.display = "block";
}

function copyExport() { const el = document.getElementById("exportContent"); el.select(); document.execCommand("copy"); showToast("已复制到剪贴板"); }

// ======== 设置 ========
function showSettings() {
  document.getElementById("settingsModal").style.display = "flex";
  fetch("/api/config").then(r=>r.json()).then(data => {
    document.getElementById("engineSelect").value = data.engine;
    document.getElementById("deepseekApiKey").value = data.deepseek_api_key || "";
    document.getElementById("greenapiApiKey").value = data.greenapi_api_key || "";
    document.getElementById("ollamaModel").value = data.ollama_model || "";
    document.getElementById("customBaseUrl").value = data.custom_base_url || "";
    document.getElementById("customApiKey").value = data.custom_api_key || "";
    document.getElementById("customModel").value = data.custom_model || "";
    onEngineChange();
  }).catch(()=>{});
}

function onEngineChange() {
  const engine = document.getElementById("engineSelect").value;
  document.querySelectorAll(".engine-fields").forEach(el => el.style.display = "none");
  const map = { deepseek:"fieldsDeepseek", greenapi:"fieldsGreenapi", ollama:"fieldsOllama", custom:"fieldsCustom" };
  const target = document.getElementById(map[engine]);
  if (target) target.style.display = "block";
}

function closeSettings() { document.getElementById("settingsModal").style.display = "none"; }

async function saveSettings() {
  const engine = document.getElementById("engineSelect").value;
  const body = { engine };
  if (engine==="deepseek") body.api_key = document.getElementById("deepseekApiKey").value.trim();
  else if (engine==="greenapi") body.api_key = document.getElementById("greenapiApiKey").value.trim();
  else if (engine==="ollama") body.model = document.getElementById("ollamaModel").value.trim();
  else if (engine==="custom") {
    body.base_url = document.getElementById("customBaseUrl").value.trim();
    body.api_key = document.getElementById("customApiKey").value.trim();
    body.model = document.getElementById("customModel").value.trim();
  }
  try {
    const r = await fetch("/api/switch-engine", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    const data = await r.json();
    if (data.ok) { document.getElementById("engineStatus").textContent = "引擎: " + engine; showToast("已切换到: " + engine); closeSettings(); }
    else if (data.error) alert(data.error);
  } catch(e) { alert("切换失败: " + e.message); }
}

function showExport() { document.getElementById("exportResult").style.display = "none"; document.getElementById("wechatStylePanel").style.display = "none"; document.getElementById("exportModal").style.display = "flex"; }
function closeExport() { document.getElementById("exportModal").style.display = "none"; }

// ======== 预览弹窗 ========
function previewDoc() {
  const title = document.getElementById("docTitle").value || "未命名";
  const text = document.getElementById("editor").value;
  const pc = document.getElementById("previewContent");
  pc.innerHTML = "<h2>" + escapeHtml(title) + "</h2><hr>" + text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");
  document.getElementById("previewModal").style.display = "flex";
}
function closePreview() { document.getElementById("previewModal").style.display = "none"; }

// ======== AI 面板 ========
function toggleAIPanel() {
  const body = document.getElementById("aiPanelBody");
  const sidebar = document.getElementById("aiPanel");
  const btn = document.getElementById("aiToggleBtn");
  if (body.style.display === "none") {
    body.style.display = "flex"; sidebar.style.width = "360px"; sidebar.style.minWidth = ""; btn.innerHTML = "收起 ▲";
  } else {
    body.style.display = "none"; sidebar.style.width = "40px"; sidebar.style.minWidth = "40px"; btn.innerHTML = "展开 ▼";
  }
}

function addUserMsg(text) { const msgs = document.getElementById("aiMessages"); msgs.innerHTML += '<div class="ai-msg user"><span class="msg-label">你</span>'+escapeHtml(text)+'</div>'; msgs.scrollTop = msgs.scrollHeight; }
function addAssistantMsg(text) { const msgs = document.getElementById("aiMessages"); msgs.innerHTML += '<div class="ai-msg assistant"><span class="msg-label">AI</span>'+escapeHtml(text)+'</div>'; msgs.scrollTop = msgs.scrollHeight; }
function addSystemMsg(text) { const msgs = document.getElementById("aiMessages"); msgs.innerHTML += '<div class="ai-msg" style="background:transparent;text-align:center;color:var(--text-dim);font-size:12px;">'+escapeHtml(text)+'</div>'; msgs.scrollTop = msgs.scrollHeight; }

// ======== 工具函数 ========
function setLoading(loading) {
  const btns = document.querySelectorAll(".editor-actions .btn, .ai-input-row .btn-primary");
  btns.forEach(b => b.disabled = loading);
  const genBtn = document.querySelectorAll(".editor-actions .btn-primary")[0];
  if (genBtn) genBtn.innerHTML = loading ? '<span class="spinner"></span>AI 生成中...' : '🤖 AI 生成';
}

function escapeHtml(text) { const div = document.createElement("div"); div.textContent = text; return div.innerHTML; }
function formatTime(iso) { if (!iso) return ""; const d = new Date(iso); return d.toLocaleString("zh-CN",{month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}); }

function showToast(msg) {
  const el = document.createElement("div");
  el.style.cssText = "position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--accent);color:#fff;padding:8px 20px;border-radius:8px;font-size:14px;z-index:200;transition:opacity 0.3s;";
  el.textContent = msg; document.body.appendChild(el);
  setTimeout(()=>{ el.style.opacity="0"; setTimeout(()=>el.remove(),300); }, 2000);
}

// ======== 系统升级 ========
let upgradeData = null;

function showUpgrade() {
  document.getElementById("upgradeModal").style.display = "flex";
  document.getElementById("upgCurrent").textContent = "v1.0.0";
  document.getElementById("upgHasUpdate").style.display = "none";
  document.getElementById("upgNoUpdate").style.display = "block";
  document.getElementById("upgCheckBtn").style.display = "";
  document.getElementById("upgApplyBtn").style.display = "none";
  document.getElementById("upgConfirm").checked = false;
  document.getElementById("upgProgress").style.display = "none";
  upgradeData = null;
  fetch("/api/version").then(r=>r.json()).then(d => {
    document.getElementById("upgCurrent").textContent = "v" + d.version;
  }).catch(()=>{});
}

function closeUpgrade() { document.getElementById("upgradeModal").style.display = "none"; }

async function checkUpdate() {
  var btn = document.getElementById("upgCheckBtn");
  btn.innerHTML = '<span class="spinner"></span> 检查中...';
  btn.disabled = true;
  try {
    var r = await fetch("/api/check-update");
    var d = await r.json();
    if (d.has_update) {
      upgradeData = d;
      document.getElementById("upgLatest").textContent = "v" + d.latest;
      document.getElementById("upgChangelog").textContent = d.changelog || "";
      document.getElementById("upgHasUpdate").style.display = "block";
      document.getElementById("upgNoUpdate").style.display = "none";
      document.getElementById("upgCheckBtn").style.display = "none";
      document.getElementById("upgApplyBtn").style.display = "";
    } else {
      document.getElementById("upgNoUpdate").style.display = "block";
      document.getElementById("upgHasUpdate").style.display = "none";
      document.getElementById("upgNoUpdate").innerHTML = '<p style="color:var(--green);font-size:15px;">✅ ' + (d.message || '已是最新版本') + '</p>';
    }
  } catch(e) {
    document.getElementById("upgNoUpdate").innerHTML = '<p style="color:var(--red);font-size:14px;">❌ 检查失败，请确保有网络连接</p>';
    document.getElementById("upgNoUpdate").style.display = "block";
  }
  btn.innerHTML = '🔍 检查更新';
  btn.disabled = false;
}

function toggleUpgradeBtn() {
  var btn = document.getElementById("upgApplyBtn");
  var checked = document.getElementById("upgConfirm").checked;
  btn.disabled = !checked;
  btn.style.opacity = checked ? "1" : "0.4";
}

async function doUpgrade() {
  if (!upgradeData || !upgradeData.download_url) return;
  document.getElementById("upgProgress").style.display = "block";
  document.getElementById("upgApplyBtn").disabled = true;
  document.getElementById("upgConfirm").disabled = true;
  
  var bar = document.getElementById("upgBar");
  var status = document.getElementById("upgStatus");
  status.textContent = "正在下载更新...";
  bar.style.width = "30%";
  
  try {
    var r = await fetch("/api/apply-update", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({download_url: upgradeData.download_url}) });
    var d = await r.json();
    if (d.ok) {
      bar.style.width = "100%";
      status.textContent = d.message;
      status.style.color = "var(--green)";
      document.getElementById("upgHasUpdate").style.display = "none";
      document.getElementById("upgNoUpdate").style.display = "block";
      document.getElementById("upgNoUpdate").innerHTML = '<p style="color:var(--green);font-size:15px;">✅ 升级完成！</p><p style="font-size:13px;color:var(--text-dim);">请重启写作台以应用更新</p>';
    } else {
      bar.style.width = "0";
      status.textContent = "升级失败: " + (d.error || "未知错误");
      status.style.color = "var(--red)";
    }
  } catch(e) {
    bar.style.width = "0";
    status.textContent = "升级失败: " + e.message;
    status.style.color = "var(--red)";
  }
}
document.addEventListener("keydown", function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveDoc(); }
});

// ======== 面板拖拽调整宽度 ========
(function() {
  const MIN_W = 150, MAX_W = 500;
  let dragHandle = null, dragTarget = null, startX = 0, startW = 0;
  const configs = [
    { handleId:"resizeLeft", targetId:"sidebar", maxW:MAX_W, minW:MIN_W },
    { handleId:"resizeRight", targetId:"aiPanel", maxW:MAX_W, minW:MIN_W },
  ];
  configs.forEach(cfg => {
    const h = document.getElementById(cfg.handleId);
    if (!h) return;
    h.addEventListener("mousedown", function(e) {
      e.preventDefault(); dragHandle = h; dragTarget = document.getElementById(cfg.targetId);
      dragTarget._minW = cfg.minW; dragTarget._maxW = cfg.maxW;
      startX = e.clientX; startW = dragTarget.offsetWidth;
      dragHandle.classList.add("active"); document.body.style.cursor = "col-resize"; document.body.style.userSelect = "none";
    });
  });
  document.addEventListener("mousemove", function(e) {
    if (!dragHandle || !dragTarget) return;
    const delta = e.clientX - startX;
    let newW = (dragHandle.id === "resizeRight") ? startW - delta : startW + delta;
    newW = Math.max(dragTarget._minW, Math.min(dragTarget._maxW, newW));
    dragTarget.style.width = newW + "px"; dragTarget.style.minWidth = newW + "px";
  });
  document.addEventListener("mouseup", function() {
    if (dragHandle) dragHandle.classList.remove("active");
    dragHandle = null; dragTarget = null; document.body.style.cursor = ""; document.body.style.userSelect = "";
  });
})();