import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'
import { openPrintWindow, tableHeaderHtml, descargarExcel, enviarPorCorreo } from '../utils/pdf'
import { formatDateShort } from '../utils/formatters'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function translateAlgo(name) {
  const map = {
    'Random Forest': 'Random Forest',
    'Linear Regression': 'Regresión Lineal',
    'Gradient Boosting': 'Gradient Boosting',
    'ARIMA': 'ARIMA',
    'Prophet': 'Prophet',
    'MLP Neural Network': 'Red Neuronal (MLP)',
    'Ensemble (RF+GB+LR)': 'Ensemble Híbrido'
  }
  return map[name] || name
}

const ALGO_COLORS = {
  'Random Forest': '#667eea',
  'Regresión Lineal': '#f39c12',
  'Gradient Boosting': '#e74c3c',
  'ARIMA': '#27ae60',
  'Prophet': '#9b59b6',
  'Red Neuronal (MLP)': '#1abc9c',
  'Ensemble Híbrido': '#e67e22',
}

const ALGO_BG = {
  'Random Forest': 'rgba(102,126,234,0.12)',
  'Regresión Lineal': 'rgba(243,156,18,0.12)',
  'Gradient Boosting': 'rgba(231,76,60,0.12)',
  'ARIMA': 'rgba(39,174,96,0.12)',
  'Prophet': 'rgba(155,89,182,0.12)',
  'Red Neuronal (MLP)': 'rgba(26,188,156,0.12)',
  'Ensemble Híbrido': 'rgba(230,126,34,0.12)',
}

function formatSecs(s) {
  if (s < 60) return `${Math.round(s)}s`
  const m = Math.floor(s / 60)
  const sec = Math.round(s % 60)
  return `${m}m ${sec}s`
}

