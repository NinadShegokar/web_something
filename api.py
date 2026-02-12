from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import ai_assistant

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    target: str


# -------------------------------
# UI (INLINE HTML)
# -------------------------------
@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Security AI Assistant</title>
  <style>
    body { margin:0; font-family:system-ui; background:#0f0f0f; color:#e5e5e5; }
    .container { display:flex; height:100vh; }
    .sidebar { width:220px; background:#111; padding:16px; }
    .chat { flex:1; display:flex; flex-direction:column; }
    #messages { flex:1; padding:20px; overflow-y:auto; }
    .msg { max-width:60%; padding:12px; border-radius:8px; margin-bottom:12px; }
    .user { background:#2563eb; margin-left:auto; }
    .assistant { background:#1f1f1f; }
    .input { display:flex; padding:10px; border-top:1px solid #333; }
    input { flex:1; padding:10px; background:#181818; color:white; border:none; }
    button { margin-left:10px; padding:10px 16px; }
    .reward { background:#181818; padding:10px; font-size:14px; }
  </style>
</head>
<body>

<div class="container">
  <div class="sidebar">
    <h3>Scanned Site</h3>
    <div>sih.gov.in</div>
  </div>

  <div class="chat">
    <div id="messages"></div>
    <div id="reward" class="reward"></div>
    <div class="input">
      <input id="q" placeholder="Ask about the scanned site..." />
      <button onclick="send()">Send</button>
    </div>
  </div>
</div>

<script>
async function send() {
  const input = document.getElementById("q");
  const text = input.value.trim();
  if (!text) return;

  add("user", text);
  input.value = "";

  const res = await fetch("/ask", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ question: text, target: "sih.gov.in" })
  });

  const data = await res.json();
  add("assistant", data.answer);

  if (data.reward === null) {
    document.getElementById("reward").innerText =
      "Baseline response (no learning applied)";
  } else {
    document.getElementById("reward").innerText =
      `Reward: ${data.reward} | C: ${data.reward_components.C} | H: ${data.reward_components.H} | V: ${data.reward_components.V}`;
  }
}

function add(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerText = text;
  document.getElementById("messages").appendChild(div);
}
</script>

</body>
</html>
"""


# -------------------------------
# API
# -------------------------------
@app.post("/ask")
def ask(req: AskRequest):
    return ai_assistant.ask(req.question, req.target)
