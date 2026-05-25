import { createContext, useContext, useState } from 'react'
import { api } from '../api/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('pv_user')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })

  // 2FA states
  const [requires2fa, setRequires2fa] = useState(false)
  const [sessionToken, setSessionToken] = useState(null)
  const [pendingUsername, setPendingUsername] = useState(null)
  const [debeConfigurar2fa, setDebeConfigurar2fa] = useState(false)
  const [qrData, setQrData] = useState(null) // { qr_base64, secret, uri }
  const [qrRecovery, setQrRecovery] = useState(null) // base64 QR for repairing corrupted 2FA

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
        // Redirigir al login
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
  }

  return (
    <AuthContext.Provider value={{
      user, login, logout,
      requires2fa, sessionToken, pendingUsername, debeConfigurar2fa, qrData, qrRecovery,
      login2FA, setup2FA, verifySetup2FA, disable2FA, recover2FA, recoverVerify2FA, clear2FAState, setDebeConfigurar2fa, setQrRecovery,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