export default function PrediccionesPage() {
  const [predicciones, setPredicciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [predResult, setPredResult] = useState('')
  const [climaResult, setClimaResult] = useState('')
  const [optimResult, setOptimResult] = useState('')
  const [optimizando, setOptimizando] = useState(false)
  const [comparacion, setComparacion] = useState(null)
  const [comparando, setComparando] = useState(false)
  const [modelosInfo, setModelosInfo] = useState(null)
  const [mejoresModelos, setMejoresModelos] = useState(null)

  // Streaming state
  const [streaming, setStreaming] = useState(false)
  const [faseActual, setFaseActual] = useState(null)
  const [productoActual, setProductoActual] = useState(null)
  const [algoritmosProgreso, setAlgoritmosProgreso] = useState({})
  const [matrizGlobal, setMatrizGlobal] = useState({})
  const [mejorPorProducto, setMejorPorProducto] = useState({})
  const [rankingGlobal, setRankingGlobal] = useState({})
  const [progresoGlobal, setProgresoGlobal] = useState({ n: 0, total: 0 })
  const [algoritmosGlobalProgreso, setAlgoritmosGlobalProgreso] = useState({})
  const [timerInfo, setTimerInfo] = useState({ transcurrido: 0, restante: null, inicio: null })
  const [resumenFinal, setResumenFinal] = useState(null)
  const [streamError, setStreamError] = useState(null)
  const [productosProcesados, setProductosProcesados] = useState([])
  const [datosProducto, setDatosProducto] = useState(null)
  const [detallesAlgoritmo, setDetallesAlgoritmo] = useState({})
  const [recomendaciones, setRecomendaciones] = useState([])
  const [formulaExpandida, setFormulaExpandida] = useState(null)
  const [detallesGlobales, setDetallesGlobales] = useState({})
  const abortRef = useRef(null)

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
      setPredicciones(predList.map(p => ({
        ...p,
        producto_nombre: prodDict[p.producto_id] || p.producto_id,
        algoritmo_utilizado: translateAlgo(p.algoritmo_utilizado)
      })))

      const translatedModelos = (metricasResp?.modelos || []).map(m => ({
        ...m,
        mejor_algoritmo: translateAlgo(m.mejor_algoritmo),
        todos_resultados: (m.todos_resultados || []).map(r => ({
          ...r,
          algoritmo: translateAlgo(r.algoritmo)
        }))
      }))
      setModelosInfo(translatedModelos)

      const translatedMejores = {}
      Object.entries(mejoresResp?.mejores_modelos || {}).forEach(([k, v]) => {
        translatedMejores[k] = translateAlgo(v)
      })
      setMejoresModelos(translatedMejores)
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  useEffect(() => {
    if (!streaming || !timerInfo.inicio) return
    const id = setInterval(() => {
      setTimerInfo(prev => ({ ...prev, transcurrido: (Date.now() - prev.inicio) / 1000 }))
    }, 100)
    return () => clearInterval(id)
  }, [streaming, timerInfo.inicio])

  const detenerStream = () => {
    if (abortRef.current) abortRef.current()
    setStreaming(false)
  }

  const iniciarComparacionStream = async () => {
    setStreaming(true)
    setStreamError(null)
    setFaseActual(null)
    setProductoActual(null)
    setAlgoritmosProgreso({})
    setMatrizGlobal({})
    setMejorPorProducto({})
    setRankingGlobal({})
    setProgresoGlobal({ n: 0, total: 0 })
    setAlgoritmosGlobalProgreso({})
    setTimerInfo({ transcurrido: 0, restante: null, inicio: Date.now() })
    setResumenFinal(null)
    setProductosProcesados([])
    setDetallesAlgoritmo({})
    setRecomendaciones([])
    setDetallesGlobales({})

    const controller = new AbortController()
    abortRef.current = () => controller.abort()

    try {
      const response = await fetch(`${API_BASE}/ml/comparar/stream`, { signal: controller.signal })
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop()
        for (const part of parts) {
          const lines = part.split('\n')
          let eventType = ''
          let dataStr = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7)
            if (line.startsWith('data: ')) dataStr = line.slice(6)
          }
          if (!dataStr) continue
          let parsed
          try { parsed = JSON.parse(dataStr) } catch { continue }
          procesarEvento(eventType, parsed)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setStreamError(err.message || 'Error de conexion')
      }
    } finally {
      setStreaming(false)
      abortRef.current = null
      fetchData()
    }
  }

  const procesarEvento = useCallback((type, data) => {
    if (data) {
      if (data.algoritmo) data.algoritmo = translateAlgo(data.algoritmo)
      if (data.mejor_algoritmo) data.mejor_algoritmo = translateAlgo(data.mejor_algoritmo)
      if (data.segundo_mejor) data.segundo_mejor = translateAlgo(data.segundo_mejor)
      if (data.resultados) {
        data.resultados = data.resultados.map(r => ({
          ...r,
          algoritmo: translateAlgo(r.algoritmo)
        }))
      }
    }
    switch (type) {
      case 'fase':
        setFaseActual(data)
        break

      case 'producto_inicio':
        setProductoActual(data)
        setAlgoritmosProgreso({})
        setProgresoGlobal(prev => ({
          n: data.n_producto,
          total: data.total_productos,
        }))
        break

      case 'producto_saltado':
        setProgresoGlobal(prev => ({
          n: data.n_producto,
          total: data.total_productos,
        }))
        break

      case 'algoritmo_inicio':
        setAlgoritmosProgreso(prev => ({
          ...prev,
          [data.algoritmo]: { paso: 'iniciando', color: ALGO_COLORS[data.algoritmo] || '#667eea' },
        }))
        break

      case 'algoritmo_progreso':
        setAlgoritmosProgreso(prev => ({
          ...prev,
          [data.algoritmo]: { paso: data.paso, color: ALGO_COLORS[data.algoritmo] || '#667eea' },
        }))
        break

      case 'algoritmo_resultado':
        setAlgoritmosProgreso(prev => ({
          ...prev,
          [data.algoritmo]: { paso: 'completado', ...data, color: ALGO_COLORS[data.algoritmo] || '#667eea' },
        }))
        if (data.es_mejor && productoActual) {
          setMejorPorProducto(prev => ({
            ...prev,
            [productoActual.producto_id]: { algoritmo: data.algoritmo, rmse: data.rmse, r2: data.r2 },
          }))
        }
        setMatrizGlobal(prev => {
          const pid = productoActual?.producto_id
          if (!pid) return prev
          return {
            ...prev,
            [pid]: { ...(prev[pid] || {}), [data.algoritmo]: data.rmse },
          }
        })
        setAlgoritmosGlobalProgreso(prev => {
          const current = prev[data.algoritmo] || 0
          return { ...prev, [data.algoritmo]: current + 1 }
        })
        break

      case 'algoritmo_error':
        setAlgoritmosProgreso(prev => ({
          ...prev,
          [data.algoritmo]: { paso: 'error', error: data.error, color: ALGO_COLORS[data.algoritmo] || '#667eea' },
        }))
        setAlgoritmosGlobalProgreso(prev => {
          const current = prev[data.algoritmo] || 0
          return { ...prev, [data.algoritmo]: current + 1 }
        })
        break

      case 'producto_resumen':
        setProductosProcesados(prev => {
          const exists = prev.find(p => p.producto_id === data.producto_id)
          if (exists) return prev.map(p => p.producto_id === data.producto_id ? data : p)
          return [...prev, data]
        })
        break

      case 'ranking_global':
        setRankingGlobal(data)
        break

      case 'completo':
        setResumenFinal(data)
        setFaseActual({ fase: 'completado', mensaje: 'Comparacion completada' })
        break

      case 'error':
        setStreamError(data.error || 'Error desconocido')
        break

      case 'datos_producto':
        setDatosProducto(data)
        break

      case 'algoritmo_detalle':
        setDetallesAlgoritmo(prev => ({
          ...prev,
          [data.algoritmo]: data,
        }))
        setDetallesGlobales(prev => {
          if (prev[data.algoritmo]) return prev
          return { ...prev, [data.algoritmo]: data }
        })
        break

      case 'recomendacion_producto':
        setRecomendaciones(prev => {
          const exists = prev.find(r => r.producto_id === data.producto_id)
          if (exists) return prev.map(r => r.producto_id === data.producto_id ? data : r)
          return [...prev, data]
        })
        break
    }
  }, [productoActual])

  const generarPredicciones = async () => {
    setPredResult('Generando predicciones...')
    try {
      const data = await api.post('/predicciones/generar?n_dias=7')
      setPredResult(`✅ ${data.mensaje || data.total_predicciones + ' predicciones generadas'}`)
      setTimeout(() => { setPredResult(''); fetchData() }, 2000)
    } catch (e) {
      setPredResult(`⚠️ ${e.response?.data?.detail || e.message || 'Error al generar predicciones'}`)
    }
  }

  const sincronizarClima = async () => {
    setClimaResult('Sincronizando clima...')
    try {
      const data = await api.post('/clima/sincronizar?dias=7')
      setClimaResult(`✅ Clima sincronizado: ${data.registros_insertados || 0} nuevos`)
      setTimeout(() => setClimaResult(''), 3000)
    } catch (e) {
      setClimaResult(`⚠️ ${e.response?.data?.detail || e.message || 'Error al sincronizar clima'}`)
    }
  }

  const optimizarHiperparametros = async () => {
    setOptimResult('Optimizando hiperparámetros...')
    setOptimizando(true)
    try {
      const data = await api.post('/ml/optimizar')
      setOptimResult(`✅ ${data.total_productos_optimizados || 0} productos optimizados`)
      setTimeout(() => setOptimResult(''), 4000)
    } catch (e) {
      setOptimResult(`⚠️ ${e.response?.data?.detail || e.message || 'Error al optimizar'}`)
    } finally {
      setOptimizando(false)
    }
  }

  const generarPDF = () => {
    const tbody = predicciones.map(p => `
      <tr><td>${p.producto_nombre}</td><td>${formatDateShort(p.fecha_proyectada)}</td><td>${parseFloat(p.demanda_estimada || 0).toFixed(1)}</td><td>${p.algoritmo_utilizado || '—'}</td><td>${p.confianza_prediccion ? (p.confianza_prediccion * 100).toFixed(1) + '%' : '—'}</td></tr>
    `).join('')
    openPrintWindow('Predicciones - Panaderia Victoria',
      tableHeaderHtml('Predicciones de Demanda') +
      '<table><thead><tr><th>Producto</th><th>Fecha</th><th>Demanda</th><th>Algoritmo</th><th>Confianza</th></tr></thead><tbody>' +
      tbody + '</tbody></table>'
    )
  }

  const pct = progresoGlobal.total > 0 ? Math.round((progresoGlobal.n / progresoGlobal.total) * 100) : 0

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '15px' }}>
        <div>
          <h1>🔮 Predicciones de Demanda</h1>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
            {Object.entries(ALGO_COLORS).map(([algo, color]) => (
              <span key={algo} style={{ background: color + '20', color, padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 500 }}>{algo}</span>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
        <button className="btn btn-danger" onClick={generarPDF} style={{ fontSize: '11px', padding: '3px 8px', flexShrink: 0 }}>📄 PDF</button>
        <button className="btn" onClick={() => enviarPorCorreo('Predicciones de Demanda', ['Producto', 'Fecha', 'Demanda', 'Algoritmo', 'Confianza'], (predicciones || []).map(p => [p.producto_nombre, p.fecha_proyectada, parseFloat(p.demanda_estimada || 0).toFixed(1), p.algoritmo_utilizado || '-', p.confianza_prediccion ? (p.confianza_prediccion * 100).toFixed(1) + '%' : '-']))} style={{ fontSize: '11px', padding: '3px 8px', background: '#e74c3c', color: '#fff', flexShrink: 0 }}>📧 Enviar</button>
        <button className="btn" onClick={() => descargarExcel('Predicciones', [{ key: "producto_nombre", label: "Producto" }, { key: "fecha_proyectada", label: "Fecha" }, { key: "demanda_estimada", label: "Demanda" }, { key: "algoritmo_utilizado", label: "Algoritmo" }, { key: "confianza_prediccion", label: "Confianza", render: (i) => i.confianza_prediccion ? (i.confianza_prediccion * 100).toFixed(1) + "%" : "-" }], predicciones)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', flexShrink: 0 }}>📊 Excel</button>
        </div>
      </div>

      <div className="card">
        <div style={{ marginBottom: '10px', fontSize: '12px', color: '#64748b', fontWeight: 600 }}>
          📌 Flujo recomendado para actualizar predicciones: Paso 1 ➔ Paso 2 ➔ Paso 3 ➔ Paso 4
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn" onClick={sincronizarClima} style={{ background: '#3b82f6', color: '#fff', fontWeight: 600, border: 'none' }}>
            1. 🌤️ Sincronizar Clima
          </button>
          <button className="btn" onClick={iniciarComparacionStream} disabled={streaming}
            style={{ background: streaming ? '#718096' : 'linear-gradient(135deg,#667eea,#764ba2)', color: '#fff', fontWeight: 600, border: 'none' }}>
            {streaming ? '⏳ Comparando...' : '2. ⚡ Comparar 7 Modelos'}
          </button>
          <button className="btn" onClick={optimizarHiperparametros} disabled={optimizando} style={{ border: '1px solid #cbd5e1' }}>
            {optimizando ? '⏳ Optimizando...' : '3. 🎯 Optimizar Hiperparámetros'}
          </button>
          <button className="btn" onClick={generarPredicciones} style={{ background: '#10b981', color: '#fff', fontWeight: 600, border: 'none' }}>
            4. 📊 Generar Predicciones (7 días)
          </button>
          {streaming && <button className="btn" onClick={detenerStream} style={{ background: '#e74c3c', color: '#fff', border: 'none' }}>⏹ Detener</button>}
        </div>
        {predResult && <p style={{ marginTop: '10px', color: predResult.includes('✅') ? '#27ae60' : '#e74c3c', fontWeight: 600 }}>{predResult}</p>}
        {climaResult && <p style={{ marginTop: '8px', color: climaResult.includes('✅') ? '#27ae60' : '#8892a4' }}>{climaResult}</p>}
        {optimResult && <p style={{ marginTop: '10px', color: optimResult.includes('✅') ? '#27ae60' : '#e74c3c', fontWeight: 600 }}>{optimResult}</p>}
        {streamError && <p style={{ marginTop: '8px', color: '#e74c3c' }}>⚠️ {streamError}</p>}
      </div>

      {streaming && (
        <div className="stream-panel" style={{ marginTop: '20px' }}>
          <div className="card" style={{ borderLeft: '4px solid #667eea' }}>
            <h3 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>⏳ Comparacion en Tiempo Real</span>
              <span style={{ fontSize: '14px', color: '#8892a4', fontWeight: 400 }}>
                ⏱ {formatSecs(timerInfo.transcurrido)}
                {pct > 0 && pct < 100 && ` · ~${formatSecs(timerInfo.transcurrido / pct * (100 - pct) / 100)} restante`}
              </span>
            </h3>

            <div className="progress-bar-track" style={{ marginBottom: '8px' }}>
              <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '20px' }}>
              {pct}% · {progresoGlobal.n}/{progresoGlobal.total} productos
              {faseActual && ` · ${faseActual.mensaje || faseActual.fase}`}
            </p>

            {productoActual && (
              <div style={{
                background: 'var(--bg-app)', borderRadius: '12px', padding: '20px',
                border: '1px solid var(--border-color)', marginBottom: '20px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0 }}>🥐 {productoActual.producto}</h4>
                  <span style={{ color: '#8892a4', fontSize: '13px' }}>
                    {productoActual.registros} registros · Train: {productoActual.train} · Test: {productoActual.test} · {productoActual.features} features
                  </span>
                </div>

                {datosProducto && datosProducto.producto_id === productoActual.producto_id && (
                  <div className="formula-card" style={{
                    background: 'rgba(102,126,234,0.06)', borderRadius: '8px', padding: '12px',
                    marginBottom: '14px', fontSize: '12px', color: '#555',
                    borderLeft: '3px solid #667eea',
                  }}>
                    <strong style={{ color: '#667eea', display: 'block', marginBottom: '6px' }}>📊 Estadisticas de Demanda</strong>
                    <div className="stats-2x2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '6px', marginBottom: '8px' }}>
                      <div><span style={{ color: '#8892a4' }}>Media</span><br/><strong>{datosProducto.demanda_media}</strong></div>
                      <div><span style={{ color: '#8892a4' }}>Desv. Std</span><br/><strong>{datosProducto.demanda_std}</strong></div>
                      <div><span style={{ color: '#8892a4' }}>Min</span><br/><strong>{datosProducto.demanda_min}</strong></div>
                      <div><span style={{ color: '#8892a4' }}>Max</span><br/><strong>{datosProducto.demanda_max}</strong></div>
                    </div>
                    <div style={{ color: '#8892a4' }}>
                      <strong>Features ({datosProducto.features.length}):</strong> {datosProducto.features.join(', ')}
                    </div>
                    <div style={{ color: '#8892a4', marginTop: '4px' }}>{datosProducto.descripcion_features}</div>
                    <div style={{ color: '#8892a4', marginTop: '4px' }}>{datosProducto.split}</div>
                  </div>
                )}

                {Object.entries(ALGO_COLORS).map(([algoName, color]) => {
                  const prog = algoritmosProgreso[algoName]
                  const resultado = prog?.paso === 'completado' ? prog : null
                  const error = prog?.paso === 'error'
                  const pendiente = !prog
                  let barWidth = 0
                  if (pendiente) barWidth = 0
                  else if (prog.paso === 'iniciando') barWidth = 20
                  else if (prog.paso === 'entrenando') barWidth = 60
                  else if (prog.paso === 'evaluando') barWidth = 85
                  else if (prog.paso === 'completado') barWidth = 100
                  else if (prog.paso === 'error') barWidth = 100

                  return (
                    <div key={algoName} style={{ marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ width: '160px', fontSize: '13px', fontWeight: 500, color: pendiente ? '#8892a4' : '#333' }}>
                        {algoName}
                      </span>
                      <div className="progress-bar-track" style={{ flex: 1, height: '10px' }}>
                        <div className="progress-bar-fill" style={{
                          width: `${barWidth}%`,
                          background: error ? '#e74c3c' : `linear-gradient(90deg, ${color}, ${color}cc)`,
                        }} />
                      </div>
                      <span style={{ width: '160px', fontSize: '12px', textAlign: 'right' }}>
                        {pendiente && <span style={{ color: '#8892a4' }}>pendiente</span>}
                        {prog?.paso === 'iniciando' && <span style={{ color }}>iniciando...</span>}
                        {prog?.paso === 'entrenando' && <span style={{ color }}>entrenando...</span>}
                        {prog?.paso === 'evaluando' && <span style={{ color }}>evaluando...</span>}
                        {resultado && (
                          <span>
                            <span style={{ color: resultado.es_mejor ? '#27ae60' : '#8892a4', fontWeight: resultado.es_mejor ? 600 : 400 }}>
                              {resultado.es_mejor ? '🏆 ' : ''}RMSE {resultado.rmse}
                            </span>
                            <span style={{ color: '#8892a4', marginLeft: '8px' }}>R² {(resultado.r2 * 100).toFixed(1)}%</span>
                          </span>
                        )}
                        {error && <span style={{ color: '#e74c3c' }}>error</span>}
                      </span>
                    </div>
                  )
                })}

                {productoActual && mejorPorProducto[productoActual.producto_id] && (
                  <div style={{
                    marginTop: '12px', padding: '10px 14px', borderRadius: '8px',
                    background: 'rgba(39,174,96,0.08)', color: '#27ae60',
                    fontSize: '13px', fontWeight: 600,
                  }}>
                    🏆 Mejor hasta ahora: {mejorPorProducto[productoActual.producto_id].algoritmo}
                    · RMSE: {mejorPorProducto[productoActual.producto_id].rmse}
                    · R²: {(mejorPorProducto[productoActual.producto_id].r2 * 100).toFixed(1)}%
                  </div>
                )}
              </div>
            )}

            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ marginBottom: '10px', fontSize: '14px', color: '#8892a4' }}>Progreso por Algoritmo</h4>
              {Object.entries(ALGO_COLORS).map(([algoName, color]) => {
                const count = algoritmosGlobalProgreso[algoName] || 0
                const total = progresoGlobal.total || 1
                const algoPct = Math.round((count / total) * 100)
                return (
                  <div key={algoName} style={{ marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '160px', fontSize: '12px', color: '#666' }}>{algoName}</span>
                    <div className="progress-bar-track" style={{ flex: 1, height: '8px', borderRadius: '4px' }}>
                      <div className="progress-bar-fill" style={{ width: `${algoPct}%`, background: color, borderRadius: '4px' }} />
                    </div>
                    <span style={{ fontSize: '11px', color: '#8892a4', width: '50px', textAlign: 'right' }}>{count}/{total}</span>
                  </div>
                )
              })}
            </div>

            {productoActual && Object.keys(detallesAlgoritmo).length > 0 && (
              <details className="formula-card" style={{ marginTop: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <summary style={{ cursor: 'pointer', padding: '10px 14px', fontWeight: 600, fontSize: '13px', color: '#667eea', background: 'rgba(102,126,234,0.04)' }}>
                  📐 Vista Previa de Detalles ({productoActual.producto}) — {Object.keys(detallesAlgoritmo).length} algoritmo(s) completado(s)
                </summary>
                <div style={{ padding: '12px', maxHeight: '350px', overflowY: 'auto' }}>
                  {Object.entries(detallesAlgoritmo).map(([algo, det]) => {
                    const color = ALGO_COLORS[algo] || '#667eea'
                    const bg = ALGO_BG[algo] || 'rgba(102,126,234,0.04)'
                    return (
                      <div key={algo} style={{ background: bg, borderRadius: '8px', padding: '12px', marginBottom: '10px', borderLeft: `3px solid ${color}` }}>
                        <strong style={{ color, fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                          {algo} · {det.complejidad === 'alta' ? '🔴' : det.complejidad === 'media' ? '🟡' : '🟢'} {det.complejidad} · ⚡ {det.velocidad}
                        </strong>
                        <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#555', lineHeight: 1.5 }}>{det.formula ? det.formula.slice(0, 200) + '...' : ''}</p>
                        {det.fortalezas && det.fortalezas.length > 0 && (
                          <div style={{ marginTop: '6px' }}>
                            {det.fortalezas.slice(0, 2).map((f, i) => (
                              <span key={i} style={{ display: 'inline-block', background: 'rgba(39,174,96,0.08)', color: '#27ae60', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', marginRight: '4px', marginBottom: '4px' }}>✅ {f.slice(0, 60)}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </details>
            )}
          </div>
        </div>
      )}

      {Object.keys(detallesGlobales).length > 0 && !streaming && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3>📐 Catalogo Completo de los 7 Modelos Predictivos</h3>
          <p style={{ color: '#8892a4', fontSize: '12px', marginBottom: '16px' }}>
            Documentacion tecnica de cada algoritmo: formula matematica, proceso de entrenamiento, parametros, fortalezas, debilidades y recomendaciones. Haz clic para expandir.
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <span style={{ fontSize: '11px', color: '#8892a4' }}>Leyenda:</span>
            <span style={{ background: '#27ae6020', color: '#27ae60', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>🟢 Baja complejidad</span>
            <span style={{ background: '#f39c1220', color: '#f39c12', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>🟡 Media</span>
            <span style={{ background: '#e74c3c20', color: '#e74c3c', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>🔴 Alta</span>
            <span style={{ background: '#667eea20', color: '#667eea', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>⚡ Velocidad</span>
            <span style={{ background: '#1abc9c20', color: '#1abc9c', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>🔍 Interpretabilidad</span>
          </div>
          {Object.entries(ALGO_COLORS).map(([algo, color]) => {
            const det = detallesGlobales[algo]
            if (!det) return (
              <div key={algo} style={{
                padding: '12px 16px', marginBottom: '8px', borderRadius: '8px',
                background: 'rgba(102,126,234,0.03)', borderLeft: `4px solid ${color}40`,
                opacity: 0.5, fontSize: '13px', color: '#8892a4',
              }}>
                ⏳ {algo} — No se obtuvieron datos en esta comparacion
              </div>
            )
            const compIcon = det.complejidad === 'baja' ? '🟢' : det.complejidad === 'media' ? '🟡' : '🔴'
            const velIcon = det.velocidad === 'muy rapida' ? '⚡⚡' : det.velocidad === 'rapida' ? '⚡' : det.velocidad === 'media' ? '⏱' : '🐢'
            const interpIcon = det.interpretabilidad === 'muy alta' ? '🔍🔍' : det.interpretabilidad === 'alta' ? '🔍' : det.interpretabilidad === 'media' ? '🔎' : '🔒'
            const compColor = det.complejidad === 'baja' ? '#27ae60' : det.complejidad === 'media' ? '#f39c12' : '#e74c3c'
            const velColor = det.velocidad === 'muy rapida' || det.velocidad === 'rapida' ? '#27ae60' : det.velocidad === 'media' ? '#f39c12' : '#e74c3c'
            const interpColor = det.interpretabilidad === 'muy alta' || det.interpretabilidad === 'alta' ? '#27ae60' : det.interpretabilidad === 'media' ? '#f39c12' : '#e74c3c'
            return (
              <details key={algo} className="formula-card" style={{
                marginBottom: '10px', borderRadius: '10px', overflow: 'hidden',
                border: `1px solid ${color}30`, background: 'var(--bg-card)',
              }}>
                <summary style={{
                  cursor: 'pointer', padding: '14px 18px', fontWeight: 600, fontSize: '14px',
                  background: ALGO_BG[algo] || 'rgba(102,126,234,0.06)',
                  color, display: 'flex', alignItems: 'center', gap: '12px',
                  userSelect: 'none', flexWrap: 'wrap',
                }}>
                  <span style={{ fontSize: '18px' }}>📐</span> {algo}
                  <span style={{ fontSize: '11px', fontWeight: 400, display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ color: compColor }}>{compIcon} {det.complejidad}</span>
                    <span style={{ color: velColor }}>{velIcon} {det.velocidad}</span>
                    <span style={{ color: interpColor }}>{interpIcon} {det.interpretabilidad}</span>
                  </span>
                </summary>
                <div style={{ padding: '20px' }}>
                  <div style={{ marginBottom: '16px', background: 'rgba(102,126,234,0.04)', borderRadius: '8px', padding: '14px' }}>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#667eea' }}>📐 Formula y Descripcion</h4>
                    <p style={{ margin: 0, fontSize: '13px', color: '#444', lineHeight: 1.7 }}>{det.formula}</p>
                  </div>
                  {det.como_funciona && det.como_funciona.length > 0 && (
                    <div style={{ marginBottom: '16px' }}>
                      <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#667eea' }}>⚙️ Proceso de Entrenamiento</h4>
                      <ol style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#555', lineHeight: 1.8 }}>
                        {det.como_funciona.map((paso, i) => <li key={i}>{paso}</li>)}
                      </ol>
                    </div>
                  )}
                  {det.por_que_parametros && (
                    <div style={{ marginBottom: '16px', background: 'rgba(243,156,18,0.05)', borderRadius: '8px', padding: '12px' }}>
                      <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: '#f39c12' }}>💡 ¿Por que estos parametros?</h4>
                      <p style={{ margin: 0, fontSize: '12px', color: '#555', lineHeight: 1.6 }}>{det.por_que_parametros}</p>
                    </div>
                  )}
                  {Object.keys(det.parametros || {}).length > 0 && (
                    <div style={{ marginBottom: '16px' }}>
                      <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#667eea' }}>⚙️ Parametros Configurados</h4>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {Object.entries(det.parametros).map(([k, v]) => (
                          <span key={k} style={{ background: 'rgba(102,126,234,0.06)', color: '#444', padding: '4px 12px', borderRadius: '5px', fontSize: '11px', border: '1px solid rgba(102,126,234,0.15)' }}>
                            <strong style={{ color: '#667eea' }}>{k}:</strong> {typeof v === 'number' ? (Math.abs(v) < 100 ? v.toFixed(4) : v.toFixed(2)) : Array.isArray(v) ? v.join(', ') : String(v)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {(det.feature_importance && det.feature_importance.length > 0) && (
                    <div style={{ marginBottom: '16px' }}>
                      <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#667eea' }}>📊 Importancia de Features</h4>
                      <p style={{ fontSize: '11px', color: '#8892a4', marginBottom: '8px' }}>Variables mas influyentes en la prediccion (mas % = mayor peso en el modelo)</p>
                      {det.feature_importance.map(fi => {
                        const impVal = fi.importance !== undefined ? fi.importance : (fi[1] || 0)
                        const pct = Math.round(impVal * 100)
                        return (
                          <div key={fi.feature || fi[0]} className="feature-bar" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                            <span style={{ width: '140px', fontSize: '12px', color: '#555', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>{fi.feature || fi[0] || '?'}</span>
                            <div className="progress-bar-track" style={{ flex: 1, height: '10px', borderRadius: '5px' }}>
                              <div className="progress-bar-fill" style={{ width: `${Math.min(pct, 100)}%`, background: color, borderRadius: '5px' }} />
                            </div>
                            <span style={{ fontSize: '11px', color: '#8892a4', width: '45px', textAlign: 'right', fontWeight: 600 }}>{pct}%</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                  {(det.coeficientes && det.coeficientes.length > 0) && (
                    <div style={{ marginBottom: '16px' }}>
                      <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#667eea' }}>📈 Coeficientes (β)</h4>
                      <p style={{ fontSize: '11px', color: '#8892a4', marginBottom: '8px' }}>Cambio en la demanda al aumentar 1 unidad de cada feature</p>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '6px' }}>
                        {det.coeficientes.map(c => (
                          <div key={c.feature} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(102,126,234,0.03)', borderRadius: '6px', fontSize: '12px' }}>
                            <span style={{ color: '#555', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.feature}</span>
                            <strong style={{ color: c.coef > 0 ? '#27ae60' : '#e74c3c', marginLeft: '8px' }}>{c.coef > 0 ? '+' : ''}{c.coef.toFixed(4)}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                    {det.fortalezas && det.fortalezas.length > 0 && (
                      <div style={{ background: 'rgba(39,174,96,0.04)', borderRadius: '8px', padding: '14px' }}>
                        <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#27ae60' }}>✅ Fortalezas</h4>
                        <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#555', lineHeight: 1.7 }}>
                          {det.fortalezas.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                      </div>
                    )}
                    {det.debilidades && det.debilidades.length > 0 && (
                      <div style={{ background: 'rgba(231,76,60,0.04)', borderRadius: '8px', padding: '14px' }}>
                        <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#e74c3c' }}>⚠️ Debilidades</h4>
                        <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#555', lineHeight: 1.7 }}>
                          {det.debilidades.map((d, i) => <li key={i}>{d}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </details>
            )
          })}
        </div>
      )}

      {Object.keys(matrizGlobal).length > 0 && (
        <div className="card" style={{ marginTop: '20px', overflow: 'auto' }}>
          <h3>📊 Matriz de Comparacion (RMSE)</h3>
          <p style={{ color: '#8892a4', fontSize: '12px', marginBottom: '10px' }}>
            ✅ = mejor modelo · ⏳ = en progreso · Valores = RMSE (menor es mejor)
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '12px', whiteSpace: 'nowrap' }}>
              <thead>
                <tr style={{ background: 'var(--bg-app)' }}>
                  <th style={{ position: 'sticky', left: 0, background: 'var(--bg-app)', zIndex: 1, minWidth: '130px' }}>Producto</th>
                  {Object.keys(ALGO_COLORS).map(algo => (
                    <th key={algo} style={{ padding: '6px 10px', fontSize: '11px' }}>{algo.length > 15 ? algo.slice(0, 12) + '...' : algo}</th>
                  ))}
                  <th style={{ padding: '6px 10px' }}>🏆</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(matrizGlobal).map(([pid, algos]) => {
                  const nombre = productosProcesados.find(p => p.producto_id === parseInt(pid))?.producto || `ID ${pid}`
                  const mejor = mejorPorProducto[pid]
                  const entrada = productosProcesados.find(p => p.producto_id === parseInt(pid))
                  const resultados = entrada?.resultados || []
                  return (
                    <tr key={pid} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ position: 'sticky', left: 0, background: 'var(--bg-card)', fontWeight: 500, fontSize: '12px' }}>{nombre}</td>
                      {Object.keys(ALGO_COLORS).map(algo => {
                        const res = resultados.find(r => r.algoritmo === algo)
                        if (!res) return <td key={algo} style={{ textAlign: 'center', color: '#8892a4' }}>⏳</td>
                        if (res.error) return <td key={algo} style={{ textAlign: 'center', color: '#e74c3c' }}>⚠️</td>
                        const esMejor = mejor?.algoritmo === algo
                        return (
                          <td key={algo} style={{
                            textAlign: 'center',
                            color: esMejor ? '#27ae60' : '#8892a4',
                            fontWeight: esMejor ? 700 : 400,
                            background: esMejor ? 'rgba(39,174,96,0.08)' : 'transparent',
                          }}>
                            {esMejor ? '✅ ' : ''}{res.rmse.toFixed(1)}
                          </td>
                        )
                      })}
                      <td style={{ textAlign: 'center', fontWeight: 600, color: '#667eea' }}>{mejor?.algoritmo || '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {resumenFinal && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3>🏆 Ranking Final</h3>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '15px' }}>
            Total: {resumenFinal.productos_con_modelo} productos con modelo · Duracion: {formatSecs(resumenFinal.duracion_total)}
            {resumenFinal.resumen_algoritmos && ` · Algoritmo dominante: ${Object.entries(resumenFinal.resumen_algoritmos).sort((a, b) => b[1] - a[1])[0]?.[0] || '—'}`}
          </p>
          {resumenFinal.resumen_algoritmos && Object.entries(resumenFinal.resumen_algoritmos).sort((a, b) => b[1] - a[1]).map(([algo, count], i) => {
            const maxCount = Object.values(resumenFinal.resumen_algoritmos).reduce((a, b) => Math.max(a, b), 1)
            const barPct = Math.round((count / maxCount) * 100)
            const medals = ['🥇', '🥈', '🥉']
            return (
              <div key={algo} style={{ marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '180px', fontSize: '13px', fontWeight: 500 }}>
                  {medals[i] || ''} {algo}
                </span>
                <div className="progress-bar-track" style={{ flex: 1, height: '16px', borderRadius: '6px' }}>
                  <div className="progress-bar-fill" style={{
                    width: `${barPct}%`,
                    background: ALGO_COLORS[algo] || '#667eea',
                    borderRadius: '6px',
                    display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: '8px',
                    fontSize: '11px', color: '#fff', fontWeight: 600, minWidth: count > 0 ? 'fit-content' : 0,
                  }}>
                    {count > 0 && count}
                  </div>
                </div>
                <span style={{ fontSize: '12px', color: '#8892a4', width: '60px', textAlign: 'right' }}>
                  {count} ({Math.round((count / (resumenFinal.productos_con_modelo || 1)) * 100)}%)
                </span>
              </div>
            )
          })}

          {resumenFinal.resumen_confianza && (
            <div style={{ marginTop: '15px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              <span style={{ background: 'rgba(39,174,96,0.08)', color: '#27ae60', padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>
                ✅ Alta: {resumenFinal.resumen_confianza.altos}
              </span>
              <span style={{ background: 'rgba(243,156,18,0.08)', color: '#f39c12', padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>
                ⚠️ Media: {resumenFinal.resumen_confianza.medios}
              </span>
              <span style={{ background: 'rgba(231,76,60,0.08)', color: '#e74c3c', padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>
                🔴 Baja: {resumenFinal.resumen_confianza.bajos}
              </span>
            </div>
          )}

          {resumenFinal.recomendaciones_globales && resumenFinal.recomendaciones_globales.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#667eea', marginBottom: '8px' }}>💡 Recomendaciones Globales</h4>
              {resumenFinal.recomendaciones_globales.map((rec, i) => (
                <p key={i} style={{ fontSize: '12px', color: '#555', marginBottom: '4px', lineHeight: 1.4 }}>
                  • {rec}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {modelosInfo && modelosInfo.length > 0 && !streaming && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3>🏆 Mejores Modelos por Producto</h3>
          <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '13px' }}>
              <thead><tr><th>Producto</th><th>Algoritmo</th><th>R²</th><th>RMSE</th></tr></thead>
              <tbody>
                {modelosInfo.filter(m => m.modelo_disponible).map(m => (
                  <tr key={m.producto_id}>
                    <td>{m.producto_nombre}</td>
                    <td><span style={{ background: 'rgba(102,126,234,0.08)', color: '#667eea', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{m.mejor_algoritmo || '?'}</span></td>
                    <td style={{ color: (m.r2 || 0) > 0.6 ? '#27ae60' : (m.r2 || 0) > 0.4 ? '#f39c12' : '#e74c3c', fontWeight: 600 }}>{m.r2 ? (m.r2 * 100).toFixed(1) + '%' : '—'}</td>
                    <td style={{ color: '#8892a4' }}>{m.rmse ? m.rmse.toFixed(1) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
                  <span style={{ background: 'rgba(102,126,234,0.08)', color: '#667eea', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>
                    {p.algoritmo_utilizado || 'Random Forest'}
                  </span>
                </td>
                <td style={{ color: (p.confianza_prediccion || 0) > 0.6 ? '#27ae60' : (p.confianza_prediccion || 0) > 0.4 ? '#f39c12' : '#e74c3c', fontWeight: 600 }}>
                  {p.confianza_prediccion !== null && p.confianza_prediccion !== undefined
                    ? Math.max(0, p.confianza_prediccion * 100).toFixed(1) + '%'
                    : '—'}
                </td>
              </tr>
            )}
          />
        )}
      </div>
    </>
  )
}
