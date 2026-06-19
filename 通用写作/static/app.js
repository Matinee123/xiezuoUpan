let currentDocId = null;
let allDocs = [];

// ======== 初始化 ========
async function init() {
  await loadVersion();
  await loadDocs();
  await loadConfig();
  setupAutoPreview();
  addSystemMsg("欢迎使用 AI 写作工作台。在左侧新建文档，或在下方输入写作指令。");
}
init();

// ======== 版本号 ========
async function loadVersion() {
  try {
    const r = await fetch("/api/version");
    const data = await r.json();
    document.getElementById("versionBadge").textContent = "v" + data.version;
  } catch(e) {}
}

// ======== 配置 ========
async function loadConfig() {
  try {
    const r = await fetch("/api/config");
    const data = await r.json();
    document.getElementById("engineStatus").textContent = "引擎: " + data.engine;
    document.getElementById("engineSelect").value = data.engine;
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
  list.innerHTML = allDocs.map(d => `
    <div class="doc-item ${d.id === currentDocId ? 'active' : ''}" onclick="openDoc('${d.id}')">
      <span class="doc-title-text">${escapeHtml(d.title)}</span>
      <span class="doc-meta">${formatTime(d.updated_at)}</span>
    </div>
  `).join("");
}

async function newDoc() {
  try {
    const r = await fetch("/api/documents", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title: "未命名文档", content: ""})
    });
    const data = await r.json();
    if (data.id) {
      currentDocId = data.id;
      document.getElementById("docTitle").value = "未命名文档";
      document.getElementById("editor").value = "";
      updatePreview();
      await loadDocs();
    }
  } catch(e) { alert("新建失败: " + e.message); }
}

async function openDoc(id) {
  try {
    const r = await fetch("/api/documents/" + id);
    const doc = await r.json();
    if (doc.error) return;
    currentDocId = doc.id;
    document.getElementById("docTitle").value = doc.title;
    document.getElementById("editor").value = doc.content;
    updatePreview();
    renderDocList();
  } catch(e) {}
}

async function saveDoc() {
  if (!currentDocId) { await newDoc(); }
  const title = document.getElementById("docTitle").value || "未命名文档";
  const content = document.getElementById("editor").value;
  try {
    const r = await fetch("/api/documents/" + currentDocId + "/save", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title, content})
    });
    const data = await r.json();
    if (data.id) {
      showToast("已保存");
      await loadDocs();
    }
  } catch(e) { alert("保存失败: " + e.message); }
}

async function deleteDoc() {
  if (!currentDocId) return;
  if (!confirm("确定删除此文档？")) return;
  try {
    await fetch("/api/documents/" + currentDocId + "/delete", {method: "POST"});
    currentDocId = null;
    document.getElementById("docTitle").value = "未命名文档";
    document.getElementById("editor").value = "";
    updatePreview();
    await loadDocs();
  } catch(e) { alert("删除失败: " + e.message); }
}

// ======== AI 功能 ========
async function aiGenerate() {
  const prompt = document.getElementById("editor").value.trim();
  if (!prompt) {
    addSystemMsg("请先在编辑区输入写作需求，或在下方的 AI 对话中输入。");
    return;
  }
  setLoading(true);
  addUserMsg("生成文章：" + prompt.substring(0, 100));
  try {
    const r = await fetch("/api/generate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt})
    });
    const data = await r.json();
    if (data.content) {
      document.getElementById("editor").value = data.content;
      updatePreview();
      addAssistantMsg("文章生成完成。");
      await saveDoc();
    } else if (data.error) {
      addAssistantMsg("错误：" + data.error);
    }
  } catch(e) {
    addAssistantMsg("请求失败：" + e.message);
  }
  setLoading(false);
}

