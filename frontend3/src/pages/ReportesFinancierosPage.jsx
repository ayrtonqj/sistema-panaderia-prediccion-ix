import { useState, useEffect, useRef } from 'react'
import { api } from '../api/api'
import { Line, Doughnut } from 'react-chartjs-2'
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { formatDateFull, formatDateShort } from '../utils/formatters'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler)

export default function ReportesFinancierosPage() {
  const today = new Date()
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
  const todayStr = today.toISOString().split('T')[0]

  const [fechaInicio, setFechaInicio] = useState(firstDay)
  const [fechaFin, setFechaFin] = useState(todayStr)
  const [reportData, setReportData] = useState(null)
  const [ventasData, setVentasData] = useState(null)
  const [porcentajeData, setPorcentajeData] = useState([])
  const [rentabilidad, setRentabilidad] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const lineRef = useRef(null)
  const doughnutRef = useRef(null)

  const generarReporte = async () => {
    setLoading(true)
    setError('')

    try {
      const res = await api.post('/reportes/estado-resultados', {
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      })
      setReportData(res)
    } catch (e) {
      setError(`estado-resultados: ${e.message}`)
      setLoading(false)
      return
    }

    try {
      const vtas = await api.get(`/reportes/ventas-diarias?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`)
      setVentasData(vtas)
    } catch (e) {
      console.error('ventas-diarias error:', e)
    }

    try {
      const pct = await api.get(`/reportes/productos-porcentaje?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`)
      setPorcentajeData(Array.isArray(pct) ? pct : [])
    } catch (e) {
      console.error('productos-porcentaje error:', e)
    }

    try {
      const rent = await api.get('/reportes/productos-rentabilidad')
      setRentabilidad(Array.isArray(rent) ? rent.slice(0, 10) : [])
    } catch (e) {
      console.error('productos-rentabilidad error:', e)
    }

    setLoading(false)
  }

  useEffect(() => { generarReporte() }, [])

  const lineChart = ventasData && ventasData.fechas ? {
    labels: ventasData.fechas,
    datasets: [{
      label: 'Unidades Vendidas',
      data: ventasData.unidades,
      borderColor: '#667eea',
      backgroundColor: 'rgba(102,126,234,0.1)',
      fill: true,
      tension: 0.4,
    }],
  } : null

  const colors = ['#667eea', '#764ba2', '#f39c12', '#27ae60', '#e74c3c', '#3498db', '#9b59b6', '#1abc9c', '#e67e22', '#2ecc71']
  const doughnutChart = porcentajeData.length > 0 ? {
    labels: porcentajeData.map(p => p.producto),
    datasets: [{
      data: porcentajeData.map(p => p.porcentaje),
      backgroundColor: colors.slice(0, porcentajeData.length),
      borderWidth: 0,
    }],
  } : null

  const descargarPDF = () => {
    const ventasCanvas = document.getElementById('ventasChartCanvas')
    const porcentajeCanvas = document.getElementById('porcentajeChartCanvas')
    let ventasChartImg = ''
    let porcentajeChartImg = ''
    try {
      if (ventasCanvas) ventasChartImg = ventasCanvas.toDataURL('image/png')
      if (porcentajeCanvas) porcentajeChartImg = porcentajeCanvas.toDataURL('image/png')
    } catch { /* ignore */ }

    const detalleBody = document.getElementById('detalleBody')?.innerHTML || ''
    const ingresos = document.getElementById('ingresosVal')?.textContent || 'S/ 0.00'
    const costos = document.getElementById('costosVal')?.textContent || 'S/ 0.00'
    const ganancia = document.getElementById('gananciaVal')?.textContent || 'S/ 0.00'
    const margen = document.getElementById('margenVal')?.textContent || '0%'

    const w = window.open('', '_blank')
    w.document.write(`<!DOCTYPE html><html><head><title>Reporte Financiero - Panadería Victoria</title>
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      body { font-family:Arial,sans-serif; padding:20px; color:#333; }
      .header { display:flex; align-items:center; justify-content:center; gap:20px; padding:20px 0; border-bottom:3px solid #667eea; margin-bottom:20px; }
      .header h1 { margin:0; font-size:22px; color:#667eea; }
      .periodo { text-align:center; background:#f5f5f5; padding:10px; margin-bottom:20px; border-radius:5px; }
      .metrics { display:flex; justify-content:space-around; margin-bottom:20px; }
      .metric-box { text-align:center; padding:15px 30px; background:#f9f9f9; border-radius:8px; border:1px solid #ddd; }
      .metric-box .value { font-size:24px; font-weight:bold; color:#667eea; }
      .metric-box .label { font-size:12px; color:#888; }
      .charts-section { display:flex; gap:20px; margin-bottom:20px; }
      .chart-container { flex:1; text-align:center; }
      .chart-container img { max-width:100%; height:auto; }
      table { width:100%; border-collapse:collapse; margin-top:10px; }
      th,td { border:1px solid #ddd; padding:8px; text-align:left; font-size:12px; }
      th { background:#667eea; color:white; }
      .footer { margin-top:30px; text-align:center; font-size:10px; color:#888; border-top:1px solid #ddd; padding-top:10px; }
    </style></head><body>
    <div class="header"><div><h1>Reportes Financieros</h1><p>Sistema de Gestión Predictiva</p></div></div>
    <div class="periodo"><strong>Período:</strong> ${formatDateShort(fechaInicio)} al ${formatDateShort(fechaFin)}</div>
    <div class="metrics">
      <div class="metric-box"><div class="value">${ingresos}</div><div class="label">💰 Ingresos</div></div>
      <div class="metric-box"><div class="value">${costos}</div><div class="label">📦 Costos</div></div>
      <div class="metric-box"><div class="value">${ganancia}</div><div class="label">📈 Ganancia</div></div>
      <div class="metric-box"><div class="value">${margen}</div><div class="label">📊 Margen</div></div>
    </div>
    <div class="charts-section">
      <div class="chart-container"><h3>📈 Ventas Diarias</h3>${ventasChartImg ? `<img src="${ventasChartImg}" alt="Ventas">` : '<p>Sin datos</p>'}</div>
      <div class="chart-container"><h3>🍩 Distribución de Ventas</h3>${porcentajeChartImg ? `<img src="${porcentajeChartImg}" alt="Distribución">` : '<p>Sin datos</p>'}</div>
    </div>
    <h3>📋 Detalle de Ventas</h3>
    <table><thead><tr><th>Producto</th><th>Categoría</th><th>Cantidad</th><th>Precio</th><th>Ingreso</th><th>Costo</th><th>Ganancia</th></tr></thead><tbody>${detalleBody}</tbody></table>
    <div class="footer">Reporte generado: ${formatDateFull(new Date())}</div>
    </body></html>`)
    w.document.close()
    setTimeout(() => w.print(), 500)
  }

  return (
    <>
      <div className="page-header">
        <h1>💰 Reportes Financieros</h1>
        <p style={{ color: '#8892a4' }}>Analiza la rentabilidad de tu negocio</p>
      </div>

      <div className="card no-print">
        <h3>📅 Selección de Período</h3>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ color: '#4a5568', fontSize: '13px', fontWeight: 600, marginBottom: '8px', display: 'block' }}>Fecha Inicio</label>
            <div className="date-input-wrapper">
              <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} />
            </div>
          </div>
          <div className="date-separator">—</div>
          <div>
            <label style={{ color: '#4a5568', fontSize: '13px', fontWeight: 600, marginBottom: '8px', display: 'block' }}>Fecha Fin</label>
            <div className="date-input-wrapper">
              <input type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)} />
            </div>
          </div>
          <button className="btn" onClick={generarReporte}>📊 Generar Reporte</button>
          {reportData && <button className="btn" onClick={descargarPDF}>📄 Descargar PDF</button>}
        </div>
      </div>

      {loading && (
        <div className="card">
          <p style={{ color: '#667eea', textAlign: 'center', padding: '40px' }}>
            ⏳ Generando reporte...
          </p>
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          ⚠️ {error}
          <br />
          <small>Verifica que el backend esté corriendo en http://localhost:8000</small>
        </div>
      )}

      {reportData && !loading && (
        <>
          <div className="grid-4">
            <div className="metric">
              <div className="value" id="ingresosVal">S/ {(reportData.ingresos || 0).toFixed(2)}</div>
              <div className="label">💰 Ingresos</div>
            </div>
            <div className="metric">
              <div className="value" id="costosVal">S/ {(reportData.costos || 0).toFixed(2)}</div>
              <div className="label">📦 Costos</div>
            </div>
            <div className="metric">
              <div className="value" id="gananciaVal" style={{ color: (reportData.ganancia_neta || 0) >= 0 ? '#27ae60' : '#e74c3c' }}>
                S/ {(reportData.ganancia_neta || 0).toFixed(2)}
              </div>
              <div className="label">📈 Ganancia Neta</div>
            </div>
            <div className="metric">
              <div className="value" id="margenVal">{(reportData.margen_porcentaje || 0).toFixed(1)}%</div>
              <div className="label">📊 Margen</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>📈 Ventas Diarias</h3>
              <div style={{ height: '250px' }}>
                {lineChart ? (
                  <Line ref={lineRef} id="ventasChartCanvas" data={lineChart} options={{
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                      y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#4a5568' } },
                      x: { grid: { display: false }, ticks: { color: '#4a5568' } },
                    },
                  }} />
                ) : <p style={{ color: '#8892a4' }}>Sin datos</p>}
              </div>
            </div>
            <div className="card">
              <h3>🍩 Distribución de Ventas (%)</h3>
              <div style={{ height: '250px' }}>
                {doughnutChart ? (
                  <Doughnut ref={doughnutRef} id="porcentajeChartCanvas" data={doughnutChart} options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'right' } },
                  }} />
                ) : <p style={{ color: '#8892a4' }}>Sin datos</p>}
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>🏆 Top Productos por Rentabilidad</h3>
              <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Producto</th><th>Vendidos</th><th>Ganancia</th><th>Margen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rentabilidad.map((p, i) => (
                      <tr key={i}>
                        <td>{p.producto}</td>
                        <td>{p.unidades_vendidas}</td>
                        <td style={{ color: (p.ganancia || 0) >= 0 ? '#27ae60' : '#e74c3c' }}>
                          S/ {(p.ganancia || 0).toFixed(2)}
                        </td>
                        <td>{(p.margen || 0).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card">
              <h3>📊 Top Productos Vendidos</h3>
              <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                <table>
                  <thead><tr><th>Producto</th><th>Unidades</th><th>% Ventas</th></tr></thead>
                  <tbody>
                    {porcentajeData.map((p, i) => (
                      <tr key={i}>
                        <td>{p.producto}</td>
                        <td>{p.unidades}</td>
                        <td>{p.porcentaje}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>📋 Estado de Resultados (Detalle)</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Producto</th><th>Categoría</th><th>Cantidad</th>
                    <th>Precio</th><th>Ingreso</th><th>Costo</th><th>Ganancia</th>
                  </tr>
                </thead>
                <tbody id="detalleBody">
                  {reportData.detalle && reportData.detalle.map((d, i) => (
                    <tr key={i}>
                      <td>{d.producto}</td>
                      <td>{d.categoria || '-'}</td>
                      <td>{typeof d.cantidad === 'number' ? d.cantidad.toFixed(1) : d.cantidad}</td>
                      <td>S/ {d.precio}</td>
                      <td>S/ {(d.ingreso || 0).toFixed(2)}</td>
                      <td>S/ {(d.costo || 0).toFixed(2)}</td>
                      <td style={{ color: (d.ganancia || 0) >= 0 ? '#27ae60' : '#e74c3c' }}>
                        S/ {(d.ganancia || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !reportData && !error && (
        <div className="alert alert-info">
          ℹ️ No hay datos financieros para el período seleccionado. Prueba con otro rango de fechas.
        </div>
      )}
    </>
  )
}
