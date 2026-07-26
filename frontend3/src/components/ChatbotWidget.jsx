import { useState, useRef, useEffect } from 'react'
import { api } from '../api/api'

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { from: 'bot', text: '¡Hola! Soy el asistente de Panadería Victoria 🥖. Puedo ayudarte con: ventas, inventario, mermas, productos, predicciones y más. ¿Qué necesitas?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [micError, setMicError] = useState(null)

  const messagesEndRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const recognitionRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── INICIAR GRABACIÓN DE AUDIO (MediaRecorder + SpeechRecognition) ──────
  async function startRecording() {
    setMicError(null)
    if (recording) {
      stopRecording()
      return
    }

    chunksRef.current = []

    let stream = null
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setMicError('⚠️ El navegador no soporta grabación de audio. Usa Chrome o Edge.')
        return
      }
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
    } catch (err) {
      console.error('Error al acceder al micrófono:', err)
      setMicError('⚠️ Permiso de micrófono denegado. Haz clic en el ícono de candado 🔒 al lado izquierdo de la URL arriba y selecciona "Permitir micrófono".')
      return
    }

    // 1. Configurar MediaRecorder de HTML5 (Idéntico a AudioRecorder.tsx)
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
      ? 'audio/webm'
      : MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
      ? 'audio/ogg;codecs=opus'
      : ''

    let speechTranscript = ''

    // 2. Intentar reconocimiento de voz nativo en paralelo
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition()
        recognition.lang = 'es-PE'
        recognition.interimResults = true
        recognition.continuous = false

        recognition.onresult = (e) => {
          let text = ''
          for (let i = e.resultIndex; i < e.results.length; ++i) {
            text += e.results[i][0].transcript
          }
          if (text.trim()) {
            speechTranscript = text
            setInput(text)
            if (inputRef.current) inputRef.current.value = text
          }
        }

        recognition.start()
        recognitionRef.current = recognition
      } catch (e) {
        console.warn('SpeechRecognition fallback:', e)
      }
    }

    // 3. Iniciar MediaRecorder
    try {
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = async () => {
        setRecording(false)
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop())
          streamRef.current = null
        }

        const audioBlob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' })

        // Si tenemos la transcripción nativa, la enviamos directamente
        if (speechTranscript.trim()) {
          sendMessageWithText(speechTranscript, true)
          return
        }

        // Si no, enviamos el audio Blob al backend /chatbot/audio
        if (audioBlob.size > 0) {
          await processAudioBlob(audioBlob)
        }
      }

      recorder.start()
      setRecording(true)
    } catch (err) {
      console.error('Error al iniciar MediaRecorder:', err)
      setMicError(`⚠️ Error al iniciar grabación: ${err.message}`)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
        streamRef.current = null
      }
    }
  }

  function stopRecording() {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch {}
    } else {
      setRecording(false)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
        streamRef.current = null
      }
    }
  }

  // Enviar audio Blob al servidor si no hubo transcripción nativa
  async function processAudioBlob(blob) {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('audio', blob, 'recording.webm')
      const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
      const res = await fetch(`${API_BASE}/chatbot/audio`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const data = await res.json()
        const text = data.transcription || data.texto || ''
        if (text.trim()) {
          setInput(text)
          if (inputRef.current) inputRef.current.value = text
          sendMessageWithText(text, true)
        } else {
          setMicError('⚠️ No se logró transcribir audio. Por favor intenta hablar más claro.')
        }
      }
    } catch (err) {
      console.error('Error procesando audio blob:', err)
    } finally {
      setLoading(false)
    }
  }

  function hablar(texto) {
    if (!('speechSynthesis' in window)) return
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
        className={`chat-bubble ${recording ? 'chat-bubble-listening' : ''}`}
        onClick={() => {
          if (open) stopRecording()
          setOpen(o => !o)
        }}
        title="Abrir asistente"
      >
        {recording ? '🎤' : '💬'}
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
                onClick={() => { setOpen(false); stopRecording() }}
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
            {recording && <div className="chat-message bot" style={{ color: '#e53e3e', fontWeight: 'bold' }}>🔴 Grabando voz por micrófono... habla ahora</div>}
            {micError && (
              <div className="chat-message bot" style={{ background: '#fff5f5', color: '#c53030', border: '1px solid #feb2b2', padding: '10px', borderRadius: '8px', fontSize: '13px', margin: '8px 0' }}>
                {micError}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <button
              onClick={startRecording}
              className={`chat-mic-btn ${recording ? 'chat-mic-active' : ''}`}
              title={recording ? 'Detener grabación' : 'Grabar voz'}
              style={recording ? { background: '#ef4444', color: '#fff', animation: 'pulse 1.2s infinite' } : {}}
            >
              🎤
            </button>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={recording ? 'Grabando tu voz...' : 'Escribe o usa el micrófono...'}
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