async function aiContinue() {
  const content = document.getElementById("editor").value.trim();
  if (!content) { addSystemMsg("请先写一些内容，再使用续写功能。"); return; }
  setLoading(true);
  addUserMsg("续写当前内容...");
  try {
    const r = await fetch("/api/continue", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({content: content.substring(0, 3000)})
    });
    const data = await r.json();
    if (data.content) {
      document.getElementById("editor").value += "\n\n" + data.content;
      updatePreview();
      addAssistantMsg("续写完成。");
      await saveDoc();
    } else if (data.error) {
      addAssistantMsg("错误：" + data.error);
    }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

async function aiRewrite() {
  const content = document.getElementById("editor").value.trim();
  if (!content) { addSystemMsg("请先写一些内容，再使用改写功能。"); return; }
  const style = prompt("请输入改写要求（如：更正式、更简洁、更生动等）", "更通顺流畅");
  if (!style) return;
  setLoading(true);
  addUserMsg("改写：" + style);
  try {
    const r = await fetch("/api/rewrite", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({content: content.substring(0, 3000), style})
    });
    const data = await r.json();
    if (data.content) {
      document.getElementById("editor").value = data.content;
      updatePreview();
      addAssistantMsg("改写完成。");
      await saveDoc();
    } else if (data.error) {
      addAssistantMsg("错误：" + data.error);
    }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

async function aiChat() {
  const input = document.getElementById("aiInput");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  addUserMsg(text);
  setLoading(true);
  const content = document.getElementById("editor").value.trim();
  const messages = [
    {role: "system", content: "你是一个专业的写作助手。请根据用户的需求提供写作建议、修改意见或直接撰写内容。"}
  ];
  if (content) {
    messages.push({role: "user", content: `当前正在写的文章：\n${content.substring(0, 1000)}`});
  }
  messages.push({role: "user", content: text});
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({messages})
    });
    const data = await r.json();
    if (data.reply) {
      addAssistantMsg(data.reply);
    } else if (data.error) {
      addAssistantMsg("错误：" + data.error);
    }
  } catch(e) { addAssistantMsg("请求失败：" + e.message); }
  setLoading(false);
}

// ======== 导出 ========
async function doExport(format) {
  const title = document.getElementById("docTitle").value || "未命名";
  const content = document.getElementById("editor").value;
  if (!content) { alert("没有内容可导出"); return; }
  try {
    const r = await fetch("/api/export", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title, content, format})
    });
    const data = await r.json();
    if (data.content) {
      document.getElementById("exportContent").value = data.content;
      document.getElementById("exportResult").style.display = "block";
    } else if (data.error) {
      alert("导出失败: " + data.error);
    }
  } catch(e) { alert("导出失败: " + e.message); }
}

function copyExport() {
  const el = document.getElementById("exportContent");
  el.select();
  document.execCommand("copy");
  showToast("已复制到剪贴板");
}

// ======== 设置 ========
function showSettings() {
  document.getElementById("settingsModal").style.display = "flex";
}
function closeSettings() {
  document.getElementById("settingsModal").style.display = "none";
}

async function saveSettings() {
  const engine = document.getElementById("engineSelect").value;
  try {
    const r = await fetch("/api/switch-engine", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({engine})
    });
    const data = await r.json();
    if (data.ok) {
      document.getElementById("engineStatus").textContent = "引擎: " + engine;
      showToast("已切换到: " + engine);
      closeSettings();
    }
  } catch(e) { alert("切换失败: " + e.message); }
}

function showExport() {
  document.getElementById("exportResult").style.display = "none";
  document.getElementById("exportModal").style.display = "flex";
}

function closeExport() {
  document.getElementById("exportModal").style.display = "none";
}

// ======== 预览 ========
function updatePreview() {
  const text = document.getElementById("editor").value;
  const preview = document.getElementById("preview");
  preview.innerHTML = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");
}

function setupAutoPreview() {
  document.getElementById("editor").addEventListener("input", updatePreview);
}

// ======== AI 面板 ========
function toggleAIPanel() {
  const panel = document.getElementById("aiPanel");
  if (panel.style.display === "none") {
    panel.style.display = "flex";
  } else {
    panel.style.display = "none";
  }
}

