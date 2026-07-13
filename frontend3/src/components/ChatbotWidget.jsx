import { useState, useRef, useEffect } from 'react'
import { api } from '../api/api'

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { from: 'bot', text: '¡Hola! Soy el asistente de Panadería Victoria. Puedo ayudarte con: ventas, inventario, mermas, productos, predicciones y más. ¿Qué necesitas?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function startListening() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Tu navegador no soporta reconocimiento de voz. Prueba con Chrome o Edge.')
      return
    }
    if (listening) {
      stopListening()
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'es-PE'
    recognition.interimResults = false
    recognition.continuous = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      if (inputRef.current) inputRef.current.value = transcript
    }

    recognition.onerror = () => {
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
    }

    recognition.start()
    setListening(true)
    recognitionRef.current = recognition
  }

  function stopListening() {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setListening(false)
  }

  function hablar(texto) {
    if (speaking) {
      speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    const cleanText = texto.replace(/[#*•⚠️✅📊📉📦🍞🛒🔮💡📖🤖]/g, '').trim()
    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.lang = 'es-PE'
    utterance.rate = 0.9
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    setSpeaking(true)
    speechSynthesis.speak(utterance)
  }

  async function sendMessage() {
    const msg = input.trim()
    if (!msg) return
    setInput('')
    if (inputRef.current) inputRef.current.value = ''
    setMessages(prev => [...prev, { from: 'user', text: msg }])
    setLoading(true)
    try {
      const data = await api.post('/chatbot/pregunta', { pregunta: msg })
      setMessages(prev => [...prev, { from: 'bot', text: data.mensaje }])
    } catch {
      setMessages(prev => [...prev, { from: 'bot', text: '⚠️ Error de conexión. Verifica que el backend esté funcionando.' }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      <div
        className={`chat-bubble ${listening ? 'chat-bubble-listening' : ''}`}
        onClick={() => {
          if (open) stopListening()
          setOpen(o => !o)
        }}
        title="Abrir asistente"
      >
        {listening ? '🎤' : '💬'}
      </div>
      {open && (
        <div className="chat-window">
          <div className="chat-header">
            <span>🤖 Asistente Victoria</span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                onClick={() => hablar(messages[messages.length - 1]?.text || '')}
                className="chat-header-btn"
                title={speaking ? 'Detener' : 'Leer respuesta'}
                style={{ fontSize: '14px', cursor: 'pointer', background: 'none', border: 'none', color: 'white', padding: '0' }}
              >
                {speaking ? '🔊' : '🔈'}
              </button>
              <span
                onClick={() => { setOpen(false); stopListening() }}
                style={{ cursor: 'pointer', fontSize: '16px' }}
              >
                ✕
              </span>
            </div>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.from}`}>
                <div dangerouslySetInnerHTML={{ __html: m.text.replace(/\n/g, '<br>') }} />
                {m.from === 'bot' && (
                  <button
                    onClick={() => hablar(m.text)}
                    className="chat-tts-btn"
                    title="Escuchar"
                  >
                    🔊
                  </button>
                )}
              </div>
            ))}
            {loading && <div className="chat-message bot">🤖 Escribiendo...</div>}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <button
              onClick={startListening}
              className={`chat-mic-btn ${listening ? 'chat-mic-active' : ''}`}
              title={listening ? 'Detener grabación' : 'Hablar'}
            >
              🎤
            </button>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe o usa el micrófono..."
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()}>
              Enviar
            </button>
          </div>
        </div>
      )}
    </>
  )
}
