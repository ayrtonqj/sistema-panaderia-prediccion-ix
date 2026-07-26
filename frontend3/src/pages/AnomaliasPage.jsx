import { useState, useEffect } from 'react'
import { api } from '../api/api'

export default function AnomaliasPage() {
  const [anomalias, setAnomalias] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filtro, setFiltro] = useState('todas')

  const fetchAnomalias = async () => {
    try {
      setLoading(true)
      const data = await api.get('/sistema/anomalias')
      setAnomalias(Array.isArray(data) ? data : data.anomalias || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAnomalias() }, [])

  const getSeveridadClass = (severidad) => {
    if (!severidad) return ''
    const s = severidad.toLowerCase()
    if (s === 'alta' || s === 'critica') return 'badge-danger'
    if (s === 'media') return 'badge-warning'
    return 'badge-info'
  }

  const filtradas = filtro === 'todas'
    ? anomalias
    : anomalias.filter(a => (a.severidad || '').toLowerCase() === filtro)

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🔍 Anomalías del Sistema</h1>
        <button className="btn-secondary" onClick={fetchAnomalias}>↻ Actualizar</button>
      </div>

      <div className="filter-bar">
        {['todas', 'alta', 'media', 'baja'].map(f => (
          <button
            key={f}
            className={`filter-btn ${filtro === f ? 'active' : ''}`}
            onClick={() => setFiltro(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading && <p className="loading-text">Analizando datos...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <div className="cards-grid">
          {filtradas.length === 0 ? (
            <div className="empty-state">
              <span style={{ fontSize: '3rem' }}>✅</span>
              <p>No se detectaron anomalías{filtro !== 'todas' ? ` de severidad ${filtro}` : ''}.</p>
            </div>
          ) : filtradas.map((a, i) => (
            <div key={i} className={`anomalia-card ${getSeveridadClass(a.severidad)}`}>
              <div className="anomalia-header">
                <span className={`badge ${getSeveridadClass(a.severidad)}`}>{a.severidad || 'Desconocida'}</span>
                <span className="anomalia-fecha">{a.fecha || a.created_at || ''}</span>
              </div>
              <h3>{a.tipo || a.title || 'Anomalía detectada'}</h3>
              <p>{a.descripcion || a.description || JSON.stringify(a)}</p>
              {a.producto && <p><strong>Producto:</strong> {a.producto}</p>}
              {a.valor && <p><strong>Valor:</strong> {a.valor}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
