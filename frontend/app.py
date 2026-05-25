import streamlit as st
import requests
import pandas as pd
from datetime import date
from streamlit.components.v1 import html

st.set_page_config(page_title="Dashboard | Panaderia Victoria", page_icon="🏠", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
.stMetric{background:#1e2a3a;padding:20px;border-radius:10px;border:1px solid #2d4a6a;}
</style>""", unsafe_allow_html=True)

chat_css = """
<style>
.chat-bubble {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
    z-index: 9999;
    transition: transform 0.3s ease;
    border: none;
}
.chat-bubble:hover { transform: scale(1.1); }
.chat-bubble span { font-size: 28px; }
.chat-window {
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 320px;
    height: 450px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    z-index: 9999;
    display: none;
    flex-direction: column;
    overflow: hidden;
}
.chat-window.active { display: flex; }
.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.chat-close { cursor: pointer; font-size: 18px; padding: 0; border: none; background: none; color: white; }
.chat-messages {
    flex: 1;
    padding: 10px;
    overflow-y: auto;
    background: #f8f9fa;
    display: flex;
    flex-direction: column;
}
.chat-input {
    padding: 10px;
    border-top: 1px solid #ddd;
    display: flex;
    gap: 8px;
}
.chat-input input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 15px;
    outline: none;
}
.chat-input button {
    background: #667eea;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 15px;
    cursor: pointer;
}
.message { margin-bottom: 10px; max-width: 80%; font-size: 13px; word-wrap: break-word; }
.message.bot { background: #e9ecef; padding: 8px 12px; border-radius: 12px 12px 12px 0; align-self: flex-start; }
.message.user { background: #667eea; color: white; padding: 8px 12px; border-radius: 12px 12px 0 12px; align-self: flex-end; }
</style>
"""

chat_js = """
<script>
var API_URL = "http://localhost:8000";

function toggleChat() {
    var win = document.querySelector('.chat-window');
    win.classList.toggle('active');
}
function closeChat() {
    document.querySelector('.chat-window').classList.remove('active');
}
function scrollBottom() {
    var msgs = document.querySelector('.chat-messages');
    msgs.scrollTop = msgs.scrollHeight;
}
function sendMessage() {
    var input = document.getElementById('chatInput');
    var message = input.value.trim();
    if (!message) return;
    
    var messages = document.querySelector('.chat-messages');
    var div = document.createElement('div');
    div.className = 'message user';
    div.textContent = message;
    messages.appendChild(div);
    input.value = '';
    scrollBottom();
    
    var typing = document.createElement('div');
    typing.className = 'message bot';
    typing.id = 'typing';
    typing.textContent = 'Escribiendo...';
    messages.appendChild(div);
    messages.appendChild(typing);
    scrollBottom();
    
    fetch(API_URL + '/chatbot/pregunta', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({pregunta: message})
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        var tip = document.getElementById('typing');
        if (tip) tip.remove();
        var resp = document.createElement('div');
        resp.className = 'message bot';
        resp.innerHTML = (data.mensaje || 'No hubo respuesta').replace(/\\n/g, '<br>');
        messages.appendChild(resp);
        scrollBottom();
    })
    .catch(function(err) {
        var tip = document.getElementById('typing');
        if (tip) tip.remove();
        var errDiv = document.createElement('div');
        errDiv.className = 'message bot';
        errDiv.textContent = 'Error. Asegurate que el backend este en http://localhost:8000';
        messages.appendChild(errDiv);
        scrollBottom();
    });
}
function handleKey(e) {
    if (e.key === 'Enter') sendMessage();
}
</script>
"""

chat_html = (
    chat_css +
    '<div class="chat-bubble" onclick="toggleChat()"><span>&#128172;</span></div>' +
    '<div class="chat-window">' +
    '  <div class="chat-header">' +
    '    <span>&#128999; Asistente</span>' +
    '    <button class="chat-close" onclick="closeChat()">&#10005;</button>' +
    '  </div>' +
    '  <div class="chat-messages">' +
    '    <div class="message bot">Hola! Soy el asistente de Panaderia Victoria. Puedo ayudarte con ventas, inventario, mermas y mas. Que necesitas?</div>' +
    '  </div>' +
    '  <div class="chat-input">' +
    '    <input type="text" id="chatInput" placeholder="Escribe tu pregunta..." onkeypress="handleKey(event)">' +
    '    <button onclick="sendMessage()">Enviar</button>' +
    '  </div>' +
    '</div>' +
    chat_js
)

html(chat_html, height=0, scrolling=False)

API = "http://localhost:8000"

PAGES_OPERATIVO = [
    st.Page("pages/Resumen.py", title="Resumen", icon="🏠", default=True),
    st.Page("pages/Registro_Diario.py", title="Registro Diario", icon="📦"),
    st.Page("pages/Predicciones.py", title="Predicciones", icon="🔮"),
    st.Page("pages/Analisis_Mermas.py", title="Mermas", icon="📊"),
    st.Page("pages/Inventario.py",           title="Inventario",          icon="🏪"),
    st.Page("pages/Catalogo.py",             title="Catalogo",            icon="📦"),
    st.Page("pages/Ordenes_Compra.py",       title="Ordenes de Compra",   icon="🛒"),
    st.Page("pages/Reportes_Financieros.py", title="Reportes Financieros", icon="💰"),
]

PAGES_TECNICO = [
    st.Page("pages/Modelo_Estadistico.py", title="Estadisticas del Modelo", icon="📈"),
]

pg = st.navigation({
    "Operacion Diaria 🏪": PAGES_OPERATIVO,
    "Sistema (Tecnico) ⚙️": PAGES_TECNICO,
})
pg.run()