import { useState, useEffect, useRef } from 'react'
import { api } from '../api/api'
import { Bar } from 'react-chartjs-2'
import { Chart, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { formatDayShort } from '../utils/formatters'
import { enviarPorCorreo } from '../utils/pdf'


Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)


function Sparkline({ data, color, height = 28 }) {
  if (!data || data.length < 2) return <div style={{ height, opacity: 0.3 }} />
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  const w = data.length * 10
  const points = data.map((v, i) => `${i * 10},${height - ((v - min) / range) * height}`).join(' ')
  return (
    <svg width={w} height={height} style={{ display: 'block', marginTop: '4px' }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [nProductos, setNProductos] = useState(0)
  const [alertas, setAlertas] = useState(null)
  const [recomendaciones, setRecomendaciones] = useState(null)
  const [kpis, setKpis] = useState(null)
  const [estado, setEstado] = useState(null)
  const [cardGroup, setCardGroup] = useState(0)
  const [recGroup, setRecGroup] = useState(0)
  const [alertGroup, setAlertGroup] = useState(0)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('produccion')
  const [eficiencia, setEficiencia] = useState(null)
  const [alertasInsumos, setAlertasInsumos] = useState([])
  const [ventasHoy, setVentasHoy] = useState(null)
  const [ordenesSugeridas, setOrdenesSugeridas] = useState(0)
  const [sugerencias, setSugerencias] = useState(null)
  const chartRef = useRef(null)

  const cargarDashboard = () => {
    Promise.all([
      api.get('/dashboard/resumen').catch(() => null),
      api.get('/productos/').catch(() => []),
      api.get('/alertas/sobreproduccion').catch(() => null),
      api.get('/predicciones/recomendaciones').catch(() => null),
      api.get('/dashboard/eficiencia?dias=1').catch(() => null),
      api.get('/insumos/alertas/').catch(() => null),
      api.get('/ventas/hoy').catch(() => null),
      api.get('/ordenes-compra/').catch(() => null),
      api.get('/produccion/sugerida').catch(() => null),
      api.get('/dashboard/kpis').catch(() => null),
      api.get('/sistema/estado').catch(() => null),
    ]).then(([resumen, productos, al, rec, ef, ins, ven, ords, sug, kpis, estado]) => {
      if (Array.isArray(ords)) setOrdenesSugeridas(ords.filter(o => o.es_sugerida && o.estado === 'pendiente').length)
      if (resumen) setData(resumen)
      setNProductos(Array.isArray(productos) ? productos.length : 0)
      if (al) setAlertas(al)
      if (rec) setRecomendaciones(rec)
      if (ef) setEficiencia(ef)
      setAlertasInsumos(Array.isArray(ins) ? ins : [])
      if (ven) setVentasHoy(ven)
      setSugerencias(Array.isArray(sug) ? sug : null)
      if (kpis) setKpis(kpis)
      if (estado) setEstado(estado)
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { cargarDashboard() }, [])
  useEffect(() => { const id = setInterval(cargarDashboard, 30000); return () => clearInterval(id) }, [])

  if (loading) return <div className="card"><p style={{color:'#718096'}}>Cargando dashboard...</p></div>
  if (error) return <div className="alert alert-error">⚠️ {error}</div>
  if (!data) return <div className="alert alert-error">⚠️ No se pudieron cargar los datos</div>

  const predicciones = data.prediccion_semana || []
  const chartData = predicciones.length > 0 ? {
    labels: predicciones.map(p => p.producto),
    datasets: [{
      label: 'Demanda estimada (7 dias)',
      data: predicciones.map(p => p.demanda_total_7d),
      backgroundColor: '#667eea',
      borderColor: '#764ba2',
      borderWidth: 1,
    }],
  } : null

  return (
    <>
      <div className="page-header" style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ marginBottom: '2px' }}>🏠 Dashboard Panaderia Victoria</h1>
          {estado && (
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '6px' }}>
              <span style={{ fontSize: '11px', color: estado.base_de_datos?.conectada ? '#27ae60' : '#e74c3c', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: estado.base_de_datos?.conectada ? '#27ae60' : '#e74c3c', display: 'inline-block' }} /> BD
              </span>
              <span style={{ fontSize: '11px', color: estado.machine_learning?.todos_entrenados ? '#27ae60' : '#f39c12', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: estado.machine_learning?.todos_entrenados ? '#27ae60' : '#f39c12', display: 'inline-block' }} /> {estado.machine_learning?.modelos_listos || 0}/{estado.machine_learning?.total_productos || 0} Modelos ML
              </span>
              <span style={{ fontSize: '11px', color: '#8892a4' }}>
                📊 {estado.base_de_datos?.ventas || 0} ventas · {estado.base_de_datos?.mermas || 0} mermas
              </span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button className="btn" style={{ fontSize: '11px', padding: '6px 10px' }} onClick={cargarDashboard}>🔄 Actualizar</button>
          {kpis && <button className="btn btn-danger" style={{ fontSize: '11px', padding: '6px 10px' }} onClick={() => {
            const rows = [
              ['Ingresos Hoy', kpis.ingresos_hoy ? 'S/ ' + kpis.ingresos_hoy.toLocaleString() : '-'],
              ['Ventas Hoy', (data.ventas_hoy || 0) + ' uds'],
              ['Merma Hoy', kpis.merma_hoy + ' uds'],
              ['Eficiencia', kpis.eficiencia_produccion_pct + '%'],
              ['Margen Bruto', kpis.margen_bruto_estimado ? 'S/ ' + kpis.margen_bruto_estimado.toLocaleString() : '-'],
              ['% Merma 30d', (data.pct_merma_30d || 0) + '%'],
              ['Prod. Hoy', kpis.produccion_unidades_hoy + ' uds'],
              ['Ventas 7d', Math.round(data.ventas_7d || 0) + ' uds'],
              ['Insumos Alerta', data.insumos_bajo_stock || 0],
              ['Ord. Pendientes', data.ordenes_pendientes || 0],
            ]
            enviarPorCorreo('Dashboard - Reporte Completo', ['Métrica', 'Valor'], rows)
          }}>📧 Enviar Reportes</button>}
        </div>
      </div>

      {kpis && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button onClick={() => setCardGroup(g => (g + 3) % 4)} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
            }}>‹</button>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', flex: 1 }}>
              {(() => {
                const tend = kpis.tendencias || {}
                const spark = kpis.sparklines || {}
                const allCards = [
                  [
                    { icon: '💰', label: 'Ingresos Hoy', value: `S/ ${kpis.ingresos_hoy?.toLocaleString()}`, color: '#667eea', trend: tend.ingresos, spark: null },
                    { icon: '📊', label: 'Margen Bruto', value: `S/ ${kpis.margen_bruto_estimado?.toLocaleString()}`, color: '#27ae60', trend: null, spark: null },
                    { icon: '⚙️', label: 'Eficiencia', value: `${kpis.eficiencia_produccion_pct}%`, color: kpis.eficiencia_produccion_pct > 80 ? '#27ae60' : '#f39c12', trend: tend.eficiencia, spark: null },
                  ],
                  [
                    { icon: '📦', label: 'Ventas Hoy', value: `${Math.round(data.ventas_hoy || 0)} uds`, color: '#1abc9c', trend: tend.ventas_uds, spark: spark.ventas },
                    { icon: '🗑️', label: 'Merma Hoy', value: `${kpis.merma_hoy} uds`, color: '#e74c3c', trend: tend.merma, spark: spark.mermas },
                    { icon: '📊', label: '% Merma 30d', value: `${data.pct_merma_30d || 0}%`, color: (data.pct_merma_30d || 0) > 20 ? '#e74c3c' : '#f39c12', trend: null, spark: null },
                  ],
                  [
                    { icon: '📈', label: 'Ventas 7d', value: Math.round(data.ventas_7d || 0), color: '#27ae60', trend: null, spark: spark.ventas },
                    { icon: '🏭', label: 'Prod. Hoy', value: `${kpis.produccion_unidades_hoy} uds`, color: '#9b59b6', trend: tend.produccion, spark: spark.produccion },
                    { icon: '🔴', label: 'Insumos Alerta', value: data.insumos_bajo_stock || 0, color: (data.insumos_bajo_stock || 0) > 0 ? '#e74c3c' : '#27ae60', trend: null, spark: null },
                  ],
                  [
                    { icon: '📦', label: 'Productos', value: nProductos, color: '#667eea', trend: null, spark: null },
                    { icon: '🛒', label: 'Ord. Pendientes', value: data.ordenes_pendientes || 0, color: (data.ordenes_pendientes || 0) > 0 ? '#f39c12' : '#27ae60', trend: null, spark: null },
                    { icon: '🤖', label: 'Ord. Sugeridas', value: ordenesSugeridas, color: ordenesSugeridas > 0 ? '#f39c12' : '#27ae60', trend: null, spark: null },
                  ],
                ]
                return (allCards[cardGroup] || allCards[0]).map((c, i) => (
                  <div key={i} className="card" style={{ borderTop: `3px solid ${c.color}`, padding: '14px 16px', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', color: '#8892a4', fontWeight: 500 }}>{c.label}</span>
                      <span style={{ fontSize: '14px' }}>{c.icon}</span>
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: c.color, marginBottom: '2px' }}>{c.value}</div>
                    <div style={{ minHeight: '20px' }}>
                      {c.trend != null && (
                        <span style={{ fontSize: '11px', fontWeight: 600, color: c.trend > 0 ? '#27ae60' : c.trend < 0 ? '#e74c3c' : '#8892a4' }}>
                          {c.trend > 0 ? '↑' : c.trend < 0 ? '↓' : '→'} {Math.abs(c.trend)}% vs ayer
                        </span>
                      )}
                    </div>
                    {c.spark && <Sparkline data={c.spark} color={c.color} />}
                  </div>
                ))
              })()}
            </div>

            <button onClick={() => setCardGroup(g => (g + 1) % 4)} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
            }}>›</button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '10px' }}>
            {[0, 1, 2, 3].map(g => (
              <div key={g} onClick={() => setCardGroup(g)} style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: cardGroup === g ? '#667eea' : '#d1d5db',
                cursor: 'pointer', transition: 'background 0.2s',
              }} />
            ))}
          </div>
        </div>
      )}



      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {[{ key: 'produccion', icon: '🔮', label: 'Prod. Sugerida' },
            { key: 'operaciones', icon: '📋', label: 'Operaciones' },
            { key: 'alertas', icon: '🚨', label: 'Alertas' },
            { key: 'recomendaciones', icon: '💡', label: 'Recomendaciones' }].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 18px', border: tab === t.key ? '2px solid #667eea' : '2px solid transparent',
              borderRadius: '20px', cursor: 'pointer', fontWeight: 600, fontSize: '12px',
              background: tab === t.key ? 'rgba(102,126,234,0.08)' : 'transparent',
              color: tab === t.key ? '#667eea' : '#8892a4',
              transition: 'all 0.2s',
            }}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'produccion' && (
        <div className="card">
          <h3>🔮 Produccion Sugerida (Proximos 7 dias)</h3>
          {chartData ? (
            <div className="chart-container-mobile" style={{ height: '250px' }}>
              <Bar ref={chartRef} data={chartData} options={{
                responsive: true, maintainAspectRatio: false,
                scales: {
                  y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#4a5568' } },
                  x: { grid: { display: false }, ticks: { color: '#4a5568' } },
                },
                plugins: { legend: { labels: { color: '#4a5568' } } },
              }} />
            </div>
          ) : (
            <p style={{ color: '#8892a4' }}>No hay predicciones generadas. Ve a Predicciones para generarlas.</p>
          )}
        </div>
      )}

      {tab === 'operaciones' && (
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
            <div className="metric" style={{ borderLeft: `4px solid ${(eficiencia?.global?.eficiencia_pct || 0) >= 80 ? '#27ae60' : '#e74c3c'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>📊 Eficiencia de Produccion</div>
              <div style={{ marginTop: '12px' }}>
                <div style={{ height: '10px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.min(eficiencia?.global?.eficiencia_pct || 0, 100)}%`, background: (eficiencia?.global?.eficiencia_pct || 0) >= 80 ? '#27ae60' : '#e74c3c', borderRadius: '4px', transition: 'width 0.5s' }} />
                </div>
                <div className="value" style={{ fontSize: '28px', marginTop: '8px', color: (eficiencia?.global?.eficiencia_pct || 0) >= 80 ? '#27ae60' : '#e74c3c' }}>{eficiencia?.global?.eficiencia_pct || 0}%</div>
              </div>
            </div>
            <div className="metric" style={{ borderLeft: '4px solid #f39c12', padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>🥇 Producto Estrella del Dia</div>
              <div className="value" style={{ fontSize: '24px', color: '#f39c12', marginTop: '8px' }}>{ventasHoy?.productos?.[0]?.producto_nombre || '—'}</div>
              <div style={{ fontSize: '14px', color: '#8892a4', marginTop: '5px' }}>{ventasHoy?.productos?.[0]?.total_vendido ? `${ventasHoy.productos[0].total_vendido} uds vendidas` : 'Sin ventas hoy'}</div>
            </div>
            <div className="metric" style={{ borderLeft: `4px solid ${alertasInsumos.length > 0 ? '#e74c3c' : '#27ae60'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>🏪 Insumos Criticos</div>
              <div className="value" style={{ fontSize: '28px', color: alertasInsumos.length > 0 ? '#e74c3c' : '#27ae60', marginTop: '8px' }}>{alertasInsumos.length > 0 ? alertasInsumos.length : '0'}</div>
              {alertasInsumos.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  {alertasInsumos.slice(0, 3).map((ins, i) => (
                    <div key={i} style={{ fontSize: '13px', color: '#8892a4', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{ins.nombre}</span>
                      <span style={{ color: '#e74c3c' }}>{ins.stock_actual}/{ins.stock_minimo}</span>
                    </div>
                  ))}
                </div>
              )}
              {alertasInsumos.length === 0 && <div style={{ fontSize: '13px', color: '#8892a4', marginTop: '5px' }}>Todos los insumos en nivel adecuado</div>}
            </div>
            <div className="metric" style={{ borderLeft: `4px solid ${(data.ordenes_pendientes || 0) > 0 ? '#f39c12' : '#27ae60'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>📋 Ordenes Pendientes</div>
              <div className="value" style={{ fontSize: '28px', color: (data.ordenes_pendientes || 0) > 0 ? '#f39c12' : '#27ae60', marginTop: '8px' }}>{data.ordenes_pendientes || 0}</div>
              <div style={{ fontSize: '13px', color: '#8892a4', marginTop: '5px' }}>{(data.ordenes_pendientes || 0) > 0 ? 'Revisar en Ordenes de Compra' : 'Sin ordenes pendientes'}</div>
            </div>
          </div>
        </div>
      )}

      {tab === 'alertas' && (() => {
        const items = alertas?.alertas || []
        const ALERTS_PER_PAGE = 6
        const alertPages = Array.from(
          { length: Math.ceil(items.length / ALERTS_PER_PAGE) },
          (_, i) => items.slice(i * ALERTS_PER_PAGE, (i + 1) * ALERTS_PER_PAGE)
        )
        const page = alertPages[alertGroup] || []

        return (
          <>
            {ordenesSugeridas > 0 && (
              <div className="card" style={{ borderLeft: '4px solid #f39c12', marginBottom: '15px' }}>
                <h3 style={{ color: '#f39c12' }}>📋 Ordenes Sugeridas Pendientes ({ordenesSugeridas})</h3>
                <p style={{ color: '#8892a4' }}>Hay {ordenesSugeridas} orden(es) de compra sugeridas pendientes de revision. Ve a <strong>Ordenes de Compra</strong> para revisarlas.</p>
              </div>
            )}
            {alertas && alertas.total_alertas > 0 ? (
              <div className="card" style={{ borderLeft: '4px solid #e74c3c' }}>
                <h3 style={{ color: '#e74c3c' }}>🚨 Alertas de Sobreproduccion (ultimos {alertas.periodo_dias} dias)</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                  {alertPages.length > 1 && (
                    <button onClick={() => setAlertGroup(g => (g - 1 + alertPages.length) % alertPages.length)} style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
                    }}>‹</button>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', flex: 1 }}>
                    {page.map(a => (
                      <div key={a.producto_id} className="metric" style={{
                        borderLeft: '3px solid #e74c3c', padding: '12px',
                      }}>
                        <div className="label" style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>{a.producto_nombre}</div>
                        <div className="value" style={{ fontSize: '20px', color: '#e74c3c' }}>{a.tasa_sobreproduccion_pct}%</div>
                        <div style={{ fontSize: '12px', color: '#8892a4', marginTop: '5px' }}>{a.unidades_perdidas} uds perdidas en {a.frecuencia} registro(s)</div>
                        <div style={{ fontSize: '12px', color: '#e67e22', marginTop: '3px' }}>💡 Considere reducir produccion en {a.reduccion_sugerida_pct}%</div>
                      </div>
                    ))}
                  </div>
                  {alertPages.length > 1 && (
                    <button onClick={() => setAlertGroup(g => (g + 1) % alertPages.length)} style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
                    }}>›</button>
                  )}
                </div>
                {alertPages.length > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '10px' }}>
                    {alertPages.map((_, g) => (
                      <div key={g} onClick={() => setAlertGroup(g)} style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: alertGroup === g ? '#e74c3c' : '#d1d5db',
                        cursor: 'pointer', transition: 'background 0.2s',
                      }} />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="card" style={{ borderLeft: '4px solid #27ae60' }}>
                <h3 style={{ color: '#27ae60' }}>✅ Sin Alertas de Sobreproduccion</h3>
                <p style={{ color: '#8892a4' }}>Ningun producto supera el umbral del {alertas?.umbral_pct || 10}% en los ultimos {alertas?.periodo_dias || 7} dias.</p>
              </div>
            )}
          </>
        )
      })()}

      {tab === 'recomendaciones' && (() => {
        const items = recomendaciones?.recomendaciones || []
        const RECS_PER_PAGE = 6
        const recPages = Array.from(
          { length: Math.ceil(items.length / RECS_PER_PAGE) },
          (_, i) => items.slice(i * RECS_PER_PAGE, (i + 1) * RECS_PER_PAGE)
        )
        const page = recPages[recGroup] || []

        return (
          <div className="card">
            <h3>🔮 Recomendaciones del Modelo (proximos 7 dias)</h3>
            {items.length > 0 ? (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                  {recPages.length > 1 && (
                    <button onClick={() => setRecGroup(g => (g - 1 + recPages.length) % recPages.length)} style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
                    }}>‹</button>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', flex: 1 }}>
                    {page.map((r, i) => (
                      <div key={i} className="metric recomendacion-item" style={{
                        borderLeft: `4px solid ${r.tipo === 'aumentar' ? '#27ae60' : '#e74c3c'}`,
                        padding: '12px',
                      }}>
                        <div style={{ fontSize: '13px', color: '#8892a4' }}>{formatDayShort(r.fecha)}</div>
                        <div className="label" style={{ fontSize: '14px', fontWeight: 'bold', margin: '4px 0' }}>{r.producto}</div>
                        <div className="value" style={{ fontSize: '18px', color: r.tipo === 'aumentar' ? '#27ae60' : '#e74c3c' }}>{r.diferencia_pct > 0 ? '+' : ''}{r.diferencia_pct}%</div>
                        <div style={{ fontSize: '12px', color: '#8892a4', marginTop: '5px' }}>{r.mensaje}</div>
                      </div>
                    ))}
                  </div>
                  {recPages.length > 1 && (
                    <button onClick={() => setRecGroup(g => (g + 1) % recPages.length)} style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      fontSize: '18px', color: '#8892a4', padding: '4px 8px', borderRadius: '4px',
                    }}>›</button>
                  )}
                </div>
                {recPages.length > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '10px' }}>
                    {recPages.map((_, g) => (
                      <div key={g} onClick={() => setRecGroup(g)} style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: recGroup === g ? '#667eea' : '#d1d5db',
                        cursor: 'pointer', transition: 'background 0.2s',
                      }} />
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p style={{ color: '#8892a4' }}>No hay recomendaciones generadas para los proximos 7 dias.</p>
            )}
          </div>
        )
      })()}
    </>
  )
}
