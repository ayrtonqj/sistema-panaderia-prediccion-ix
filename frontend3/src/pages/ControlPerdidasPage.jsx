import { useState, useEffect, useRef } from 'react'
import { api } from '../api/api'
import { Bar } from 'react-chartjs-2'
import { Chart, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { openPrintWindow, tableHeaderHtml, descargarExcel, enviarPorCorreo } from '../utils/pdf'
import { formatDateChart, formatDateShort } from '../utils/formatters'

Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const TABS = [
  { key: 'eficiencia', label: '📈 Eficiencia' },
  { key: 'mermas', label: '📊 Análisis de Mermas' },
]

export default function ControlPerdidasPage() {
  const [tab, setTab] = useState('eficiencia')
  const [dias, setDias] = useState(30)
  const [eficiencia, setEficiencia] = useState(null)
  const [analisis, setAnalisis] = useState(null)
  const [mermas, setMermas] = useState([])
  const [loading, setLoading] = useState(true)
  const chartRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    if (tab === 'eficiencia') {
      api.get(`/dashboard/eficiencia?dias=${dias}`)
        .then(setEficiencia)
        .catch(() => {})
        .finally(() => setLoading(false))
    } else {
      Promise.all([
        api.get('/mermas/analisis'),
        api.get('/mermas/'),
      ]).then(([an, mer]) => {
        setAnalisis(an)
        setMermas(Array.isArray(mer) ? mer : [])
      }).catch(() => {}).finally(() => setLoading(false))
    }
  }, [tab, dias])

  const generarPDF = () => {
    if (tab === 'eficiencia') {
      const canvas = chartRef.current?.canvas
      const chartImg = canvas?.toDataURL ? canvas.toDataURL() : ''
      const prodBody = document.querySelector('#prodTable tbody')?.innerHTML || ''
      openPrintWindow('Control de Pérdidas - Panadería Victoria',
        tableHeaderHtml(`Eficiencia de Producción (últimos ${dias} días)`) +
        (chartImg ? `<img src="${chartImg}" style="width:100%;max-width:700px;display:block;margin:20px auto;" />` : '') +
        '<h3>Resumen por Producto</h3>' +
        '<table><thead><tr><th>Producto</th><th>Producido</th><th>Vendido</th><th>Merma</th><th>Eficiencia</th><th>Pérdida S/</th></tr></thead><tbody>' +
        prodBody + '</tbody></table>' +
        '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
      )
    } else {
      const mermasBody = document.querySelector('#mermasTable tbody')?.innerHTML || '<tr><td colspan="5">Sin datos</td></tr>'
      const pctEl = document.querySelector('#kpi-merma-pct')?.textContent || '0%'
      const unidadesEl = document.querySelector('#kpi-merma-uds')?.textContent || '0'
      const perdidaEl = document.querySelector('#kpi-merma-perdida')?.textContent || 'S/ 0.00'
      openPrintWindow('Control de Pérdidas - Panadería Victoria',
        tableHeaderHtml('Análisis de Mermas') +
        '<div class="metrics">' +
        `<div class="metric-box"><div class="value">${pctEl}</div><div class="label">% Merma Global</div></div>` +
        `<div class="metric-box"><div class="value">${unidadesEl}</div><div class="label">Unidades Perdidas</div></div>` +
        `<div class="metric-box"><div class="value">${perdidaEl}</div><div class="label">Pérdida Económica</div></div>` +
        '</div>' +
        '<h3 style="margin-top:20px;">Registro de Mermas</h3>' +
        '<table><thead><tr><th>ID</th><th>Producto</th><th>Fecha</th><th>Cantidad</th><th>Motivo</th></tr></thead><tbody>' +
        mermasBody + '</tbody></table>' +
        '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
      )
    }
  }

  const g = eficiencia?.global || {}
  const diario = eficiencia?.diario || []
  const porProducto = eficiencia?.por_producto || []

  const chartLabels = diario.map(d => formatDateChart(d.fecha))
  const chartData = diario.length > 0 ? {
    labels: chartLabels,
    datasets: [
      { label: 'Producción', data: diario.map(d => d.producido), backgroundColor: '#667eea', borderRadius: 3 },
      { label: 'Vendido',    data: diario.map(d => d.vendido),    backgroundColor: '#27ae60', borderRadius: 3 },
      { label: 'Merma',     data: diario.map(d => d.merma),     backgroundColor: '#e74c3c', borderRadius: 3 },
    ],
  } : null

  const eficChartData = diario.length > 0 ? {
    labels: chartLabels,
    datasets: [{
      label: 'Eficiencia %',
      data: diario.map(d => d.eficiencia_pct),
      borderColor: '#f39c12',
      backgroundColor: 'rgba(243,156,18,0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
    }],
  } : null

  if (loading) return <div className="card"><p>Cargando...</p></div>

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>📊 Control de Pérdidas</h1>
          <p style={{ color: '#8892a4' }}>Monitorea la eficiencia de producción y analiza las mermas</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {tab === 'eficiencia' && (
            <select value={dias} onChange={e => setDias(Number(e.target.value))} className="btn" style={{ padding: '6px 12px' }}>
              <option value={7}>7 días</option>
              <option value={15}>15 días</option>
              <option value={30}>30 días</option>
              <option value={60}>60 días</option>
            </select>
          )}
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
        <button className="btn btn-danger" onClick={generarPDF} style={{ fontSize: '11px', padding: '3px 8px', flexShrink: 0 }}>📄 PDF</button>
        <button className="btn" onClick={() => enviarPorCorreo('Control de Pérdidas', ['Producto', 'Producido', 'Vendido', 'Merma', 'Eficiencia'], (porProducto || []).map(p => [p.producto_nombre, p.total_producido, p.total_vendido, p.total_merma, p.eficiencia_pct + '%']))} style={{ fontSize: '11px', padding: '3px 8px', background: '#e74c3c', color: '#fff', flexShrink: 0 }}>📧 Enviar</button>
        <button className="btn" onClick={() => descargarExcel('ControlPerdidas', [{ key: "producto_nombre", label: "Producto" }, { key: "total_producido", label: "Producido" }, { key: "total_vendido", label: "Vendido" }, { key: "total_merma", label: "Merma" }, { key: "eficiencia_pct", label: "Eficiencia %" }], porProducto)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', flexShrink: 0 }}>📊 Excel</button>
        </div>
        </div>
      </div>

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '5px' }}>
          {TABS.map(t => (
            <button key={t.key}
              onClick={() => setTab(t.key)}
              style={{
                padding: '8px 20px',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: tab === t.key ? '700' : '400',
                background: tab === t.key ? '#667eea' : 'transparent',
                color: tab === t.key ? '#fff' : '#4a5568',
                transition: 'all 0.2s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'eficiencia' && eficiencia && (
        <>
          <div className="grid-4">
            <div className="metric">
              <div className="value">{Math.round(g.total_producido || 0)}</div>
              <div className="label">🏭 Total Producido</div>
            </div>
            <div className="metric">
              <div className="value" style={{ color: '#27ae60' }}>{Math.round(g.total_vendido || 0)}</div>
              <div className="label">✅ Total Vendido</div>
            </div>
            <div className="metric">
              <div className="value" style={{ color: (g.total_merma || 0) > 0 ? '#e74c3c' : undefined }}>{Math.round(g.total_merma || 0)}</div>
              <div className="label">⚠️ Total Merma</div>
            </div>
            <div className="metric">
              <div className="value" style={{ color: (g.eficiencia_pct || 0) < 80 ? '#e74c3c' : '#27ae60', fontSize: '28px' }}>
                {g.eficiencia_pct || 0}%
              </div>
              <div className="label">📊 Eficiencia Global</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>📊 Producción · Ventas · Merma por Día</h3>
              {chartData ? (
                <div style={{ height: '280px' }}>
                  <Bar ref={chartRef} data={chartData} options={{
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                      y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#4a5568' } },
                      x: { grid: { display: false }, ticks: { color: '#4a5568', maxTicksLimit: 15 } },
                    },
                    plugins: { legend: { labels: { color: '#4a5568', boxWidth: 12 } } },
                  }} />
                </div>
              ) : <p style={{ color: '#8892a4' }}>Sin datos para el período.</p>}
            </div>
            <div className="card">
              <h3>📈 Tendencia de Eficiencia</h3>
              {eficChartData ? (
                <div style={{ height: '280px' }}>
                  <Bar data={eficChartData} options={{
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                      y: { beginAtZero: true, max: 100, grid: { color: '#e2e8f0' }, ticks: { color: '#4a5568', callback: v => v + '%' } },
                      x: { grid: { display: false }, ticks: { color: '#4a5568', maxTicksLimit: 15 } },
                    },
                    plugins: { legend: { labels: { color: '#4a5568' } } },
                  }} />
                </div>
              ) : <p style={{ color: '#8892a4' }}>Sin datos para el período.</p>}
            </div>
          </div>

          <div className="card">
            <h3>📋 Resumen por Producto (ordenado por eficiencia)</h3>
            {porProducto.length > 0 ? (
              <table id="prodTable">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Producido</th>
                    <th>Vendido</th>
                    <th>Merma</th>
                    <th>Eficiencia</th>
                    <th>Pérdida S/</th>
                  </tr>
                </thead>
                <tbody>
                  {porProducto.map((r, i) => (
                    <tr key={i} style={(r.eficiencia_pct || 100) < 80 ? { background: 'rgba(231,76,60,0.08)' } : {}}>
                      <td>{r.producto}</td>
                      <td>{r.producido}</td>
                      <td>{r.vendido}</td>
                      <td>{r.merma}</td>
                      <td>
                        <span style={{
                          color: r.eficiencia_pct >= 90 ? '#27ae60' : r.eficiencia_pct >= 80 ? '#f39c12' : '#e74c3c',
                          fontWeight: 'bold',
                        }}>
                          {r.eficiencia_pct}%
                        </span>
                      </td>
                      <td>S/ {(r.perdida_economica || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p style={{ color: '#8892a4' }}>Sin datos para el período.</p>}
          </div>
        </>
      )}

      {tab === 'mermas' && analisis && (
        <>
          <div className="grid-3">
            <div className="metric">
              <div className="value" id="kpi-merma-pct">{analisis.porcentaje_merma_global || 0}%</div>
              <div className="label">% Merma Global</div>
            </div>
            <div className="metric">
              <div className="value" id="kpi-merma-uds">{analisis.total_unidades_merma || 0}</div>
              <div className="label">Unidades Perdidas</div>
            </div>
            <div className="metric">
              <div className="value" id="kpi-merma-perdida" style={{ color: (analisis.perdida_economica_total || 0) > 0 ? '#e74c3c' : undefined }}>
                S/ {(analisis.perdida_economica_total || 0).toFixed(2)}
              </div>
              <div className="label">💸 Pérdida Económica</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>Mermas por Motivo</h3>
              {analisis.por_motivo?.length > 0 ? (
                <table>
                  <thead><tr><th>Motivo</th><th>Frecuencia</th><th>Total</th><th>Pérdida S/</th></tr></thead>
                  <tbody>
                    {analisis.por_motivo.map((m, i) => (
                      <tr key={i}><td>{m.motivo}</td><td>{m.frecuencia}</td><td>{m.total_merma}</td><td>S/ {(m.perdida_economica || 0).toFixed(2)}</td></tr>
                    ))}
                  </tbody>
                </table>
              ) : <p style={{ color: '#8892a4' }}>Sin datos</p>}
            </div>
            <div className="card">
              <h3>Mermas por Producto</h3>
              {analisis.por_producto?.length > 0 ? (
                <table>
                  <thead><tr><th>Producto</th><th>Frecuencia</th><th>Total</th><th>Costo U.</th><th>Pérdida S/</th></tr></thead>
                  <tbody>
                    {analisis.por_producto.map((m, i) => (
                      <tr key={i}><td>{m.producto}</td><td>{m.frecuencia}</td><td>{m.total_merma}</td><td>S/ {(m.costo_unitario || 0).toFixed(2)}</td><td>S/ {(m.perdida_economica || 0).toFixed(2)}</td></tr>
                    ))}
                  </tbody>
                </table>
              ) : <p style={{ color: '#8892a4' }}>Sin datos</p>}
            </div>
          </div>

          <div className="card">
            <h3>Registro de Mermas</h3>
            {mermas.length > 0 ? (
              <table id="mermasTable">
                <thead><tr><th>ID</th><th>Producto</th><th>Fecha</th><th>Cantidad</th><th>Motivo</th></tr></thead>
                <tbody>
                  {mermas.slice(0, 20).map(m => (
                    <tr key={m.id}>
                      <td>{m.id}</td>
                      <td>{m.producto_nombre}</td>
                      <td>{formatDateShort(m.fecha)}</td>
                      <td>{m.cantidad_merma}</td>
                      <td>{m.motivo || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p style={{ color: '#8892a4' }}>No hay mermas registradas.</p>}
          </div>
        </>
      )}
    </>
  )
}