function addUserMsg(text) {
  const msgs = document.getElementById("aiMessages");
  msgs.innerHTML += `<div class="ai-msg user"><span class="msg-label">你</span>${escapeHtml(text)}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
}

function addAssistantMsg(text) {
  const msgs = document.getElementById("aiMessages");
  msgs.innerHTML += `<div class="ai-msg assistant"><span class="msg-label">AI</span>${escapeHtml(text)}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
}

function addSystemMsg(text) {
  const msgs = document.getElementById("aiMessages");
  msgs.innerHTML += `<div class="ai-msg" style="background:transparent;text-align:center;color:var(--text-dim);font-size:12px;">${escapeHtml(text)}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
}

// ======== 工具函数 ========
function setLoading(loading) {
  const btns = document.querySelectorAll(".editor-actions .btn, .ai-input-row .btn-primary");
  btns.forEach(b => b.disabled = loading);
  document.querySelectorAll(".editor-actions .btn-primary")[0].innerHTML = loading ? '<span class="spinner"></span>AI 生成中...' : '🤖 AI 生成';
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("zh-CN", {month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"});
}

function showToast(msg) {
  const el = document.createElement("div");
  el.style.cssText = "position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--accent);color:#fff;padding:8px 20px;border-radius:8px;font-size:14px;z-index:200;transition:opacity 0.3s;";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 2000);
}

// ======== 升级 ========
let upgradeData = null;
function showUpgrade(){document.getElementById("upgradeModal").style.display="flex";document.getElementById("upgHasUpdate").style.display="none";document.getElementById("upgNoUpdate").style.display="block";document.getElementById("upgCheckBtn").style.display="";document.getElementById("upgApplyBtn").style.display="none";document.getElementById("upgConfirm").checked=false;document.getElementById("upgProgress").style.display="none";upgradeData=null;fetch("/api/version").then(r=>r.json()).then(d=>{document.getElementById("upgCurrent").textContent="v"+d.version;}).catch(()=>{});}
function closeUpgrade(){document.getElementById("upgradeModal").style.display="none";}
async function checkUpdate(){var btn=document.getElementById("upgCheckBtn");btn.innerHTML='<span class="spinner"></span>检查中...';btn.disabled=true;try{var r=await fetch("/api/check-update");var d=await r.json();if(d.has_update){upgradeData=d;document.getElementById("upgLatest").textContent="v"+d.latest;document.getElementById("upgChangelog").textContent=d.changelog||"";document.getElementById("upgHasUpdate").style.display="block";document.getElementById("upgNoUpdate").style.display="none";document.getElementById("upgCheckBtn").style.display="none";document.getElementById("upgApplyBtn").style.display="";}else{document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--green);">✅ '+(d.message||"已是最新版本")+'</p>';}}catch(e){document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--red);">❌ 检查失败</p>';}btn.innerHTML="🔍 检查更新";btn.disabled=false;}
function toggleUpgradeBtn(){var b=document.getElementById("upgApplyBtn");var c=document.getElementById("upgConfirm").checked;b.disabled=!c;b.style.opacity=c?"1":"0.4";}
async function doUpgrade(){if(!upgradeData||!upgradeData.download_url)return;document.getElementById("upgProgress").style.display="block";document.getElementById("upgApplyBtn").disabled=true;document.getElementById("upgConfirm").disabled=true;var bar=document.getElementById("upgBar");var st=document.getElementById("upgStatus");st.textContent="正在下载...";bar.style.width="30%";try{var r=await fetch("/api/apply-update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({download_url:upgradeData.download_url})});var d=await r.json();if(d.ok){bar.style.width="100%";st.textContent=d.message;st.style.color="var(--green)";document.getElementById("upgHasUpdate").style.display="none";document.getElementById("upgNoUpdate").style.display="block";document.getElementById("upgNoUpdate").innerHTML='<p style="color:var(--green);">✅ 升级完成！请重启写作台</p>';}else{bar.style.width="0";st.textContent="升级失败: "+(d.error||"未知错误");st.style.color="var(--red)";}}catch(e){bar.style.width="0";st.textContent="升级失败: "+e.message;st.style.color="var(--red);"}}

// ======== 键盘快捷键 ========
document.addEventListener("keydown", function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    saveDoc();
  }
});
