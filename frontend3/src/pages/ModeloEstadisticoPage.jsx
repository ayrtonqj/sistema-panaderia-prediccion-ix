import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'

export default function ModeloEstadisticoPage() {
  const [metricas, setMetricas] = useState(null)
  const [estado, setEstado] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mlResult, setMlResult] = useState('')

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/ml/metricas'),
      api.get('/sistema/estado'),
    ]).then(([met, est]) => {
      setMetricas(met)
      setEstado(est)
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const cargarSeed = async () => {
    setMlResult('⏳ Cargando datos de prueba...')
    try {
      const data = await api.post('/datos/semilla')
      setMlResult(`✅ ${data.mensaje || 'Datos cargados correctamente'}`)
      setTimeout(() => { setMlResult(''); fetchData() }, 1500)
    } catch (err) {
      setMlResult(`⚠️ Error: ${err.message}`)
    }
  }

  const completarDatos = async () => {
    setMlResult('⏳ Generando datos para productos nuevos...')
    try {
      const data = await api.post('/datos/completar')
      setMlResult(`✅ ${data.mensaje || 'Datos completados'}`)
      setTimeout(() => { setMlResult(''); fetchData() }, 1500)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Error desconocido'
      setMlResult(`⚠️ Error: ${detail}`)
    }
  }

  const entrenarModelos = async () => {
    setMlResult('⏳ Entrenando modelos (esto puede tomar unos minutos)...')
    try {
      const data = await api.post('/ml/entrenar')
      const count = data?.productos_con_modelo || data?.modelos?.length || 0
      setMlResult(`✅ ${count} modelos entrenados correctamente`)
      setTimeout(() => { setMlResult(''); fetchData() }, 2000)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Error desconocido'
      setMlResult(`⚠️ Error: ${detail}`)
    }
  }

  const sincronizarClima = async () => {
    setMlResult('⏳ Sincronizando clima...')
    try {
      const data = await api.post('/clima/sincronizar?dias=7')
      setMlResult(`✅ Clima sincronizado: ${data.registros_insertados || 0} nuevos, ${data.registros_actualizados || 0} actualizados`)
      setTimeout(() => setMlResult(''), 3000)
    } catch (err) {
      setMlResult(`⚠️ Error: ${err.message}`)
    }
  }

  const r2Color = (r2) => {
    if (r2 > 0.7) return '#27ae60'
    if (r2 > 0.5) return '#f39c12'
    return '#e74c3c'
  }

  if (loading) return <div className="card"><p>Cargando...</p></div>

  return (
    <>
      <div className="page-header">
          <h1>📈 Estadísticas del Modelo</h1>
        <p style={{ color: '#8892a4' }}>Panel técnico del sistema de Machine Learning</p>
      </div>

      <div className="card">
        <h3>⚙️ Control del Sistema ML</h3>
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <button className="btn" onClick={cargarSeed}>📊 Cargar Datos de Prueba (Seed)</button>
          <button className="btn" onClick={completarDatos}>🔄 Completar Datos Faltantes</button>
          <button className="btn" onClick={entrenarModelos}>🧠 Entrenar Modelos</button>
          <button className="btn" onClick={sincronizarClima}>🌤️ Sincronizar Clima</button>
        </div>
        {mlResult && (
          <p style={{
            marginTop: '10px',
            color: mlResult.includes('✅') ? '#27ae60' : mlResult.includes('⚠️') ? '#e74c3c' : '#667eea',
          }}>{mlResult}</p>
        )}
      </div>

      {metricas && metricas.modelos && metricas.modelos.length > 0 ? (
        <div className="card">
          <h3>Métricas de Rendimiento de Modelos</h3>
          <Pagination
            data={metricas.modelos}
            pageSize={20}
            columns={['Producto', 'R²', 'MAE', 'RMSE', 'Estado']}
            renderRow={(m) => (
              <tr key={m.producto_id || m.producto_nombre}>
                <td>{m.producto_nombre}</td>
                <td style={{ color: m.r2 ? r2Color(m.r2) : undefined }}>
                  {m.r2 ? m.r2.toFixed(3) : '—'}
                </td>
                <td>{m.mae ? m.mae.toFixed(2) : '—'}</td>
                <td>{m.rmse ? m.rmse.toFixed(2) : '—'}</td>
                <td>
                  {m.modelo_disponible
                    ? <span style={{ color: '#27ae60' }}>✅ Entrenado</span>
                    : <span style={{ color: '#e74c3c' }}>⚠️ Sin entrenar</span>}
                </td>
              </tr>
            )}
          />
        </div>
      ) : (
        <div className="card">
          <h3>Métricas de Rendimiento</h3>
          <p style={{ color: '#8892a4' }}>No hay modelos entrenados. Carga datos de prueba y entrena los modelos.</p>
        </div>
      )}

      {estado && (
        <div className="grid-2">
          <div className="card">
            <h3>📊 Base de Datos</h3>
            <table style={{ width: '100%' }}>
              <tbody>
                {estado.base_de_datos && Object.entries(estado.base_de_datos).map(([key, val]) => (
                  <tr key={key}>
                    <td style={{
                      textTransform: 'capitalize',
                      borderBottom: '1px solid var(--border-color)',
                      padding: '10px 0',
                    }}>
                      {key.replace(/_/g, ' ')}
                    </td>
                    <td style={{
                      textAlign: 'right',
                      color: '#667eea',
                      fontWeight: 600,
                      borderBottom: '1px solid var(--border-color)',
                      padding: '10px 0',
                    }}>{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <h3>🤖 Machine Learning</h3>
            {estado.machine_learning && (
              <>
                <table style={{ width: '100%' }}>
                  <tbody>
                    <tr>
                      <td style={{ padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>Modelos Entrenados</td>
                      <td style={{ textAlign: 'right', color: '#27ae60', fontWeight: 600, padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>
                        {estado.machine_learning.modelos_listos}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>Total Productos</td>
                      <td style={{ textAlign: 'right', color: '#667eea', fontWeight: 600, padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>
                        {estado.machine_learning.total_productos}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: '10px 0' }}>Todos Entrenados</td>
                      <td style={{ textAlign: 'right', color: estado.machine_learning.todos_entrenados ? '#27ae60' : '#e74c3c', fontWeight: 600, padding: '10px 0' }}>
                        {estado.machine_learning.todos_entrenados ? '✅ Sí' : '❌ No'}
                      </td>
                    </tr>
                  </tbody>
                </table>
                {estado.machine_learning.detalle && (
                  <>
                    <br />
                    <h4>Detalle por Producto:</h4>
                    <div className="table-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      <table>
                        <thead><tr><th>Producto</th><th>Entrenado</th><th>R²</th></tr></thead>
                        <tbody>
                          {estado.machine_learning.detalle.map((d, i) => (
                            <tr key={i}>
                              <td>{d.producto}</td>
                              <td>{d.entrenado ? '✅' : '⚠️'}</td>
                              <td>{d.r2 ? d.r2.toFixed(3) : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {estado && estado.servicios && (
        <div className="card">
          <h3>🔗 Servicios del Sistema</h3>
          <div className="grid-4">
            {Object.entries(estado.servicios).map(([key, val]) => (
              <div className="metric" key={key}>
                <div className="value" style={{ fontSize: '14px' }}>{val || '—'}</div>
                <div className="label">{key}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
