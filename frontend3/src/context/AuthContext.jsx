import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api/api'

const IS_DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'
const DEMO_USERNAME = import.meta.env.VITE_DEMO_USERNAME || 'admin'
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || 'admin'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('autologin') === 'admin') {
      return { username: 'admin', rol: 'administrador', vendedor_id: null }
    }
    try {
      const saved = localStorage.getItem('pv_user')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })

  // Demo Mode & Warmup states
  const [isDemoLoading, setIsDemoLoading] = useState(false)
  const [demoElapsed, setDemoElapsed] = useState(0)
  const [demoAttempts, setDemoAttempts] = useState(0)
  const [demoError, setDemoError] = useState(null)
  const [cancelAutoLogin, setCancelAutoLogin] = useState(false)

  // 2FA states
  const [requires2fa, setRequires2fa] = useState(false)
  const [sessionToken, setSessionToken] = useState(null)
  const [pendingUsername, setPendingUsername] = useState(null)
  const [debeConfigurar2fa, setDebeConfigurar2fa] = useState(false)
  const [qrData, setQrData] = useState(null) // { qr_base64, secret, uri }
  const [qrRecovery, setQrRecovery] = useState(null) // base64 QR for repairing corrupted 2FA

  // Auto-login loop when IS_DEMO_MODE is active and user is not logged in
  useEffect(() => {
    if (IS_DEMO_MODE && !user && !cancelAutoLogin) {
      setIsDemoLoading(true)
      let isMounted = true
      let timerId = null

      setDemoElapsed(0)
      setDemoAttempts(0)
      setDemoError(null)

      const startTime = Date.now()
      timerId = setInterval(() => {
        if (isMounted) {
          setDemoElapsed(Math.floor((Date.now() - startTime) / 1000))
        }
      }, 1000)

      const runAutoLogin = async () => {
        let attempts = 0
        while (isMounted && !user) {
          attempts++
          if (isMounted) setDemoAttempts(attempts)

          try {
            const res = await api.post('/auth/login', {
              username: DEMO_USERNAME,
              password: DEMO_PASSWORD,
            })

            if (res && res.username) {
              const u = { username: res.username, rol: res.rol, vendedor_id: res.vendedor_id }
              if (isMounted) {
                setUser(u)
                localStorage.setItem('pv_user', JSON.stringify(u))
                setIsDemoLoading(false)
              }
              break
            }
          } catch (err) {
            if (!isMounted) break
            const isNetworkErr = !err.response || err.name === 'AbortError' || err.message?.includes('Fetch') || err.message?.includes('HTTP 502') || err.message?.includes('HTTP 503') || err.message?.includes('HTTP 504')
            const msg = isNetworkErr
              ? 'El servidor backend se está despertando en Render...'
              : (err?.response?.data?.detail || 'Reintentando conexión con la API...')
            setDemoError(msg)
            await new Promise((resolve) => setTimeout(resolve, 3000))
          }
        }
      }

      runAutoLogin()

      return () => {
        isMounted = false
        if (timerId) clearInterval(timerId)
      }
    }
  }, [user, cancelAutoLogin])

  const retryDemoLogin = useCallback(() => {
    setCancelAutoLogin(false)
    setDemoElapsed(0)
    setDemoAttempts(0)
    setDemoError(null)
  }, [])

  const skipAutoLogin = useCallback(() => {
    setCancelAutoLogin(true)
    setIsDemoLoading(false)
  }, [])

  async function login(username, password) {
    try {
      const res = await api.post('/auth/login', { username, password })

      if (res.requiere_2fa) {
        setRequires2fa(true)
        setSessionToken(res.session_token)
        setPendingUsername(res.username)
        if (res.qr_recovery) {
          setQrRecovery(res.qr_recovery)
        }
        return { requiere_2fa: true, qr_recovery: res.qr_recovery }
      }

      if (res.debe_configurar_2fa) {
        const u = { username: res.username, rol: res.rol, vendedor_id: res.vendedor_id }
        setUser(u)
        localStorage.setItem('pv_user', JSON.stringify(u))
        setDebeConfigurar2fa(true)
        return { debe_configurar_2fa: true }
      }

      const u = { username: res.username, rol: res.rol, vendedor_id: res.vendedor_id }
      setUser(u)
      localStorage.setItem('pv_user', JSON.stringify(u))
      return true
    } catch {
      return false
    }
  }

  async function login2FA(totpCode) {
    try {
      const res = await api.post('/auth/login-2fa', {
        username: pendingUsername,
        session_token: sessionToken,
        totp_code: totpCode,
      })
      const u = { username: res.username, rol: res.rol, vendedor_id: res.vendedor_id }
      setUser(u)
      localStorage.setItem('pv_user', JSON.stringify(u))
      setRequires2fa(false)
      setSessionToken(null)
      setPendingUsername(null)
      setQrRecovery(null)
      return true
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Error'
      if (msg.includes('Demasiados intentos')) {
        setRequires2fa(false)
        setSessionToken(null)
        setPendingUsername(null)
        return { expired: true, msg }
      }
      return { error: msg }
    }
  }

  async function setup2FA(username, password) {
    try {
      const res = await api.post('/auth/setup-2fa', { username, password })
      setQrData({
        qr_base64: res.qr_base64,
        secret: res.secret,
        uri: res.uri,
      })
      return true
    } catch {
      return false
    }
  }

  async function verifySetup2FA(username, code) {
    try {
      const res = await api.post('/auth/verify-2fa', { username, totp_code: code })
      if (res.success) {
        setDebeConfigurar2fa(false)
        setQrData(null)
        return true
      }
      return false
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Error'
      if (msg.includes('Demasiados intentos')) {
        setDebeConfigurar2fa(false)
        setQrData(null)
        logout()
        return { expired: true, msg }
      }
      return { error: msg }
    }
  }

  async function disable2FA(username, password) {
    try {
      await api.post('/auth/disable-2fa', { username, password })
      return true
    } catch {
      return false
    }
  }

  async function recover2FA(password) {
    try {
      const res = await api.post('/auth/recover-2fa', {
        username: pendingUsername,
        session_token: sessionToken,
        password,
      })
      return { qr_base64: res.qr_base64 }
    } catch (err) {
      return { error: err?.response?.data?.detail || 'Error al verificar contraseña' }
    }
  }

  async function recoverVerify2FA(totpCode) {
    try {
      const res = await api.post('/auth/recover-verify', {
        username: pendingUsername,
        session_token: sessionToken,
        totp_code: totpCode,
      })
      const u = { username: res.username, rol: res.rol, vendedor_id: res.vendedor_id }
      setUser(u)
      localStorage.setItem('pv_user', JSON.stringify(u))
      setRequires2fa(false)
      setSessionToken(null)
      setPendingUsername(null)
      setQrRecovery(null)
      return true
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Error'
      if (msg.includes('Demasiados intentos')) {
        setRequires2fa(false)
        setSessionToken(null)
        setPendingUsername(null)
        return { expired: true, msg }
      }
      return { error: msg }
    }
  }

  function clear2FAState() {
    setRequires2fa(false)
    setSessionToken(null)
    setPendingUsername(null)
    setDebeConfigurar2fa(false)
    setQrData(null)
  }

  function logout() {
    setUser(null)
    clear2FAState()
    localStorage.removeItem('pv_user')
    if (IS_DEMO_MODE) {
      setCancelAutoLogin(true)
      setIsDemoLoading(false)
    }
  }

  return (
    <AuthContext.Provider value={{
      user, login, logout,
      requires2fa, sessionToken, pendingUsername, debeConfigurar2fa, qrData, qrRecovery,
      login2FA, setup2FA, verifySetup2FA, disable2FA, recover2FA, recoverVerify2FA, clear2FAState, setDebeConfigurar2fa, setQrRecovery,
      // Demo Mode exports
      isDemoMode: IS_DEMO_MODE,
      isDemoLoading,
      demoElapsed,
      demoAttempts,
      demoError,
      retryDemoLogin,
      skipAutoLogin,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
