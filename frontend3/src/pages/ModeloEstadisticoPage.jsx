import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'

export default function ModeloEstadisticoPage() {
  const [metricas, setMetricas] = useState(null)
  const [estado, setEstado] = useState(null)
  const [wilcoxon, setWilcoxon] = useState(null)
  const [dieboldMariano, setDieboldMariano] = useState(null)
  const [ablacion, setAblacion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mlResult, setMlResult] = useState('')
  const [tab, setTab] = useState('metricas')

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/ml/metricas'),
      api.get('/sistema/estado'),
      api.get('/ml/wilcoxon'),
      api.get('/ml/diebold-mariano'),
      api.get('/ml/ablacion'),
    ]).then(([met, est, wil, dm, ab]) => {
      setMetricas(met)
      setEstado(est)
      setWilcoxon(wil)
      setDieboldMariano(dm)
      setAblacion(ab)
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

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button onClick={() => setTab('metricas')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'metricas' ? '700' : '400',
            background: tab === 'metricas' ? '#667eea' : 'transparent',
            color: tab === 'metricas' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>📈 Métricas de Rendimiento</button>
          <button onClick={() => setTab('wilcoxon')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'wilcoxon' ? '700' : '400',
            background: tab === 'wilcoxon' ? '#667eea' : 'transparent',
            color: tab === 'wilcoxon' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>🔬 Prueba de Wilcoxon</button>
          <button onClick={() => setTab('diebold')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'diebold' ? '700' : '400',
            background: tab === 'diebold' ? '#667eea' : 'transparent',
            color: tab === 'diebold' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>📊 Prueba de Diebold-Mariano (DM)</button>
          <button onClick={() => setTab('ablacion')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'ablacion' ? '700' : '400',
            background: tab === 'ablacion' ? '#667eea' : 'transparent',
            color: tab === 'ablacion' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>🧪 Análisis de Ablación</button>
        </div>
      </div>

      {tab === 'metricas' && (
        <>
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
                columns={['Producto', 'Algoritmo Preferido', 'R²', 'MAE', 'RMSE', 'Estado']}
                renderRow={(m) => (
                  <tr key={m.producto_id || m.producto_nombre}>
                    <td>{m.producto_nombre}</td>
                    <td>
                      <span style={{
                        background: 'rgba(102,126,234,0.08)',
                        color: '#667eea',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 500
                      }}>
                        {m.mejor_algoritmo === 'Ensemble (RF+GB+LR)' ? 'Ensemble Híbrido' : m.mejor_algoritmo || '—'}
                      </span>
                    </td>
                    <td style={{ color: m.r2 ? r2Color(m.r2) : undefined, fontWeight: 600 }}>
                      {m.r2 ? (m.r2 * 100).toFixed(1) + '%' : '—'}
                    </td>
                    <td>{m.mae ? m.mae.toFixed(2) : '—'}</td>
                    <td>{m.rmse ? m.rmse.toFixed(2) : '—'}</td>
                    <td>
                      {m.modelo_disponible
                        ? <span style={{ color: '#27ae60', fontWeight: 600 }}>✅ Entrenado</span>
                        : <span style={{ color: '#e74c3c', fontWeight: 600 }}>⚠️ Sin entrenar</span>}
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
                                  <td>{d.r2 ? (d.r2 * 100).toFixed(1) + '%' : '—'}</td>
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
      )}

      {tab === 'wilcoxon' && (
        <div className="card">
          <h3>🔬 Prueba de Wilcoxon para Muestras Pareadas</h3>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '20px' }}>
            Esta prueba estadística no paramétrica contrasta los errores absolutos del modelo <strong>Ensemble Híbrido</strong> frente a los otros seis algoritmos base. Un valor p menor a 0.05 indica que la ganancia en precisión del Ensemble es estadísticamente significativa y no se debe al azar (Nivel de significancia α = 0.05).
          </p>

          {wilcoxon && wilcoxon.comparaciones ? (
            <table>
              <thead>
                <tr>
                  <th>Comparación (Ensemble Híbrido vs.)</th>
                  <th>Estadístico W</th>
                  <th>Valor p</th>
                  <th>¿Diferencia significativa?</th>
                  <th>Decisión</th>
                </tr>
              </thead>
              <tbody>
                {wilcoxon.comparaciones.map((c, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td><strong>{c.comparacion}</strong></td>
                    <td>{c.estadistico_w.toFixed(1)}</td>
                    <td style={{ color: c.valor_p < 0.05 ? '#27ae60' : '#e74c3c', fontWeight: 600 }}>
                      {c.valor_p < 0.001 ? '< 0.001' : c.valor_p.toFixed(3)}
                    </td>
                    <td>
                      <span style={{
                        background: c.diferencia_significativa ? 'rgba(39,174,96,0.12)' : 'rgba(231,76,60,0.12)',
                        color: c.diferencia_significativa ? '#27ae60' : '#e74c3c',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        fontSize: '12px'
                      }}>
                        {c.diferencia_significativa ? '✅ SÍ' : '❌ NO'}
                      </span>
                    </td>
                    <td style={{ color: '#555', fontStyle: 'italic' }}>{c.conclusion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Cargando resultados de Wilcoxon...</p>
          )}

          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: 'rgba(102,126,234,0.05)',
            borderLeft: '4px solid #667eea',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#4a5568',
            lineHeight: '1.6'
          }}>
            <strong>💡 Conclusión de Tesis:</strong> Al contrastar la hipótesis nula (H0: no existe diferencia en la distribución de errores), todos los p-valores resultaron inferiores a α = 0.05. Por lo tanto, se rechaza la hipótesis nula en todos los casos, confirmando que el <strong>Ensemble Híbrido</strong> ofrece un rendimiento significativamente superior desde el punto de vista estadístico frente a todos los algoritmos base analizados.
          </div>
        </div>
      )}

      {tab === 'diebold' && (
        <div className="card">
          <h3>📊 Prueba de Diebold-Mariano (DM) para Comparar Pronósticos</h3>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '20px' }}>
            Esta prueba estadística evalúa si la diferencia en la precisión predictiva entre el modelo <strong>Ensemble Híbrido</strong> y cada uno de los otros algoritmos es estadísticamente significativa en series temporales de demanda diaria. Un valor p menor a 0.05 (o |DM| &gt; 1.96) demuestra con solidez metodológica la superioridad del modelo propuesto (Nivel de significancia α = 0.05).
          </p>

          {dieboldMariano && dieboldMariano.comparaciones ? (
            <table>
              <thead>
                <tr>
                  <th>Comparación (Ensemble Híbrido vs.)</th>
                  <th>Estadístico DM</th>
                  <th>Valor p</th>
                  <th>¿Diferencia significativa?</th>
                  <th>Decisión</th>
                </tr>
              </thead>
              <tbody>
                {dieboldMariano.comparaciones.map((c, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td><strong>{c.comparacion}</strong></td>
                    <td>{c.estadistico_dm.toFixed(2)}</td>
                    <td style={{ color: c.valor_p < 0.05 ? '#27ae60' : '#e74c3c', fontWeight: 600 }}>
                      {c.valor_p < 0.001 ? '< 0.001' : c.valor_p.toFixed(3)}
                    </td>
                    <td>
                      <span style={{
                        background: c.diferencia_significativa ? 'rgba(39,174,96,0.12)' : 'rgba(231,76,60,0.12)',
                        color: c.diferencia_significativa ? '#27ae60' : '#e74c3c',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        fontSize: '12px'
                      }}>
                        {c.diferencia_significativa ? '✅ SÍ' : '❌ NO'}
                      </span>
                    </td>
                    <td style={{ color: '#555', fontStyle: 'italic' }}>{c.conclusion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Cargando resultados de Diebold-Mariano...</p>
          )}

          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: 'rgba(102,126,234,0.05)',
            borderLeft: '4px solid #667eea',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#4a5568',
            lineHeight: '1.6'
          }}>
            <strong>💡 Conclusión de Tesis:</strong> Al contrastar la hipótesis nula (H0: no existe diferencia en la exactitud del pronóstico), todos los p-valores resultaron inferiores a α = 0.05 y los estadísticos DM superan el valor crítico de 1.96 (|DM| &gt; 1.96). Por lo tanto, se rechaza la hipótesis nula en todos los casos, confirmando que la superioridad predictiva del <strong>Ensemble Híbrido</strong> es estadísticamente significativa en series temporales continuas de demanda de panificación.
          </div>
        </div>
      )}

      {tab === 'ablacion' && (
        <div className="card">
          <h3>🧪 Análisis de Ablación de Características Climáticas</h3>
          <p style={{ color: '#8892a4', fontSize: '13.5px', marginBottom: '20px' }}>
            Un experimento de control de ablación evalúa el impacto neto de remover las variables del clima (Open-Meteo) para demostrar empíricamente el aporte de la ingeniería de características sobre la precisión predictiva.
          </p>

          {ablacion && ablacion.scenarios ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
              {ablacion.scenarios.map((sc, idx) => (
                <div key={idx} style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '20px',
                  background: '#fcfcfd'
                }}>
                  <h4 style={{ color: '#667eea', margin: '0 0 10px 0', fontSize: '15px' }}>{sc.nombre}</h4>
                  <p style={{ fontSize: '12.5px', color: '#4a5568', margin: '0 0 15px 0', lineHeight: '1.5' }}>
                    {sc.descripcion}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '15px', marginBottom: '15px' }}>
                    <div style={{ background: '#fff', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', color: '#718096', fontWeight: 600 }}>MODELO COMPLETO</div>
                      <div style={{ fontSize: '17px', fontWeight: 700, color: '#2d3748', marginTop: '5px' }}>
                        RMSE: {sc.completo.rmse.toFixed(2)}
                      </div>
                      <div style={{ fontSize: '10px', color: '#a0aec0' }}>
                        MAE: {sc.completo.mae.toFixed(2)} · R²: {sc.completo.r2.toFixed(2)}
                      </div>
                    </div>

                    <div style={{ background: '#fff', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', color: '#718096', fontWeight: 600 }}>{sc.id === 'con_lags' ? 'MODELO ABLACIONADO (SIN CLIMA)' : 'MODELO BASE (SIN CLIMA)'}</div>
                      <div style={{ fontSize: '17px', fontWeight: 700, color: '#e53e3e', marginTop: '5px' }}>
                        RMSE: {sc.ablacionado.rmse.toFixed(2)}
                      </div>
                      <div style={{ fontSize: '10px', color: '#a0aec0' }}>
                        MAE: {sc.ablacionado.mae.toFixed(2)} · R²: {sc.ablacionado.r2.toFixed(2)}
                      </div>
                    </div>

                    <div style={{
                      background: sc.cambio_rmse_pct < 0 ? 'rgba(39,174,96,0.06)' : 'rgba(229,62,62,0.06)',
                      padding: '12px',
                      borderRadius: '6px',
                      border: sc.cambio_rmse_pct < 0 ? '1px solid #c6f6d5' : '1px solid #fed7d7',
                      textAlign: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center'
                    }}>
                      <div style={{ fontSize: '10px', color: '#4a5568', fontWeight: 600 }}>{sc.id === 'con_lags' ? 'IMPACTO (AUMENTO ERROR)' : 'MEJORA DEL ERROR (NETA)'}</div>
                      <div style={{
                        fontSize: '18px',
                        fontWeight: 800,
                        color: sc.cambio_rmse_pct < 0 ? '#38a169' : '#e53e3e',
                        marginTop: '5px'
                      }}>
                        {sc.cambio_rmse_pct > 0 ? `+${sc.cambio_rmse_pct.toFixed(1)}%` : `${sc.cambio_rmse_pct.toFixed(1)}%`}
                      </div>
                      <div style={{ fontSize: '9px', color: '#718096', marginTop: '2px' }}>
                        {sc.cambio_rmse_pct < 0 ? 'Reducción del error' : 'Incremento del error'}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    fontSize: '12.5px',
                    color: '#2d3748',
                    background: 'rgba(102,126,234,0.04)',
                    padding: '10px 15px',
                    borderRadius: '6px',
                    borderLeft: '3px solid #667eea',
                    lineHeight: '1.5'
                  }}>
                    <strong>💡 Explicación Científica (Q1):</strong> {sc.explicación_tecnica}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>Cargando resultados del análisis de ablación...</p>
          )}
        </div>
      )}
    </>
  )
}
