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

  async function startListening() {
    if (listening) {
      stopListening()
      return
    }

    // 1. Forzar solicitud explícita de permiso de micrófono al navegador (MediaDevices)
    let micStream = null
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
        // Detener los tracks de prueba una vez concedido el permiso
        micStream.getTracks().forEach(t => t.stop())
      }
    } catch (err) {
      console.error('Error al acceder al micrófono:', err)
      alert('⚠️ El navegador bloqueó el acceso al micrófono. Por favor haz clic en el ícono de candado 🔒 o micrófono en la barra de dirección del navegador y selecciona "Permitir".')
      setListening(false)
      return
    }

    // 2. Iniciar el motor SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Tu navegador no soporta reconocimiento de voz nativo. Por favor abre el sistema desde Google Chrome o Microsoft Edge.')
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.lang = 'es-PE'
      recognition.interimResults = true
      recognition.continuous = false
      recognition.maxAlternatives = 1

      let finalTranscript = ''

      recognition.onstart = () => {
        setListening(true)
      }

      recognition.onresult = (event) => {
        let currentText = ''
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          currentText += event.results[i][0].transcript
        }
        if (currentText.trim()) {
          finalTranscript = currentText
          setInput(currentText)
          if (inputRef.current) inputRef.current.value = currentText
        }
      }

      recognition.onerror = (e) => {
        console.warn('Error en reconocimiento de voz:', e.error)
        setListening(false)
        if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
          alert('⚠️ Permiso de micrófono denegado. Por favor actívalo en la configuración del navegador.')
        } else if (e.error === 'no-speech') {
          console.log('No se detectó voz.')
        }
      }

      recognition.onend = () => {
        setListening(false)
        if (finalTranscript.trim()) {
          // Enviar el mensaje capturado de forma automática
          sendMessageWithText(finalTranscript, true)
        }
      }

      recognition.start()
      recognitionRef.current = recognition
    } catch (err) {
      console.error('Error al iniciar reconocedor:', err)
      setListening(false)
    }
  }

  function stopListening() {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setListening(false)
  }

  function hablar(texto) {
    if (!('speechSynthesis' in window)) {
      alert('Tu navegador no soporta síntesis de voz.')
      return
    }
    if (speaking) {
      speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    speechSynthesis.cancel()
    const cleanText = texto
      .replace(/[*#•⚠️✅📊📉📦🍞🛒🔮💡📖🤖➔🏷️👥💰🏆]/g, '')
      .replace(/https?:\/\/\S+/g, '')
      .trim()
    if (!cleanText) return

    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.lang = 'es-PE'
    utterance.rate = 0.95
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    setSpeaking(true)
    speechSynthesis.speak(utterance)
  }

  async function sendMessageWithText(textToSend = null, autoSpeak = false) {
    const msg = (textToSend !== null ? textToSend : input).trim()
    if (!msg) return
    setInput('')
    if (inputRef.current) inputRef.current.value = ''
    setMessages(prev => [...prev, { from: 'user', text: msg }])
    setLoading(true)
    try {
      const data = await api.post('/chatbot/mensaje', { mensaje: msg, pregunta: msg })
      const botText = data.respuesta || data.mensaje || 'Respuesta no disponible'
      setMessages(prev => [...prev, { from: 'bot', text: botText }])
      if (autoSpeak) {
        hablar(botText)
      }
    } catch {
      setMessages(prev => [...prev, { from: 'bot', text: '⚠️ Error de conexión. Verifica que el backend esté funcionando.' }])
    } finally {
      setLoading(false)
    }
  }

  function sendMessage() {
    sendMessageWithText(null, false)
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
                title={speaking ? 'Detener lectura' : 'Escuchar última respuesta'}
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
            {loading && <div className="chat-message bot">🤖 Procesando consulta...</div>}
            {listening && <div className="chat-message bot" style={{ color: '#e53e3e', fontWeight: 'bold' }}>🔴 Escuchando voz... habla ahora</div>}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <button
              onClick={startListening}
              className={`chat-mic-btn ${listening ? 'chat-mic-active' : ''}`}
              title={listening ? 'Detener grabación' : 'Hablar por micrófono'}
              style={listening ? { background: '#ef4444', color: '#fff', animation: 'pulse 1.2s infinite' } : {}}
            >
              🎤
            </button>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={listening ? 'Escuchando tu voz...' : 'Escribe o usa el micrófono...'}
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
