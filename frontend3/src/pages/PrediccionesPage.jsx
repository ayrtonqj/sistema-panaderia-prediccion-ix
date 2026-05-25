import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'
import { openPrintWindow, tableHeaderHtml } from '../utils/pdf'
import { formatDateShort } from '../utils/formatters'

export default function PrediccionesPage() {
  const [predicciones, setPredicciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [predResult, setPredResult] = useState('')
  const [climaResult, setClimaResult] = useState('')
  const [comparacion, setComparacion] = useState(null)
  const [comparando, setComparando] = useState(false)
  const [modelosInfo, setModelosInfo] = useState(null)
  const [mejoresModelos, setMejoresModelos] = useState(null)

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/predicciones/'),
      api.get('/productos/'),
      api.get('/ml/metricas'),
      api.get('/ml/mejores-modelos'),
    ]).then(([preds, prods, metricasResp, mejoresResp]) => {
      const predList = Array.isArray(preds) ? preds : []
      const prodList = Array.isArray(prods) ? prods : []
      const prodDict = {}
      prodList.forEach(p => { prodDict[p.id] = p.nombre })

      setPredicciones(predList.map(p => ({ ...p, producto_nombre: prodDict[p.producto_id] || p.producto_id })))

      const metricas = metricasResp?.modelos || []
      setModelosInfo(metricas)

      const mejores = mejoresResp?.mejores_modelos || {}
      setMejoresModelos(mejores)
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const generarPredicciones = async () => {
    setPredResult('⏳ Generando predicciones...')
    try {
      const data = await api.post('/predicciones/generar?n_dias=7')
      setPredResult(`✅ ${data.mensaje || data.total_predicciones + ' predicciones generadas'}`)
      setTimeout(() => { setPredResult(''); fetchData() }, 2000)
    } catch {
      setPredResult('⚠️ Error al generar predicciones')
    }
  }

  const sincronizarClima = async () => {
    setClimaResult('⏳ Sincronizando clima...')
    try {
      const data = await api.post('/clima/sincronizar?dias=7')
      setClimaResult(`✅ Clima sincronizado: ${data.registros_insertados || 0} nuevos, ${data.registros_actualizados || 0} actualizados`)
      setTimeout(() => setClimaResult(''), 3000)
    } catch {
      setClimaResult('⚠️ Error al sincronizar clima')
    }
  }

  const ejecutarComparacion = async () => {
    setComparando(true)
    setComparacion(null)
    try {
      const data = await api.post('/ml/comparar')
      setComparacion(data)
    } catch {
      setComparacion({ error: 'Error al ejecutar comparación' })
    } finally {
      setComparando(false)
    }
  }

  const generarPDF = () => {
    const tbody = predicciones.map(p => `
      <tr>
        <td>${p.producto_nombre}</td>
        <td>${formatDateShort(p.fecha_proyectada)}</td>
        <td>${parseFloat(p.demanda_estimada || 0).toFixed(1)}</td>
        <td>${p.algoritmo_utilizado || '—'}</td>
        <td>${p.confianza_prediccion ? `${parseFloat(p.confianza_prediccion).toFixed(1)}%` : '—'}</td>
      </tr>
    `).join('')
    openPrintWindow('Predicciones de Demanda - Panadería Victoria',
      tableHeaderHtml('Predicciones de Demanda') +
      '<table><thead><tr><th>Producto</th><th>Fecha</th><th>Demanda</th><th>Algoritmo</th><th>Confianza</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema Predictivo Multimodelo - Panadería Victoria</div>'
    )
  }

  const getR2Color = (r2) => {
    if (r2 == null) return '#8892a4'
    if (r2 > 0.6) return '#27ae60'
    if (r2 > 0.4) return '#f39c12'
    return '#e74c3c'
  }

  const getR2Label = (r2) => {
    if (r2 == null) return '—'
    return `${(r2 * 100).toFixed(1)}%`
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>🔮 Predicciones de Demanda</h1>
          <p style={{ color: '#8892a4' }}>7 modelos de Machine Learning en comparación</p>
        </div>
        <button className="btn btn-danger" onClick={generarPDF}>📄 Descargar PDF</button>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>🎯 7 Modelos Predictivos</h3>
          <p style={{ color: '#8892a4', marginBottom: '8px', fontSize: '13px' }}>
            Random Forest · Linear Regression · Gradient Boosting · SARIMA · Prophet · MLP Neural Network · Ensemble
          </p>
          <ul style={{ fontSize: '13px', color: '#a0a8b8', marginBottom: '15px', paddingLeft: '20px' }}>
            <li>Entrena 7 algoritmos por producto</li>
            <li>Elige automáticamente el mejor (menor RMSE)</li>
            <li>Usa el mejor modelo al generar predicciones</li>
          </ul>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button className="btn" onClick={ejecutarComparacion} disabled={comparando}>
              {comparando ? '⏳ Comparando...' : '🔄 Comparar 7 Modelos'}
            </button>
            <button className="btn" onClick={generarPredicciones}>📊 Generar Predicciones (7 días)</button>
            <button className="btn" onClick={sincronizarClima}>🌤️ Sincronizar Clima</button>
          </div>
          {predResult && <p style={{ marginTop: '10px', color: predResult.includes('✅') ? '#27ae60' : '#e74c3c' }}>{predResult}</p>}
          {climaResult && <p style={{ marginTop: '10px', color: climaResult.includes('✅') ? '#27ae60' : '#e74c3c' }}>{climaResult}</p>}
        </div>

        {mejoresModelos && Object.keys(mejoresModelos).length > 0 && (
          <div className="card">
            <h3>🏆 Mejores Modelos por Producto</h3>
            <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '13px' }}>
              <table style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Producto</th>
                    <th style={{ textAlign: 'left' }}>Algoritmo</th>
                    <th style={{ textAlign: 'right' }}>R²</th>
                  </tr>
                </thead>
                <tbody>
                  {(modelosInfo || []).filter(m => m.modelo_disponible).map(m => (
                    <tr key={m.producto_id}>
                      <td>{m.producto_nombre}</td>
                      <td>
                        <span style={{
                          background: 'rgba(102,126,234,0.1)', color: '#667eea',
                          padding: '2px 8px', borderRadius: '4px', fontSize: '12px',
                        }}>
                          {m.mejor_algoritmo || '?'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', color: getR2Color(m.r2), fontWeight: 600 }}>
                        {getR2Label(m.r2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {comparacion && !comparacion.error && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3>📊 Resultados de Comparación</h3>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '15px' }}>
            {comparacion.total_productos} productos evaluados · {comparacion.modelos_evaluados} modelos por producto
            · {comparacion.productos_con_modelo} productos con modelo asignado
          </p>

          {comparacion.resumen_algoritmos && (
            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', marginBottom: '20px' }}>
              {Object.entries(comparacion.resumen_algoritmos).map(([algo, count]) => {
                const colors = {
                  'Random Forest': '#667eea',
                  'Linear Regression': '#f39c12',
                  'Gradient Boosting': '#e74c3c',
                  'SARIMA': '#27ae60',
                  'Prophet': '#9b59b6',
                  'MLP Neural Network': '#1abc9c',
                  'Ensemble (RF+GB+LR)': '#e67e22',
                }
                return (
                  <div key={algo} style={{
                    background: 'var(--bg-app)', padding: '10px 16px', borderRadius: '10px',
                    border: `1px solid ${colors[algo] || '#667eea'}33`,
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: colors[algo] || '#667eea' }}>{count}</div>
                    <div style={{ fontSize: '12px', color: '#8892a4' }}>{algo}</div>
                  </div>
                )
              })}
            </div>
          )}

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Registros</th>
                  <th>🏆 Mejor Modelo</th>
                  <th>RMSE</th>
                  <th>R²</th>
                  <th>RF</th>
                  <th>GB</th>
                  <th>PRO</th>
                  <th>SAR</th>
                  <th>LR</th>
                  <th>MLP</th>
                  <th>ENS</th>
                </tr>
              </thead>
              <tbody>
                {(comparacion.detalle_por_producto || []).map(prod => {
                  const res = prod.resultados || []
                  const getRMSE = (algo) => {
                    const r = res.find(x => x.algoritmo === algo)
                    return r && r.rmse != null ? r.rmse.toFixed(1) : '—'
                  }
                  return (
                    <tr key={prod.producto_id}>
                      <td>{prod.producto_nombre}</td>
                      <td>{prod.n_registros || 0}</td>
                      <td>
                        <span style={{
                          background: 'rgba(102,126,234,0.1)', color: '#667eea',
                          padding: '2px 8px', borderRadius: '4px', fontSize: '12px',
                        }}>
                          {prod.mejor_modelo || '—'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{prod.mejor_rmse != null ? prod.mejor_rmse.toFixed(1) : '—'}</td>
                      <td style={{ color: getR2Color(prod.r2), fontWeight: 600 }}>
                        {getR2Label(prod.r2)}
                      </td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('Random Forest')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('Gradient Boosting')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('Prophet')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('SARIMA')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('Linear Regression')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('MLP Neural Network')}</td>
                      <td style={{ fontSize: '12px' }}>{getRMSE('Ensemble (RF+GB+LR)')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <p style={{ color: '#8892a4', fontSize: '11px', marginTop: '10px' }}>
            Valores = RMSE (menor es mejor) · RF=Random Forest · GB=Gradient Boosting · PRO=Prophet · SAR=SARIMA · LR=Linear Regression · MLP=MLP Neural Network · ENS=Ensemble
          </p>
        </div>
      )}

      <div className="card" style={{ marginTop: '20px' }}>
        <h3>Predicciones Actuales</h3>
        {loading ? <p>Cargando...</p> : (
          <Pagination
            data={predicciones}
            pageSize={20}
            columns={['Producto', 'Fecha', 'Demanda', 'Algoritmo', 'Confianza']}
            renderRow={(p) => (
              <tr key={p.id}>
                <td>{p.producto_nombre}</td>
                <td>{formatDateShort(p.fecha_proyectada)}</td>
                <td>{parseFloat(p.demanda_estimada || 0).toFixed(1)}</td>
                <td>
                  <span style={{
                    background: 'rgba(102,126,234,0.08)', color: '#667eea',
                    padding: '2px 8px', borderRadius: '4px', fontSize: '12px',
                  }}>
                    {p.algoritmo_utilizado || 'Random Forest'}
                  </span>
                </td>
                <td style={{ color: getR2Color(p.confianza_prediccion), fontWeight: 600 }}>
                  {getR2Label(p.confianza_prediccion)}
                </td>
              </tr>
            )}
          />
        )}
      </div>
    </>
  )
}
