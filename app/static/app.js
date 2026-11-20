const $ = (id) => document.getElementById(id);
const messages = $("messages");
const form = $("askForm");
const input = $("question");
const sendBtn = $("sendBtn");
const fileInput = $("fileInput");
const uploadMsg = $("uploadMsg");
const docList = $("docList");

function addBubble(text, kind) {
  const div = document.createElement("div");
  div.className = `bubble ${kind}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function addSources(bubble, sources) {
  if (!sources || !sources.length) return;
  const details = document.createElement("details");
  details.className = "sources";
  const summary = document.createElement("summary");
  summary.textContent = `Sources (${sources.length})`;
  details.appendChild(summary);
  for (const s of sources) {
    const box = document.createElement("div");
    box.className = "source";
    const title = document.createElement("b");
    title.textContent = `${s.label}  (match ${s.score})`;
    const body = document.createElement("div");
    body.textContent = s.text;
    box.append(title, body);
    details.appendChild(box);
  }
  bubble.appendChild(details);
}

async function refreshDocs() {
  const res = await fetch("/api/documents");
  const data = await res.json();
  renderDocs(data.documents);
}

function renderDocs(docs) {
  docList.replaceChildren();
  if (!docs.length) {
    const li = document.createElement("li");
    li.textContent = "No documents yet.";
    docList.appendChild(li);
    return;
  }
  for (const d of docs) {
    const li = document.createElement("li");
    const left = document.createElement("span");
    left.className = "name";
    left.textContent = d.name + " ";
    const small = document.createElement("small");
    small.textContent = `${d.chunks} chunks`;
    left.appendChild(small);
    const del = document.createElement("button");
    del.title = "Remove";
    del.textContent = "×";
    del.addEventListener("click", () => removeDoc(d.name));
    li.append(left, del);
    docList.appendChild(li);
  }
}

async function removeDoc(name) {
  const res = await fetch(`/api/documents/${encodeURIComponent(name)}`, { method: "DELETE" });
  if (res.ok) renderDocs((await res.json()).documents);
}

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;
  uploadMsg.className = "msg";
  uploadMsg.textContent = "Uploading...";
  const body = new FormData();
  body.append("file", file);
  try {
    const res = await fetch("/api/upload", { method: "POST", body });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    uploadMsg.textContent = `Added ${data.uploaded}`;
    renderDocs(data.documents);
  } catch (err) {
    uploadMsg.className = "msg error";
    uploadMsg.textContent = err.message;
  }
  fileInput.value = "";
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  addBubble(question, "user");
  input.value = "";
  sendBtn.disabled = true;
  const pending = addBubble("Thinking...", "bot");
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed");
    pending.textContent = data.answer;
    addSources(pending, data.sources);
  } catch (err) {
    pending.textContent = err.message;
    pending.classList.add("error");
  } finally {
    sendBtn.disabled = false;
    input.focus();
    messages.scrollTop = messages.scrollHeight;
  }
});

async function init() {
  await refreshDocs();
  const health = await (await fetch("/api/health")).json();
  $("modeBadge").textContent = health.claude_enabled
    ? `Answers by Claude (${health.model})`
    : "Retrieval-only mode: set ANTHROPIC_API_KEY for Claude answers";
}
init();
