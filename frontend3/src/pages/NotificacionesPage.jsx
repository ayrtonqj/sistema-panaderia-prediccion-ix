import { useState, useEffect } from 'react'
import { api } from '../api/api'

export default function NotificacionesPage() {
  const [notificaciones, setNotificaciones] = useState([])
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('historial')
  const [configForm, setConfigForm] = useState({ telegram_chat_id: '', email_destino: '', alertas_activas: true })

  const fetchNotificaciones = async () => {
    try {
      setLoading(true)
      const data = await api.get('/sistema/notificaciones')
      setNotificaciones(Array.isArray(data) ? data : data.notificaciones || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchConfig = async () => {
    try {
      const data = await api.get('/sistema/notificaciones/config')
      setConfig(data)
      setConfigForm({ telegram_chat_id: data.telegram_chat_id || '', email_destino: data.email_destino || '', alertas_activas: data.alertas_activas ?? true })
    } catch {}
  }

  useEffect(() => {
    fetchNotificaciones()
    fetchConfig()
  }, [])

  const handleSaveConfig = async (e) => {
    e.preventDefault()
    try {
      await api.put('/sistema/notificaciones/config', configForm)
      alert('Configuración guardada correctamente')
      fetchConfig()
    } catch (e) {
      alert(e.message)
    }
  }

  const getTipoIcon = (tipo) => {
    if (!tipo) return '🔔'
    const t = tipo.toLowerCase()
    if (t.includes('error') || t.includes('alerta')) return '⚠️'
    if (t.includes('stock') || t.includes('inventario')) return '📦'
    if (t.includes('venta')) return '💰'
    if (t.includes('prediccion') || t.includes('predicción')) return '🔮'
    return '🔔'
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🔔 Notificaciones</h1>
        <button className="btn-secondary" onClick={fetchNotificaciones}>↻ Actualizar</button>
      </div>

      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'historial' ? 'active' : ''}`} onClick={() => setTab('historial')}>
          Historial
        </button>
        <button className={`tab-btn ${tab === 'config' ? 'active' : ''}`} onClick={() => setTab('config')}>
          ⚙️ Configuración
        </button>
      </div>

      {tab === 'historial' && (
        <>
          {loading && <p className="loading-text">Cargando notificaciones...</p>}
          {error && <p className="error-text">{error}</p>}
          {!loading && !error && (
            <div className="notif-list">
              {notificaciones.length === 0 ? (
                <div className="empty-state">
                  <span style={{ fontSize: '3rem' }}>🔕</span>
                  <p>No hay notificaciones registradas.</p>
                </div>
              ) : notificaciones.map((n, i) => (
                <div key={i} className={`notif-item ${n.leida ? 'leida' : 'no-leida'}`}>
                  <span className="notif-icon">{getTipoIcon(n.tipo)}</span>
                  <div className="notif-body">
                    <p className="notif-mensaje">{n.mensaje || n.message || JSON.stringify(n)}</p>
                    <span className="notif-meta">
                      {n.tipo || 'Sistema'} · {n.fecha || n.created_at || ''}
                    </span>
                  </div>
                  {!n.leida && <span className="notif-badge">Nueva</span>}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'config' && (
        <div className="config-panel">
          <h2>Configuración de Alertas</h2>
          <form onSubmit={handleSaveConfig} className="form-grid">
            <label>Telegram Chat ID
              <input
                value={configForm.telegram_chat_id}
                onChange={e => setConfigForm({ ...configForm, telegram_chat_id: e.target.value })}
                placeholder="Ej: 123456789"
              />
            </label>
            <label>Email destino
              <input
                type="email"
                value={configForm.email_destino}
                onChange={e => setConfigForm({ ...configForm, email_destino: e.target.value })}
                placeholder="correo@ejemplo.com"
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={configForm.alertas_activas}
                onChange={e => setConfigForm({ ...configForm, alertas_activas: e.target.checked })}
              />
              Alertas activas
            </label>
            <div className="form-actions">
              <button type="submit" className="btn-primary">Guardar configuración</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
