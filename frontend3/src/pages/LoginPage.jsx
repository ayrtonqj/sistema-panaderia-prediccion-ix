import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login, requires2fa, login2FA, recover2FA, recoverVerify2FA, qrRecovery, setQrRecovery, isDemoMode, retryDemoLogin } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [codeError, setCodeError] = useState('')
  const [codeLoading, setCodeLoading] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const inputsRef = useRef([])

  // Recovery states
  const [recoverMode, setRecoverMode] = useState(null) // null | 'password' | 'qr'
  const [recoverPassword, setRecoverPassword] = useState('')
  const [recoverQrBase64, setRecoverQrBase64] = useState('')
  const [recoverLoading, setRecoverLoading] = useState(false)
  const [recoverError, setRecoverError] = useState('')
  const [recoverCode, setRecoverCode] = useState(['', '', '', '', '', ''])
  const [recoverCodeLoading, setRecoverCodeLoading] = useState(false)
  const [recoverCodeError, setRecoverCodeError] = useState('')
  const recoverInputsRef = useRef([])

  // Cuando requires2fa se activa, pasamos al modo código
  useEffect(() => {
    if (requires2fa) {
      setVerifying(true)
      setCodeError('')
      setCode(['', '', '', '', '', ''])
      setRecoverMode(null)
    }
  }, [requires2fa])

  useEffect(() => {
    if (verifying && inputsRef.current[0]) {
      inputsRef.current[0].focus()
    }
  }, [verifying])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const result = await login(username, password)
    if (result === false) {
      setError('Credenciales incorrectas')
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

  const handleCodePaste = (e) => {
    e.preventDefault()
    const pasted = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      const newCode = pasted.split('')
      setCode(newCode)
      inputsRef.current[5]?.focus()
      // Auto-submit with pasted code
      handleVerifyCode(newCode.join(''))
    }
  }

  const handleVerifyCode = async (fullCode) => {
    if (fullCode.length !== 6) return
    setCodeLoading(true)
    setCodeError('')
    const result = await login2FA(fullCode)
    if (result === true) {
      setVerifying(false)
      return
    }
    if (result?.expired) {
      setCodeError(result.msg || 'Sesión expirada. Ingrese credenciales nuevamente.')
      setVerifying(false)
      setCode(['', '', '', '', '', ''])
      return
    }
    setCodeError(result?.error || 'Código inválido')
    setCode(['', '', '', '', '', ''])
    inputsRef.current[0]?.focus()
    setCodeLoading(false)
  }

  const handleStartRecover = () => {
    setRecoverMode('password')
    setRecoverPassword('')
    setRecoverQrBase64('')
    setRecoverError('')
    setRecoverCode(['', '', '', '', '', ''])
    setRecoverCodeError('')
  }

  const handleRecoverPasswordSubmit = async () => {
    if (!recoverPassword) return
    setRecoverLoading(true)
    setRecoverError('')
    const result = await recover2FA(recoverPassword)
    if (result?.qr_base64) {
      setRecoverQrBase64(result.qr_base64)
      setRecoverMode('qr')
      setTimeout(() => recoverInputsRef.current[0]?.focus(), 100)
    } else {
      setRecoverError(result?.error || 'Error al verificar contraseña')
    }
    setRecoverLoading(false)
  }

  const handleRecoverCodeChange = (index, value) => {
    if (value && !/^\d$/.test(value)) return
    const newCode = [...recoverCode]
    newCode[index] = value
    setRecoverCode(newCode)
    if (value && index < 5) {
      recoverInputsRef.current[index + 1]?.focus()
    }
  }

  const handleRecoverCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !recoverCode[index] && index > 0) {
      recoverInputsRef.current[index - 1]?.focus()
    }
  }

  const handleRecoverCodePaste = (e) => {
    e.preventDefault()
    const pasted = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      const newCode = pasted.split('')
      setRecoverCode(newCode)
      recoverInputsRef.current[5]?.focus()
      handleRecoverVerify(newCode.join(''))
    }
  }

  const handleRecoverVerify = async (fullCode) => {
    if (fullCode.length !== 6) return
    setRecoverCodeLoading(true)
    setRecoverCodeError('')
    const result = await recoverVerify2FA(fullCode)
    if (result === true) {
      setRecoverMode(null)
      setVerifying(false)
      return
    }
    if (result?.expired) {
      setRecoverCodeError(result.msg || 'Sesión expirada. Inicie sesión nuevamente.')
      setRecoverMode(null)
      setVerifying(false)
      setCode(['', '', '', '', '', ''])
      return
    }
    setRecoverCodeError(result?.error || 'Código inválido')
    setRecoverCode(['', '', '', '', '', ''])
    recoverInputsRef.current[0]?.focus()
    setRecoverCodeLoading(false)
  }

  const fullRecoverCode = recoverCode.join('')
  useEffect(() => {
    if (fullRecoverCode.length === 6 && !recoverCodeLoading) {
      handleRecoverVerify(fullRecoverCode)
    }
  }, [fullRecoverCode])

  // Auto-submit when 6 digits entered
  const fullCode = code.join('')
  useEffect(() => {
    if (fullCode.length === 6 && !codeLoading) {
      handleVerifyCode(fullCode)
    }
  }, [fullCode])

  const renderLoginForm = () => (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#4a5568', fontWeight: 500, fontSize: '0.9rem' }}>Usuario</label>
        <div style={{ position: 'relative' }}>
          <span style={{ position: 'absolute', left: '15px', top: '50%', transform: 'translateY(-50%)', color: '#a0aec0' }}>👤</span>
          <input
            type="text" value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Ingresa tu usuario" required
            style={{
              width: '100%', padding: '14px 16px 14px 45px',
              border: '2px solid #e2e8f0', borderRadius: '12px',
              fontSize: '1rem', fontFamily: "'Poppins', sans-serif",
              outline: 'none', boxSizing: 'border-box',
            }}
            onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
            onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
          />
        </div>
      </div>
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#4a5568', fontWeight: 500, fontSize: '0.9rem' }}>Contraseña</label>
        <div style={{ position: 'relative' }}>
          <span style={{ position: 'absolute', left: '15px', top: '50%', transform: 'translateY(-50%)', color: '#a0aec0' }}>🔒</span>
          <input
            type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Ingresa tu contraseña" required
            style={{
              width: '100%', padding: '14px 16px 14px 45px',
              border: '2px solid #e2e8f0', borderRadius: '12px',
              fontSize: '1rem', fontFamily: "'Poppins', sans-serif",
              outline: 'none', boxSizing: 'border-box',
            }}
            onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
            onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
          />
        </div>
      </div>
      <button type="submit" disabled={loading} style={{
        width: '100%', padding: '16px',
        background: loading ? '#a0aec0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white', border: 'none', borderRadius: '12px',
        fontSize: '1rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease', fontFamily: "'Poppins', sans-serif",
      }}
        onMouseEnter={e => { if (!loading) { e.target.style.transform = 'translateY(-2px)'; e.target.style.boxShadow = '0 10px 20px rgba(102,126,234,0.3)' } }}
        onMouseLeave={e => { e.target.style.transform = 'none'; e.target.style.boxShadow = 'none' }}
      >
        {loading ? 'Verificando...' : 'Iniciar Sesión'}
      </button>

      {isDemoMode && (
        <button
          type="button"
          onClick={retryDemoLogin}
          style={{
            marginTop: '12px',
            width: '100%',
            padding: '12px',
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: '#6366f1',
            borderRadius: '12px',
            fontSize: '0.9rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          ⚡ Iniciar en Modo Demo (Auto-login)
        </button>
      )}
    </form>
  )

  const renderCodeInput = () => (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <div style={{ fontSize: '48px', marginBottom: '15px' }}>🔐</div>
        <h2 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '8px' }}>Autenticación en Dos Pasos</h2>
        <p style={{ color: '#666', fontSize: '0.9rem' }}>
          Ingresa el código de 6 dígitos de <strong>Google Authenticator</strong>
        </p>
      </div>

      {qrRecovery && (
        <div style={{
          background: '#fff3cd', color: '#856404', padding: '16px',
          borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
          textAlign: 'center',
        }}>
          <p style={{ fontWeight: 600, marginBottom: '10px' }}>⚠️ Tu código QR ha sido regenerado</p>
          <p style={{ marginBottom: '12px' }}>Escanea este QR nuevamente con <strong>Google Authenticator</strong>:</p>
          <img src={`data:image/png;base64,${qrRecovery}`} alt="QR Recovery"
            style={{ width: '160px', height: '160px', borderRadius: '10px', border: '2px solid #856404' }} />
        </div>
      )}

      {codeError && (
        <div style={{
          background: '#fed7d7', color: '#c53030', padding: '12px 16px',
          borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
          textAlign: 'center',
        }}>
          ⚠️ {codeError}
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '30px' }}
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
              width: '52px', height: '60px',
              textAlign: 'center', fontSize: '1.5rem', fontWeight: 700,
              border: `2px solid ${codeError ? '#e74c3c' : '#e2e8f0'}`,
              borderRadius: '12px',
              outline: 'none', fontFamily: "'Poppins', sans-serif",
              color: '#333', background: digit ? '#f7fafc' : 'white',
              caretColor: '#667eea',
            }}
            onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
            onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
          />
        ))}
      </div>

      <div style={{ textAlign: 'center', marginTop: '15px' }}>
        <button onClick={() => { setVerifying(false); setCode(['', '', '', '', '', '']); setCodeError(''); setQrRecovery(null) }}
          style={{
            background: 'none', border: 'none', color: '#667eea',
            cursor: 'pointer', fontSize: '0.85rem', textDecoration: 'underline',
            fontFamily: "'Poppins', sans-serif",
          }}>
          ← Volver al inicio de sesión
        </button>
      </div>

      <div style={{ textAlign: 'center', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
        <button onClick={handleStartRecover}
          style={{
            background: 'none', border: 'none', color: '#e74c3c',
            cursor: 'pointer', fontSize: '0.8rem', textDecoration: 'underline',
            fontFamily: "'Poppins', sans-serif",
          }}>
          🔐 ¿Perdiste acceso a tu autenticador?
        </button>
      </div>
    </div>
  )

  const renderRecoverPassword = () => (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <div style={{ fontSize: '48px', marginBottom: '15px' }}>🔐</div>
        <h2 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '8px' }}>Recuperar Acceso</h2>
        <p style={{ color: '#666', fontSize: '0.9rem' }}>
          Ingresa tu <strong>contraseña</strong> para generar un nuevo código QR
        </p>
      </div>

      {recoverError && (
        <div style={{
          background: '#fed7d7', color: '#c53030', padding: '12px 16px',
          borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
          textAlign: 'center',
        }}>
          ⚠️ {recoverError}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#4a5568', fontWeight: 500, fontSize: '0.9rem' }}>Contraseña</label>
        <div style={{ position: 'relative' }}>
          <span style={{ position: 'absolute', left: '15px', top: '50%', transform: 'translateY(-50%)', color: '#a0aec0' }}>🔒</span>
          <input
            type="password" value={recoverPassword}
            onChange={e => setRecoverPassword(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleRecoverPasswordSubmit() }}
            placeholder="Ingresa tu contraseña" required
            style={{
              width: '100%', padding: '14px 16px 14px 45px',
              border: '2px solid #e2e8f0', borderRadius: '12px',
              fontSize: '1rem', fontFamily: "'Poppins', sans-serif",
              outline: 'none', boxSizing: 'border-box',
            }}
            onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
            onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
          />
        </div>
      </div>

      <button onClick={handleRecoverPasswordSubmit} disabled={recoverLoading || !recoverPassword} style={{
        width: '100%', padding: '16px',
        background: recoverLoading || !recoverPassword ? '#a0aec0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white', border: 'none', borderRadius: '12px',
        fontSize: '1rem', fontWeight: 600, cursor: recoverLoading || !recoverPassword ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease', fontFamily: "'Poppins', sans-serif",
      }}>
        {recoverLoading ? 'Verificando...' : 'Generar Nuevo QR'}
      </button>

      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <button onClick={() => { setRecoverMode(null); setRecoverError(''); setRecoverPassword('') }}
          style={{
            background: 'none', border: 'none', color: '#667eea',
            cursor: 'pointer', fontSize: '0.85rem', textDecoration: 'underline',
            fontFamily: "'Poppins', sans-serif",
          }}>
          ← Cancelar
        </button>
      </div>
    </div>
  )

  const renderRecoverQr = () => (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <div style={{ fontSize: '48px', marginBottom: '15px' }}>📱</div>
        <h2 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '8px' }}>Vincula tu Autenticador</h2>
        <p style={{ color: '#666', fontSize: '0.85rem', marginBottom: '15px' }}>
          Escanea el código QR con <strong>Google Authenticator</strong>
        </p>
      </div>

      {recoverQrBase64 && (
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <img src={`data:image/png;base64,${recoverQrBase64}`} alt="QR Code"
            style={{ width: '180px', height: '180px', borderRadius: '12px', border: '2px solid #e2e8f0' }} />
        </div>
      )}

      <p style={{ textAlign: 'center', color: '#4a5568', fontWeight: 500, fontSize: '0.85rem', marginBottom: '15px' }}>
        Luego ingresa el código de 6 dígitos generado:
      </p>

      {recoverCodeError && (
        <div style={{
          background: '#fed7d7', color: '#c53030', padding: '12px 16px',
          borderRadius: '10px', marginBottom: '20px', fontSize: '0.85rem',
          textAlign: 'center',
        }}>
          ⚠️ {recoverCodeError}
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}
        onPaste={handleRecoverCodePaste}>
        {recoverCode.map((digit, i) => (
          <input
            key={i}
            ref={el => recoverInputsRef.current[i] = el}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={e => handleRecoverCodeChange(i, e.target.value)}
            onKeyDown={e => handleRecoverCodeKeyDown(i, e)}
            style={{
              width: '52px', height: '60px',
              textAlign: 'center', fontSize: '1.5rem', fontWeight: 700,
              border: `2px solid ${recoverCodeError ? '#e74c3c' : '#e2e8f0'}`,
              borderRadius: '12px',
              outline: 'none', fontFamily: "'Poppins', sans-serif",
              color: '#333', background: digit ? '#f7fafc' : 'white',
              caretColor: '#667eea',
            }}
            onFocus={e => { e.target.style.borderColor = '#667eea'; e.target.style.boxShadow = '0 0 0 3px rgba(102,126,234,0.15)' }}
            onBlur={e => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
          />
        ))}
      </div>

      <div style={{ textAlign: 'center' }}>
        <button onClick={() => { setRecoverMode('password'); setRecoverCode(['', '', '', '', '', '']); setRecoverCodeError('') }}
          style={{
            background: 'none', border: 'none', color: '#667eea',
            cursor: 'pointer', fontSize: '0.85rem', textDecoration: 'underline',
            fontFamily: "'Poppins', sans-serif",
          }}>
          ← Volver a ingresar contraseña
        </button>
      </div>
    </div>
  )

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px',
      fontFamily: "'Poppins', sans-serif",
    }}>
      <div className="login-card" style={{
        display: 'flex',
        background: 'white',
        borderRadius: '20px',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
        overflow: 'hidden',
        maxWidth: '900px',
        width: '100%',
      }}>
        <div style={{
          flex: 1,
          background: 'linear-gradient(135deg, rgba(102,126,234,0.9), rgba(118,75,162,0.9))',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '40px',
          color: 'white',
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80" width="200" height="80">
            <defs>
              <linearGradient id="panGradLogin" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#fff"/>
                <stop offset="100%" stopColor="#e8e8e8"/>
              </linearGradient>
            </defs>
            <rect x="10" y="10" width="60" height="60" rx="15" fill="url(#panGradLogin)"/>
            <ellipse cx="40" cy="45" rx="22" ry="17" fill="#e8c9a0"/>
            <ellipse cx="40" cy="42" rx="19" ry="14" fill="#f5deb3"/>
            <path d="M25 38 Q40 30 55 38" stroke="#c9956c" strokeWidth="2.5" fill="none"/>
            <path d="M28 44 Q40 36 52 44" stroke="#c9956c" strokeWidth="2.5" fill="none"/>
            <path d="M31 50 Q40 42 49 50" stroke="#c9956c" strokeWidth="2.5" fill="none"/>
            <ellipse cx="32" cy="36" rx="5" ry="3" fill="#fff5e6" opacity="0.7"/>
            <text x="80" y="35" fontFamily="Poppins, Arial, sans-serif" fontSize="18" fontWeight="700" fill="white" letterSpacing="2">VICTORIA</text>
            <text x="80" y="58" fontFamily="Poppins, Arial, sans-serif" fontSize="14" fontWeight="400" fill="rgba(255,255,255,0.8)" letterSpacing="4">PANADERÍA</text>
          </svg>
          <p style={{ marginTop: '15px', textAlign: 'center' }}>Sistema de Gestión Predictiva</p>
          {!verifying && (
            <div style={{ marginTop: '20px', fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
              <p>🔐 Autenticación de Doble Factor</p>
              <p style={{ fontSize: '0.75rem', marginTop: '5px' }}>Google Authenticator requerido</p>
            </div>
          )}
        </div>
        <div style={{
          flex: 1,
          padding: '50px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          {!verifying ? (
            <>
              <h2 style={{ fontSize: '1.8rem', color: '#333', marginBottom: '10px' }}>Bienvenido</h2>
              <p style={{ color: '#666', marginBottom: '30px', fontSize: '0.95rem' }}>Ingresa tus credenciales para continuar</p>

              {error && (
                <div style={{
                  background: '#fed7d7', color: '#c53030', padding: '12px 16px',
                  borderRadius: '10px', marginBottom: '20px', fontSize: '0.9rem',
                  display: 'flex', alignItems: 'center', gap: '10px',
                }}>
                  <span>⚠️</span> {error}
                </div>
              )}

              {renderLoginForm()}

              <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
                <h4 style={{ color: '#4a5568', fontSize: '0.85rem', marginBottom: '12px' }}>Roles disponibles:</h4>
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px',
                  fontSize: '0.8rem', color: '#718096',
                }}>
                  {[
                    { label: 'Administrador', cls: '#fed7e2', color: '#ed64a6', letter: 'A' },
                    { label: 'Gerente', cls: '#c6f6d5', color: '#48bb78', letter: 'G' },
                    { label: 'Vendedor', cls: '#bee3f8', color: '#4299e1', letter: 'V' },
                    { label: 'Cocina', cls: '#feebc8', color: '#ed8936', letter: 'C' },
                  ].map(r => (
                    <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        width: '24px', height: '24px', borderRadius: '6px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.7rem', background: r.cls, color: r.color, fontWeight: 600,
                      }}>{r.letter}</span>
                      {r.label}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : recoverMode === 'password' ? (
            renderRecoverPassword()
          ) : recoverMode === 'qr' ? (
            renderRecoverQr()
          ) : (
            renderCodeInput()
          )}
        </div>
      </div>
    </div>
  )
}
