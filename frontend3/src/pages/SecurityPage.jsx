import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNav } from '../context/NavContext'

export default function SecurityPage() {
  const { user, debeConfigurar2fa, qrData, setup2FA, verifySetup2FA, clear2FAState } = useAuth()
  const setPage = useNav()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [codeError, setCodeError] = useState('')
  const [codeLoading, setCodeLoading] = useState(false)
  const [step, setStep] = useState('prompt') // prompt → qr → done
  const [success, setSuccess] = useState('')
  const inputsRef = useRef([])

  useEffect(() => {
    if (step === 'qr' && inputsRef.current[0]) {
      inputsRef.current[0].focus()
    }
  }, [step])

  const handleGenerateQR = async (e) => {
    e?.preventDefault()
    setError('')
    setLoading(true)
    const ok = await setup2FA(user.username, password)
    if (ok) {
      setStep('qr')
      setError('')
    } else {
      setError('Error al generar QR. Verifica tu contraseña.')
    }
    setLoading(false)
  }

  const handleCodeChange = (index, value) => {
    if (value && !/^\d$/.test(value)) return
    const newCode = [...code]
    newCode[index] = value
    setCode(newCode)
    if (value && index < 5) {
      inputsRef.current[index + 1]?.focus()
    }
  }

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputsRef.current[index - 1]?.focus()
    }
  }

  const handleVerify = async () => {
    const fullCode = code.join('')
    if (fullCode.length !== 6) return
    setCodeLoading(true)
    setCodeError('')
    const result = await verifySetup2FA(user.username, fullCode)
    if (result === true) {
      setSuccess('✅ 2FA activado correctamente.')
      setStep('done')
      setCode(['', '', '', '', '', ''])
      setCodeLoading(false)
      setTimeout(() => setPage('dashboard'), 2000)
      return
    }
    if (result?.expired) {
      setCodeError(result.msg || 'Demasiados intentos. Redirigiendo al login...')
      setCode(['', '', '', '', '', ''])
      setStep('prompt')
      setCodeLoading(false)
      setTimeout(() => {
        clear2FAState()
        window.location.reload()
      }, 2000)
      return
    }
    setCodeError(result?.error || 'Código inválido')
    setCode(['', '', '', '', '', ''])
    inputsRef.current[0]?.focus()
    setCodeLoading(false)
  }

  const handleCodePaste = (e) => {
    e.preventDefault()
    const pasted = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      const newCode = pasted.split('')
      setCode(newCode)
      inputsRef.current[5]?.focus()
      setTimeout(() => handleVerify(), 100)
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>🔐 Seguridad</h1>
        <p style={{ color: '#8892a4' }}>Autenticación de Doble Factor con Google Authenticator</p>
      </div>

      <div className="card" style={{ maxWidth: '600px' }}>
        {debeConfigurar2fa && !success && (
          <div style={{
            background: 'rgba(102,126,234,0.08)', border: '1px solid rgba(102,126,234,0.15)',
            borderRadius: '10px', padding: '12px 18px', marginBottom: '20px',
            color: '#667eea', fontSize: '14px', fontWeight: 500,
          }}>
            ⚠️ Debes configurar la autenticación de doble factor antes de usar el sistema.
          </div>
        )}

        {success && (
          <div style={{
            background: '#c6f6d5', color: '#276749', padding: '16px',
            borderRadius: '10px', marginBottom: '20px', fontSize: '14px', fontWeight: 600,
            textAlign: 'center',
          }}>
            {success}
          </div>
        )}

        {step === 'prompt' && !success && (
          <>
            <h3 style={{ marginBottom: '15px' }}>📱 Configurar Google Authenticator</h3>
            <ol style={{ color: '#a0a8b8', fontSize: '14px', lineHeight: 1.8, marginBottom: '25px', paddingLeft: '20px' }}>
              <li>Descarga <strong>Google Authenticator</strong> en tu celular</li>
              <li>Ingresa tu contraseña actual y presiona "Generar QR"</li>
              <li>Escanea el código QR con la app</li>
              <li>Ingresa el código de 6 dígitos que aparece en la app</li>
            </ol>

            {error && (
              <div style={{
                background: '#fed7d7', color: '#c53030', padding: '12px 16px',
                borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
              }}>
                ⚠️ {error}
              </div>
            )}

            <form onSubmit={handleGenerateQR}>
              <label style={{ display: 'block', marginBottom: '8px', color: '#4a5568', fontWeight: 500, fontSize: '0.9rem' }}>
                Contraseña actual
              </label>
              <input
                type="password" value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Ingresa tu contraseña para generar QR" required
                style={{
                  width: '100%', padding: '14px 16px', border: '2px solid #e2e8f0',
                  borderRadius: '12px', fontSize: '1rem', outline: 'none',
                  fontFamily: "'Poppins', sans-serif", boxSizing: 'border-box', marginBottom: '20px',
                }}
                onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
                onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
              />
              <button type="submit" disabled={loading || !password}
                style={{
                  width: '100%', padding: '16px',
                  background: loading || !password ? '#a0aec0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white', border: 'none', borderRadius: '12px',
                  fontSize: '1rem', fontWeight: 600, cursor: loading || !password ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', sans-serif",
                }}
              >
                {loading ? 'Generando...' : '📱 Generar QR'}
              </button>
            </form>
          </>
        )}

        {step === 'qr' && qrData && !success && (
          <>
            <h3 style={{ marginBottom: '15px', textAlign: 'center' }}>📷 Escanea el código QR</h3>

            {codeError && (
              <div style={{
                background: '#fed7d7', color: '#c53030', padding: '12px 16px',
                borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
                textAlign: 'center',
              }}>
                ⚠️ {codeError}
              </div>
            )}

            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <img
                src={`data:image/png;base64,${qrData.qr_base64}`}
                alt="QR Code para Google Authenticator"
                style={{
                  width: '220px', height: '220px',
                  border: '2px solid #e2e8f0', borderRadius: '12px',
                  padding: '10px', background: 'white',
                }}
              />
              <p style={{ color: '#8892a4', fontSize: '13px', marginTop: '10px' }}>
                Escanea con Google Authenticator o ingresa el código manual:
              </p>
              <p style={{
                fontFamily: 'monospace', fontSize: '12px', color: '#667eea',
                background: '#f7fafc', padding: '8px 12px', borderRadius: '8px',
                wordBreak: 'break-all', maxWidth: '300px', margin: '8px auto',
              }}>
                {qrData.secret}
              </p>
            </div>

            <p style={{ color: '#8892a4', fontSize: '13px', textAlign: 'center', marginBottom: '15px' }}>
              Ingresa el código de 6 dígitos que aparece en la app
            </p>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}
              onPaste={handleCodePaste}
            >
              {code.map((digit, i) => (
                <input
                  key={i}
                  ref={el => inputsRef.current[i] = el}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleCodeChange(i, e.target.value)}
                  onKeyDown={e => handleCodeKeyDown(i, e)}
                  style={{
                    width: '48px', height: '56px',
                    textAlign: 'center', fontSize: '1.5rem', fontWeight: 700,
                    border: `2px solid ${codeError ? '#e74c3c' : '#e2e8f0'}`,
                    borderRadius: '12px', outline: 'none',
                    fontFamily: "'Poppins', sans-serif",
                    color: '#333', background: digit ? '#f7fafc' : 'white',
                  }}
                  onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
                  onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
                />
              ))}
            </div>

            <button onClick={handleVerify} disabled={codeLoading || code.join('').length !== 6}
              style={{
                width: '100%', padding: '16px',
                background: codeLoading || code.join('').length !== 6 ? '#a0aec0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white', border: 'none', borderRadius: '12px',
                fontSize: '1rem', fontWeight: 600,
                cursor: codeLoading || code.join('').length !== 6 ? 'not-allowed' : 'pointer',
                fontFamily: "'Poppins', sans-serif",
              }}
            >
              {codeLoading ? 'Verificando...' : '✅ Activar 2FA'}
            </button>

            <div style={{ textAlign: 'center', marginTop: '15px' }}>
              <button onClick={() => { setStep('prompt'); setCode(['', '', '', '', '', '']); setCodeError('') }}
                style={{
                  background: 'none', border: 'none', color: '#8892a4',
                  cursor: 'pointer', fontSize: '0.85rem', textDecoration: 'underline',
                  fontFamily: "'Poppins', sans-serif",
                }}>
                ← Volver
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
