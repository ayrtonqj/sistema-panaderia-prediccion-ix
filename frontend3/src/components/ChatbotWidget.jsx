import { useState, useRef, useEffect } from 'react'
import { api } from '../api/api'

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { from: 'bot', text: '¡Hola! Soy el asistente de Panadería Victoria. Puedo ayudarte con: ventas, inventario, mermas, productos y más. ¿Qué necesitas?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    const msg = input.trim()
    if (!msg) return
    setInput('')
    setMessages(prev => [...prev, { from: 'user', text: msg }])
    setLoading(true)
    try {
      const data = await api.post('/chatbot/pregunta', { pregunta: msg })
      setMessages(prev => [...prev, { from: 'bot', text: data.mensaje }])
    } catch {
      setMessages(prev => [...prev, { from: 'bot', text: '⚠️ Error de conexión. Verifica que el backend esté en http://localhost:8000' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="chat-bubble" onClick={() => setOpen(o => !o)} title="Abrir asistente">💬</div>
      {open && (
        <div className="chat-window">
          <div className="chat-header">
            <span>🤖 Asistente Victoria</span>
            <span onClick={() => setOpen(false)} style={{cursor:'pointer',fontSize:'16px'}}>✕</span>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.from}`}
                dangerouslySetInnerHTML={{ __html: m.text.replace(/\n/g, '<br>') }}
              />
            ))}
            {loading && <div className="chat-message bot">🤖 Escribiendo...</div>}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Escribe tu pregunta..."
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading}>Enviar</button>
          </div>
        </div>
      )}
    </>
  )
}
