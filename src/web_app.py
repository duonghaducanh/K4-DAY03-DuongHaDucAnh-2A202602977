"""Local web UI for the VinUni ReAct agent."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent, save_waterfall_trace
from mcp_server import MCPAcademicServer
from providers import get_llm_provider

HOST = "127.0.0.1"
PORT = int(os.getenv("WEB_PORT", "8000"))
PROVIDER = get_llm_provider()
MCP_SERVER = MCPAcademicServer()

PAGE = r'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VinUni ReAct Desk</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{--ink:#14231f;--muted:#6d7974;--paper:#f4f2eb;--panel:#fffdf8;--line:#dfe3d9;--lime:#caf06a;--coral:#ff806d;--teal:#187b70;--shadow:0 18px 45px rgba(36,52,42,.08)}
*{box-sizing:border-box}body{margin:0;min-height:100vh;color:var(--ink);background:var(--paper);font-family:'Space Grotesk',system-ui,sans-serif}body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.35;background-image:linear-gradient(rgba(20,35,31,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(20,35,31,.035) 1px,transparent 1px);background-size:32px 32px}.shell{position:relative;width:min(1420px,calc(100% - 40px));margin:auto;padding:28px 0 36px}header{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:28px}.eyebrow{color:var(--teal);font:500 12px 'DM Mono',monospace;letter-spacing:.08em;text-transform:uppercase}h1{max-width:650px;margin:8px 0;font-size:clamp(36px,5vw,68px);line-height:.95;letter-spacing:-.04em}.lede{max-width:600px;margin:0;color:var(--muted);font-size:16px;line-height:1.55}.status{display:flex;align-items:center;gap:10px;padding:11px 14px;border:1px solid var(--line);background:rgba(255,253,248,.8);font:500 12px 'DM Mono',monospace;box-shadow:var(--shadow)}.dot{width:9px;height:9px;border-radius:50%;background:var(--lime);box-shadow:0 0 0 4px rgba(202,240,106,.22)}.workspace{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(320px,.75fr);gap:18px}.panel{border:1px solid var(--line);background:rgba(255,253,248,.92);box-shadow:var(--shadow)}.chat{display:flex;min-height:680px;flex-direction:column}.panel-head{display:flex;justify-content:space-between;align-items:center;padding:18px 20px;border-bottom:1px solid var(--line)}.panel-title{font-weight:700;font-size:15px}.panel-meta{color:var(--muted);font:12px 'DM Mono',monospace}#messages{flex:1;min-height:420px;max-height:590px;padding:22px;overflow:auto}.welcome{max-width:570px;padding:22px;border-left:4px solid var(--coral);background:#fff7e8}.welcome strong{display:block;margin-bottom:8px;font-size:18px}.welcome p{margin:0;color:#69706c;line-height:1.55}.quick{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.quick button{padding:9px 11px;color:var(--teal);border:1px solid #a9d2c8;background:transparent;font:600 12px 'Space Grotesk',sans-serif;cursor:pointer}.message{display:flex;margin-bottom:18px;animation:rise .3s ease both}.message.user{justify-content:flex-end}.bubble{max-width:min(80%,680px);padding:14px 16px;line-height:1.5;white-space:pre-wrap}.assistant .bubble{border-left:3px solid var(--teal);background:#eef2e9}.user .bubble{color:#fff;background:var(--ink)}.label{display:block;margin-bottom:5px;color:var(--muted);font:11px 'DM Mono',monospace;text-transform:uppercase}.user .label{color:#c8d1cc}.composer{padding:16px;border-top:1px solid var(--line)}textarea{width:100%;min-height:60px;padding:14px;resize:none;border:1px solid var(--line);outline:none;background:#fff;color:var(--ink);font:15px 'Space Grotesk',sans-serif}textarea:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(24,123,112,.12)}.composer-row{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:10px}.hint{color:var(--muted);font-size:12px}.send{padding:12px 18px;border:0;background:var(--lime);color:var(--ink);font:600 13px 'Space Grotesk',sans-serif;cursor:pointer}.send:disabled{cursor:wait;opacity:.55}.trace{min-height:680px}.trace-list{max-height:620px;padding:16px;overflow:auto}.empty{padding:18px 4px;color:var(--muted);font-size:14px;line-height:1.5}.event{margin-bottom:12px;border:1px solid var(--line);background:#fff}.event-head{display:flex;justify-content:space-between;gap:10px;padding:11px 12px;background:#f7f8f1;font:500 11px 'DM Mono',monospace}.event-type{color:var(--teal)}.event-body{padding:12px;font-size:13px;line-height:1.45}.event-body p{margin:0 0 8px}pre{margin:8px 0 0;padding:10px;overflow:auto;background:#f4f5ef;color:#52605a;font:11px/1.5 'DM Mono',monospace}@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}@media(max-width:850px){.shell{width:min(100% - 24px,680px);padding-top:18px}header{display:block}.status{display:inline-flex;margin-top:18px}.workspace{grid-template-columns:1fr}.chat,.trace{min-height:0}#messages{max-height:none}.trace-list{max-height:430px}.bubble{max-width:90%}}
</style>
</head>
<body>
<main class="shell">
<header><div><div class="eyebrow">VINUNI / ACADEMIC INTELLIGENCE</div><h1>Hỏi ít. Agent tự làm nhiều.</h1><p class="lede">Trợ lý học vụ kết nối MCP, tra cứu dữ liệu và đặt lịch tư vấn qua vòng lặp ReAct có thể quan sát.</p></div><div class="status"><span class="dot"></span><span id="provider">Đang kết nối...</span></div></header>
<section class="workspace"><section class="panel chat"><div class="panel-head"><span class="panel-title">Cuộc trò chuyện</span><span class="panel-meta" id="mcp">MCP / checking</span></div><div id="messages"><div class="welcome"><strong>Xin chào, mình là trợ lý học vụ.</strong><p>Mình có thể tra cứu hồ sơ sinh viên, xử lý mã không tồn tại và đặt lịch với cố vấn. Mỗi lần gọi tool sẽ hiện trong Agent trace.</p><div class="quick"><button data-prompt="Hãy tra cứu thông tin học vụ của sinh viên SV2026001.">Tra cứu SV2026001</button><button data-prompt="Hãy tra cứu cố vấn của sinh viên SV2026001 và đặt lịch tư vấn với cố vấn đó vào 14:00 ngày 15/09/2026.">Tra cứu rồi đặt lịch</button></div></div></div><form class="composer" id="composer"><textarea id="input" placeholder="Viết câu hỏi của bạn..." aria-label="Câu hỏi"></textarea><div class="composer-row"><span class="hint">Enter để gửi · Shift + Enter xuống dòng</span><button class="send" id="send">Gửi yêu cầu ↗</button></div></form></section><aside class="panel trace"><div class="panel-head"><span class="panel-title">Agent trace</span><span class="panel-meta">LIVE WATERFALL</span></div><div class="trace-list" id="trace"><div class="empty">Trace sẽ xuất hiện sau khi agent suy luận và gọi MCP tool.</div></div></aside></section>
</main>
<script>
const messages=document.querySelector('#messages'),traceBox=document.querySelector('#trace'),input=document.querySelector('#input'),send=document.querySelector('#send');
const escapeHtml=v=>v.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
function addMessage(role,text){const el=document.createElement('div');el.className=`message ${role}`;el.innerHTML=`<div class="bubble"><span class="label">${role==='user'?'Bạn':'ReAct Agent'}</span>${escapeHtml(text)}</div>`;messages.appendChild(el);messages.scrollTop=messages.scrollHeight}
function renderTrace(events){traceBox.innerHTML='';events.forEach(e=>{let body=e.thought?`<p><b>Thought</b> ${escapeHtml(e.thought)}</p>`:'';if(e.arguments)body+=`<p><b>Arguments</b></p><pre>${escapeHtml(JSON.stringify(e.arguments,null,2))}</pre>`;if(e.observation&&Object.keys(e.observation).length)body+=`<p><b>Observation</b></p><pre>${escapeHtml(JSON.stringify(e.observation,null,2))}</pre>`;if(e.output)body+=`<p><b>Output</b> ${escapeHtml(e.output)}</p>`;const el=document.createElement('article');el.className='event';el.innerHTML=`<div class="event-head"><span class="event-type">STEP ${e.step} / ${e.action_type}${e.tool_name?' · '+e.tool_name:''}</span><span>${e.latency_ms} ms</span></div><div class="event-body">${body}</div>`;traceBox.appendChild(el)})}
async function submit(question){if(!question.trim()||send.disabled)return;addMessage('user',question);input.value='';send.disabled=true;send.textContent='Đang suy luận...';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});const data=await r.json();if(!r.ok)throw Error(data.error||'Không thể gọi agent');addMessage('assistant',data.answer);renderTrace(data.trace)}catch(e){addMessage('assistant',`Có lỗi: ${e.message}`)}finally{send.disabled=false;send.textContent='Gửi yêu cầu ↗';input.focus()}}
async function status(){const r=await fetch('/api/status');const d=await r.json();document.querySelector('#provider').textContent=`${d.provider} · ${d.model||'ready'}`;document.querySelector('#mcp').textContent=`MCP / ${d.tools} tools online`}
document.querySelector('#composer').addEventListener('submit',e=>{e.preventDefault();submit(input.value)});input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit(input.value)}});document.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>{input.value=b.dataset.prompt;input.focus()}));status().catch(()=>document.querySelector('#provider').textContent='Agent offline');
</script>
</body>
</html>'''


def final_answer(trace):
    for event in reversed(trace):
        if event.get("action_type") == "FINAL_ANSWER":
            return event.get("output", "Agent không có phản hồi.")
    return "Agent không hoàn tất được yêu cầu."


class RequestHandler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/status":
            self.send_json({"provider": PROVIDER.__class__.__name__, "model": getattr(PROVIDER, "model_name", ""), "tools": len(MCP_SERVER.list_tools())})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("Vui lòng nhập câu hỏi.")
            trace = run_react_agent(question, PROVIDER, MCP_SERVER)
            save_waterfall_trace(trace)
            self.send_json({"answer": final_answer(trace), "trace": trace})
        except Exception as error:
            self.send_json({"error": str(error)}, 400)

    def log_message(self, format, *args):
        print(f"[web] {format % args}")


if __name__ == "__main__":
    print(f"VinUni ReAct Desk: http://{HOST}:{PORT}")
    print(f"Provider: {PROVIDER.__class__.__name__}")
    ThreadingHTTPServer((HOST, PORT), RequestHandler).serve_forever()
