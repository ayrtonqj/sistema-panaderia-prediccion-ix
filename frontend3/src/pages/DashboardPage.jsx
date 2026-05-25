import { useState, useEffect, useRef } from 'react'
import { api } from '../api/api'
import { Bar } from 'react-chartjs-2'
import { Chart, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { formatDayShort } from '../utils/formatters'

Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [nProductos, setNProductos] = useState(0)
  const [alertas, setAlertas] = useState(null)
  const [recomendaciones, setRecomendaciones] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('produccion')
  const [eficiencia, setEficiencia] = useState(null)
  const [alertasInsumos, setAlertasInsumos] = useState([])
  const [ventasHoy, setVentasHoy] = useState(null)
  const [ordenesSugeridas, setOrdenesSugeridas] = useState(0)
  const chartRef = useRef(null)

  useEffect(() => {
    Promise.all([
      api.get('/dashboard/resumen'),
      api.get('/productos/'),
      api.get('/alertas/sobreproduccion').catch(() => null),
      api.get('/predicciones/recomendaciones').catch(() => null),
      api.get('/dashboard/eficiencia?dias=1').catch(() => null),
      api.get('/insumos/alertas/').catch(() => null),
      api.get('/ventas/hoy').catch(() => null),
      api.get('/ordenes-compra/').catch(() => null),
    ]).then(([resumen, productos, al, rec, ef, ins, ven, ords]) => {
      if (Array.isArray(ords)) {
        setOrdenesSugeridas(ords.filter(o => o.es_sugerida && o.estado === 'pendiente').length)
      }
      setData(resumen)
      setNProductos(Array.isArray(productos) ? productos.length : 0)
      setAlertas(al)
      setRecomendaciones(rec)
      setEficiencia(ef)
      setAlertasInsumos(Array.isArray(ins) ? ins : [])
      setVentasHoy(ven)
    }).catch(() => {
      setError('No se puede conectar con el servidor. Verifica que el backend esté en http://localhost:8000')
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card"><p style={{color:'#718096'}}>Cargando dashboard...</p></div>
  if (error) return <div className="alert alert-error">⚠️ {error}</div>
  if (!data) return <div className="alert alert-error">⚠️ No se pudieron cargar los datos</div>

  const predicciones = data.prediccion_semana || []
  const chartData = predicciones.length > 0 ? {
    labels: predicciones.map(p => p.producto),
    datasets: [{
      label: 'Demanda estimada (7 días)',
      data: predicciones.map(p => p.demanda_total_7d),
      backgroundColor: '#667eea',
      borderColor: '#764ba2',
      borderWidth: 1,
    }],
  } : null

  return (
    <>
        <div className="page-header">
        <h1>🏠 Dashboard Panadería Victoria</h1>
      </div>

      <div className="grid-4">
        <div className="metric">
          <div className="value">{Math.round(data.ventas_hoy || 0)} uds</div>
          <div className="label">📦 Ventas Hoy</div>
        </div>
        <div className="metric">
          <div className="value" style={{ color: (data.mermas_hoy || 0) > 0 ? '#e74c3c' : undefined }}>
            {Math.round(data.mermas_hoy || 0)} uds
          </div>
          <div className="label">⚠️ Mermas Hoy</div>
        </div>
        <div className="metric">
          <div className="value" style={{ color: (data.pct_merma_30d || 0) > 20 ? '#e74c3c' : undefined }}>
            {data.pct_merma_30d || 0}%
          </div>
          <div className="label">📊 % Merma (30d)</div>
        </div>
        <div className="metric">
          <div className="value" style={{ color: (data.insumos_bajo_stock || 0) > 0 ? '#e74c3c' : undefined }}>
            {data.insumos_bajo_stock || 0}
          </div>
          <div className="label">🔴 Insumos en Alerta</div>
        </div>
      </div>

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setTab('produccion')}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: tab === 'produccion' ? '700' : '400',
              background: tab === 'produccion' ? '#667eea' : 'transparent',
              color: tab === 'produccion' ? '#fff' : '#4a5568',
              transition: 'all 0.2s',
            }}
          >🔮 Producción Sugerida</button>
          <button
            onClick={() => setTab('operaciones')}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: tab === 'operaciones' ? '700' : '400',
              background: tab === 'operaciones' ? '#667eea' : 'transparent',
              color: tab === 'operaciones' ? '#fff' : '#4a5568',
              transition: 'all 0.2s',
            }}
          >📋 Resumen de Operaciones</button>
          <button
            onClick={() => setTab('alertas')}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: tab === 'alertas' ? '700' : '400',
              background: tab === 'alertas' ? '#667eea' : 'transparent',
              color: tab === 'alertas' ? '#fff' : '#4a5568',
              transition: 'all 0.2s',
            }}
          >🚨 Alertas de Sobreproducción</button>
          <button
            onClick={() => setTab('recomendaciones')}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: tab === 'recomendaciones' ? '700' : '400',
              background: tab === 'recomendaciones' ? '#667eea' : 'transparent',
              color: tab === 'recomendaciones' ? '#fff' : '#4a5568',
              transition: 'all 0.2s',
            }}
          >🔮 Recomendaciones del Modelo</button>
        </div>
      </div>

      {tab === 'produccion' && (
        <div className="card">
          <h3>🔮 Producción Sugerida (Próximos 7 días)</h3>
          {chartData ? (
            <div style={{ height: '250px' }}>
              <Bar ref={chartRef} data={chartData} options={{
                responsive: true,
                maintainAspectRatio: false,
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
            <div className="metric" style={{ borderLeft: `4px solid ${eficiencia?.global?.eficiencia_pct >= 80 ? '#27ae60' : '#e74c3c'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>📊 Eficiencia de Producción</div>
              <div style={{ marginTop: '12px' }}>
                <div style={{ height: '10px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(eficiencia?.global?.eficiencia_pct || 0, 100)}%`,
                    background: (eficiencia?.global?.eficiencia_pct || 0) >= 80 ? '#27ae60' : '#e74c3c',
                    borderRadius: '4px',
                    transition: 'width 0.5s',
                  }} />
                </div>
                <div className="value" style={{ fontSize: '28px', marginTop: '8px', color: (eficiencia?.global?.eficiencia_pct || 0) >= 80 ? '#27ae60' : '#e74c3c' }}>
                  {eficiencia?.global?.eficiencia_pct || 0}%
                </div>
              </div>
            </div>

            <div className="metric" style={{ borderLeft: '4px solid #f39c12', padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>🥇 Producto Estrella del Día</div>
              <div className="value" style={{ fontSize: '24px', color: '#f39c12', marginTop: '8px' }}>
                {ventasHoy?.productos?.[0]?.producto_nombre || '—'}
              </div>
              <div style={{ fontSize: '14px', color: '#8892a4', marginTop: '5px' }}>
                {ventasHoy?.productos?.[0]?.total_vendido ? `${ventasHoy.productos[0].total_vendido} uds vendidas` : 'Sin ventas hoy'}
              </div>
            </div>

            <div className="metric" style={{ borderLeft: `4px solid ${alertasInsumos.length > 0 ? '#e74c3c' : '#27ae60'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>🏪 Insumos Críticos</div>
              <div className="value" style={{ fontSize: '28px', color: alertasInsumos.length > 0 ? '#e74c3c' : '#27ae60', marginTop: '8px' }}>
                {alertasInsumos.length > 0 ? alertasInsumos.length : '0'}
              </div>
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
              {alertasInsumos.length === 0 && (
                <div style={{ fontSize: '13px', color: '#8892a4', marginTop: '5px' }}>Todos los insumos en nivel adecuado</div>
              )}
            </div>

            <div className="metric" style={{ borderLeft: `4px solid ${(data.ordenes_pendientes || 0) > 0 ? '#f39c12' : '#27ae60'}`, padding: '20px' }}>
              <div className="label" style={{ fontSize: '15px' }}>📋 Órdenes Pendientes</div>
              <div className="value" style={{ fontSize: '28px', color: (data.ordenes_pendientes || 0) > 0 ? '#f39c12' : '#27ae60', marginTop: '8px' }}>
                {data.ordenes_pendientes || 0}
              </div>
              <div style={{ fontSize: '13px', color: '#8892a4', marginTop: '5px' }}>
                {(data.ordenes_pendientes || 0) > 0 ? 'Revisar en Órdenes de Compra' : 'Sin órdenes pendientes'}
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'alertas' && (
        <>
          {ordenesSugeridas > 0 && (
            <div className="card" style={{ borderLeft: '4px solid #f39c12', marginBottom: '15px' }}>
              <h3 style={{ color: '#f39c12' }}>📋 Órdenes Sugeridas Pendientes ({ordenesSugeridas})</h3>
              <p style={{ color: '#8892a4' }}>
                Hay {ordenesSugeridas} orden(es) de compra sugeridas pendientes de revisión.
                Ve a <strong>Órdenes de Compra</strong> para revisarlas, editarlas, confirmarlas o cancelarlas.
              </p>
            </div>
          )}
          {alertas && alertas.total_alertas > 0 && (
            <div className="card" style={{ borderLeft: '4px solid #e74c3c' }}>
              <h3 style={{ color: '#e74c3c' }}>🚨 Alertas de Sobreproducción (últimos {alertas.periodo_dias} días)</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginTop: '10px' }}>
                {alertas.alertas.map(a => (
                  <div key={a.producto_id} className="metric" style={{ flex: '1 1 250px', borderLeft: '3px solid #e74c3c' }}>
                    <div className="label" style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>
                      {a.producto_nombre}
                    </div>
                    <div className="value" style={{ fontSize: '20px', color: '#e74c3c' }}>
                      {a.tasa_sobreproduccion_pct}%
                    </div>
                    <div style={{ fontSize: '12px', color: '#8892a4', marginTop: '5px' }}>
                      {a.unidades_perdidas} uds perdidas en {a.frecuencia} registro(s)
                    </div>
                    <div style={{ fontSize: '12px', color: '#e67e22', marginTop: '3px' }}>
                      💡 Considere reducir producción en {a.reduccion_sugerida_pct}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {alertas && alertas.total_alertas === 0 && (
            <div className="card" style={{ borderLeft: '4px solid #27ae60' }}>
              <h3 style={{ color: '#27ae60' }}>✅ Sin Alertas de Sobreproducción</h3>
              <p style={{ color: '#8892a4' }}>Ningún producto supera el umbral del {alertas.umbral_pct}% en los últimos {alertas.periodo_dias} días.</p>
            </div>
          )}
        </>
      )}

      {tab === 'recomendaciones' && (
        <>
          {recomendaciones && recomendaciones.recomendaciones.length > 0 ? (
            <div className="card">
              <h3>🔮 Recomendaciones del Modelo (próximos 7 días)</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '10px' }}>
                {recomendaciones.recomendaciones.map((r, i) => (
                  <div key={i} className="metric" style={{
                    flex: '1 1 280px',
                    borderLeft: `4px solid ${r.tipo === 'aumentar' ? '#27ae60' : '#e74c3c'}`,
                  }}>
                    <div style={{ fontSize: '13px', color: '#8892a4' }}>
                      {formatDayShort(r.fecha)}
                    </div>
                    <div className="label" style={{ fontSize: '14px', fontWeight: 'bold', margin: '4px 0' }}>
                      {r.producto}
                    </div>
                    <div className="value" style={{
                      fontSize: '18px',
                      color: r.tipo === 'aumentar' ? '#27ae60' : '#e74c3c',
                    }}>
                      {r.diferencia_pct > 0 ? '+' : ''}{r.diferencia_pct}%
                    </div>
                    <div style={{ fontSize: '12px', color: '#8892a4', marginTop: '5px' }}>
                      {r.mensaje}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card">
              <h3>🔮 Recomendaciones del Modelo</h3>
              <p style={{ color: '#8892a4' }}>No hay recomendaciones generadas para los próximos 7 días.</p>
            </div>
          )}
        </>
      )}

      <div className="grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>📦 Productos</h3>
          <div style={{ fontSize: '32px', color: '#667eea' }}>{nProductos}</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>📈 Ventas 7 días</h3>
          <div style={{ fontSize: '32px', color: '#27ae60' }}>{Math.round(data.ventas_7d || 0)}</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>📉 Mermas 30 días</h3>
          <div style={{ fontSize: '32px', color: '#e74c3c' }}>{Math.round(data.mermas_30d || 0)}</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>🛒 Órdenes Pendientes</h3>
          <div style={{ fontSize: '32px', color: '#f39c12' }}>{data.ordenes_pendientes || 0}</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>🤖 Órdenes Sugeridas</h3>
          <div style={{ fontSize: '32px', color: ordenesSugeridas > 0 ? '#f39c12' : '#27ae60' }}>{ordenesSugeridas}</div>
        </div>
      </div>
    </>
  )
}
