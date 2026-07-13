import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'
import { openPrintWindow, tableHeaderHtml, descargarExcel, enviarPorCorreo } from '../utils/pdf'
import { formatDateShort } from '../utils/formatters'
import { useNav } from '../context/NavContext'

export default function RegistroDiarioPage() {
  const [productos, setProductos] = useState([])
  const [produccion, setProduccion] = useState([])
  const [ventasHoy, setVentasHoy] = useState(null)
  const [loading, setLoading] = useState(true)

  const [form, setForm] = useState({
    producto_id: '',
    fecha: new Date().toISOString().split('T')[0],
    cantidad_producida: '',
  })
  const [result, setResult] = useState('')
  const [sugerencias, setSugerencias] = useState([])
  const [sinPredicciones, setSinPredicciones] = useState(false)
  const [produccionHoy, setProduccionHoy] = useState([])
  const navigate = useNav()
  const [tab, setTab] = useState('registrar')
  const [tabSec, setTabSec] = useState('sugerencias')
  const [loadingPendientes, setLoadingPendientes] = useState(false)
  const [pendientesValores, setPendientesValores] = useState({})
  const [toast, setToast] = useState(null)
  const [panPasadoItems, setPanPasadoItems] = useState([])
  const [ppLoading, setPpLoading] = useState(false)

  const cargarDatos = async () => {
    try {
      const [prods, prodRegs, ventas, sug, prodHoy] = await Promise.all([
        api.get('/productos/'),
        api.get('/produccion/'),
        api.get('/ventas/hoy'),
        api.get('/produccion/sugerida').catch(() => []),
        api.get('/produccion/hoy'),
      ])
      setProductos(Array.isArray(prods) ? prods : [])
      setProduccion(Array.isArray(prodRegs) ? prodRegs : [])
      setVentasHoy(ventas)
      if (Array.isArray(sug)) {
        setSugerencias(sug)
        setSinPredicciones(sug.length === 0)
      } else {
        setSugerencias([])
        setSinPredicciones(true)
      }
      setProduccionHoy(Array.isArray(prodHoy) ? prodHoy : [])
    } catch {
      setResult('⚠️ Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargarDatos() }, [])
  useEffect(() => { if (!toast) return; const id = setTimeout(() => setToast(null), 3000); return () => clearTimeout(id) }, [toast])

  const cargarPanPasado = async () => {
    setPpLoading(true)
    try {
      await api.post('/pan-pasado/auto-generar?dias=3', {}).catch(() => {})
      const pp = await api.get('/pan-pasado/disponible').catch(() => [])
      setPanPasadoItems(Array.isArray(pp) ? pp : [])
    } catch {} finally { setPpLoading(false) }
  }

  const venderPanPasado = async (ppId, cantidad) => {
    try {
      const data = await api.post(`/pan-pasado/${ppId}/vender`, { cantidad_vender: cantidad })
      setToast({ tipo: 'ok', msg: `✅ ${data.mensaje} — S/ ${data.total_soles.toFixed(2)}` })
      cargarPanPasado()
    } catch { setToast({ tipo: 'error', msg: '❌ Error al vender pan' }) }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setResult('⏳ Guardando...')
    try {
      const res = await api.post('/produccion/', {
        producto_id: parseInt(form.producto_id),
        fecha: form.fecha,
        cantidad_producida: parseFloat(form.cantidad_producida),
      })
      let msg = `✅ Producción registrada: ${res.cantidad_producida} unidades`
      if (res.merma_auto_generada) {
        msg += `<br>⚠️ Merma automática: ${res.merma_auto_generada}`
      }
      setResult(msg)
      setForm(f => ({ ...f, producto_id: '', cantidad_producida: '' }))
      const [prodRegs, ventas] = await Promise.all([
        api.get('/produccion/'),
        api.get('/ventas/hoy'),
      ])
      setProduccion(Array.isArray(prodRegs) ? prodRegs : [])
      setVentasHoy(ventas)
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (detail?.insumos_faltantes) {
        setToast({ tipo: 'error', msg: `❌ Stock insuficiente. Generando órdenes sugeridas...` })
        api.post('/ordenes-compra/sugerir-urgente', detail.insumos_faltantes).catch(() => {})
        setTimeout(() => navigate('ordenes_compra'), 2500)
      } else {
        setResult('❌ Error al registrar producción')
      }
    }
  }

  const usarSugerencia = (s) => {
    setForm(f => ({
      ...f,
      producto_id: String(s.producto_id),
      cantidad_producida: String(s.produccion_sugerida),
    }))
    document.querySelector('.form-card')?.scrollIntoView({ behavior: 'smooth' })
  }

  const registrarPendientes = async () => {
    const entries = Object.entries(pendientesValores).filter(([_, v]) => v && parseFloat(v) > 0)
    if (entries.length === 0) return
    setLoadingPendientes(true)
    setToast({ tipo: 'ok', msg: `⏳ Registrando ${entries.length} producción(es)...` })
    const results = await Promise.allSettled(
      entries.map(([id, cantidad]) =>
        api.post('/produccion/', {
          producto_id: Number(id),
          fecha: new Date().toISOString().split('T')[0],
          cantidad_producida: parseFloat(cantidad),
        })
      )
    )
    const insumosFaltantes = []
    let successCount = 0
    for (const r of results) {
      if (r.status === 'fulfilled') {
        successCount++
      } else if (r.reason?.response?.data?.detail?.insumos_faltantes) {
        for (const ins of r.reason.response.data.detail.insumos_faltantes) {
          const dup = insumosFaltantes.find(i => i.insumo === ins.insumo)
          if (dup) {
            dup.necesario += ins.necesario
            dup.faltante += ins.faltante
          } else {
            insumosFaltantes.push({ ...ins })
          }
        }
      }
    }
    if (insumosFaltantes.length > 0) {
      const lista = insumosFaltantes.map(i => `${i.insumo} (falta ${i.faltante} ${i.unidad})`).join(', ')
      setToast({ tipo: 'error', msg: `❌ Stock insuficiente: ${lista}. Generando órdenes sugeridas...` })
      await api.post('/ordenes-compra/sugerir-urgente', insumosFaltantes).catch(() => {})
      setTimeout(() => navigate('ordenes_compra'), 2500)
    } else {
      setToast({ tipo: 'ok', msg: `✅ ${successCount} producción(es) registrada(s)` })
    }
    const [prodRegs, prodHoy] = await Promise.all([
      api.get('/produccion/'),
      api.get('/produccion/hoy'),
    ])
    setProduccion(Array.isArray(prodRegs) ? prodRegs : [])
    setProduccionHoy(Array.isArray(prodHoy) ? prodHoy : [])
    setPendientesValores({})
    setLoadingPendientes(false)
  }

  const generarPDF = () => {
    const tbody = produccion.map(r => `
      <tr>
        <td>${r.id}</td>
        <td>${r.producto_nombre}</td>
        <td>${formatDateShort(r.fecha)}</td>
        <td>${r.cantidad_producida}</td>
      </tr>
    `).join('')
    openPrintWindow('Registro de Producción - Panadería Victoria',
      tableHeaderHtml('Registro Diario de Producción') +
      '<table><thead><tr><th>ID</th><th>Producto</th><th>Fecha</th><th>Producido</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
    )
  }

  if (loading) return <div className="card"><p>Cargando...</p></div>

  const sugerenciaMap = {}
  sugerencias.forEach(s => { sugerenciaMap[s.producto_id] = s.produccion_sugerida })
  const pendientes = produccionHoy.filter(p => p.producido_hoy === 0)

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}><div>
          <h1>📝 Registro Diario de Producción</h1><p style={{ color: '#8892a4' }}>Registra la cantidad producida del día</p>
        </div><div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
        <button className="btn btn-danger" onClick={generarPDF} style={{ fontSize: '11px', padding: '3px 8px', flexShrink: 0 }}>📄 PDF</button>
        <button className="btn" onClick={() => enviarPorCorreo('Registro Diario de Producción', ['ID', 'Producto', 'Fecha', 'Producido'], (produccion || []).map(r => [r.id, r.producto_nombre, r.fecha, r.cantidad_producida]))} style={{ fontSize: '11px', padding: '3px 8px', background: '#e74c3c', color: '#fff', flexShrink: 0 }}>📧 Enviar</button>
        <button className="btn" onClick={() => descargarExcel('Produccion', [{ key: "id", label: "ID" }, { key: "producto_nombre", label: "Producto" }, { key: "fecha", label: "Fecha", render: (i) => formatDateShort(i.fecha) }, { key: "cantidad_producida", label: "Producido" }], produccion)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', flexShrink: 0 }}>📊 Excel</button>
        </div>
</div>

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button onClick={() => setTab('registrar')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'registrar' ? '700' : '400',
            background: tab === 'registrar' ? '#667eea' : 'transparent',
            color: tab === 'registrar' ? '#fff' : '#4a5568', transition: 'all 0.2s',
          }}>📝 Registrar Nueva Producción</button>
          <button onClick={() => setTab('pendientes')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'pendientes' ? '700' : '400',
            background: tab === 'pendientes' ? '#667eea' : 'transparent',
            color: tab === 'pendientes' ? '#fff' : '#4a5568', transition: 'all 0.2s',
          }}>🚨 Productos Pendientes{pendientes.length > 0 ? ` (${pendientes.length})` : ''}</button>
        </div>
      </div>

      {tab === 'registrar' && (
        <div className="card form-card">
          <h3>📝 Registrar Nueva Producción</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
              <select value={form.producto_id} onChange={e => setForm(f => ({ ...f, producto_id: e.target.value }))} required>
                <option value="">Seleccionar producto</option>
                {productos.map(p => (
                  <option key={p.id} value={p.id}>{p.nombre} ({p.categoria})</option>
                ))}
              </select>
              <input type="date" value={form.fecha} onChange={e => setForm(f => ({ ...f, fecha: e.target.value }))} required />
              <input type="number" placeholder="Cantidad Producida" step="0.01" min="0" required
                value={form.cantidad_producida} onChange={e => setForm(f => ({ ...f, cantidad_producida: e.target.value }))} />
              <button type="submit" className="btn">Registrar Producción</button>
            </div>
          </form>
          {result && <div style={{ marginTop: '15px' }} dangerouslySetInnerHTML={{ __html: result }} />}
        </div>
      )}

      {tab === 'pendientes' && (
        <div className="card">
          <h3>🚨 Productos Pendientes de Producción</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <div style={{ fontSize: '14px', color: '#8892a4' }}>
              {produccionHoy.filter(p => p.producido_hoy > 0).length} de {produccionHoy.length} productos producidos hoy
            </div>
            <div style={{
              padding: '4px 12px', borderRadius: '12px', fontSize: '13px', fontWeight: 600,
              background: pendientes.length === 0 ? '#27ae6020' : '#e74c3c20',
              color: pendientes.length === 0 ? '#27ae60' : '#e74c3c',
            }}>
              {pendientes.length === 0
                ? '✅ Todos los productos tienen producción hoy'
                : `⚠️ ${pendientes.length} productos pendientes`}
            </div>
          </div>
          {pendientes.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <p style={{ color: '#27ae60', fontWeight: 600, fontSize: '15px' }}>✅ Todos los productos tienen producción registrada hoy.</p>
            </div>
          ) : (
            <div>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontSize: '12px', color: '#8892a4', fontWeight: 600 }}>Producto</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontSize: '12px', color: '#8892a4', fontWeight: 600 }}>Categoría</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', fontSize: '12px', color: '#8892a4', fontWeight: 600 }}>✨ Sugerido</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', fontSize: '12px', color: '#8892a4', fontWeight: 600 }}>Cantidad</th>
                  </tr>
                </thead>
                <tbody>
                  {pendientes.map(p => (
                    <tr key={p.producto_id} style={{ borderBottom: '1px solid #e2e8f040' }}>
                      <td style={{ padding: '5px 8px', fontSize: '13px', fontWeight: 500 }}>{p.producto_nombre}</td>
                      <td style={{ padding: '5px 8px', fontSize: '12px', color: '#8892a4' }}>{p.categoria}</td>
                      <td style={{ padding: '5px 8px', textAlign: 'center', fontSize: '13px', fontWeight: 600, color: sugerenciaMap[p.producto_id] !== undefined ? '#667eea' : '#ccc' }}>
                        {sugerenciaMap[p.producto_id] !== undefined ? sugerenciaMap[p.producto_id] : '—'}
                      </td>
                      <td style={{ padding: '5px 8px', textAlign: 'center' }}>
                        <input type="number" placeholder="0" min="0" step="0.01"
                          value={pendientesValores[p.producto_id] || ''}
                          onChange={e => setPendientesValores(v => ({ ...v, [p.producto_id]: e.target.value }))}
                          style={{ width: '80px', padding: '5px 8px', border: '1px solid #e2e8f0', borderRadius: '4px', fontSize: '13px', textAlign: 'center' }} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '12px' }}>
                <button className="btn" style={{ padding: '8px 18px', fontSize: '14px' }}
                  onClick={() => {
                    const vals = {}
                    pendientes.forEach(p => {
                      if (sugerenciaMap[p.producto_id] !== undefined) vals[p.producto_id] = String(sugerenciaMap[p.producto_id])
                    })
                    setPendientesValores(vals)
                  }}>
                  ✨ Usar Sugeridos
                </button>
                <button className="btn"
                  onClick={registrarPendientes}
                  disabled={loadingPendientes || !Object.values(pendientesValores).some(v => v && parseFloat(v) > 0)}
                  style={{ padding: '8px 18px', fontSize: '14px' }}>
                  {loadingPendientes ? '⏳ Registrando...' : '🚀 Registrar Todo'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px', marginTop: '10px' }}>
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button onClick={() => setTabSec('sugerencias')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tabSec === 'sugerencias' ? '700' : '400',
            background: tabSec === 'sugerencias' ? '#667eea' : 'transparent',
            color: tabSec === 'sugerencias' ? '#fff' : '#4a5568', transition: 'all 0.2s',
          }}>✨ Sugerencias del Modelo</button>
          <button onClick={() => setTabSec('historial')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tabSec === 'historial' ? '700' : '400',
            background: tabSec === 'historial' ? '#667eea' : 'transparent',
            color: tabSec === 'historial' ? '#fff' : '#4a5568', transition: 'all 0.2s',
          }}>📋 Historial de Producción</button>
          <button onClick={() => { setTabSec('pan_pasado'); cargarPanPasado() }} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tabSec === 'pan_pasado' ? '700' : '400',
            background: tabSec === 'pan_pasado' ? '#667eea' : 'transparent',
            color: tabSec === 'pan_pasado' ? '#fff' : '#4a5568', transition: 'all 0.2s',
          }}>🥖 Pan del Día Anterior</button>
        </div>
      </div>

      {tabSec === 'sugerencias' && (
        <>
          {!sinPredicciones && sugerencias.length > 0 ? (
            <div className="card">
              <h3>✨ Producción Sugerida (basada en ML + merma histórica)</h3>
              <table>
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>📊 Demanda</th>
                    <th>✅ Vendido</th>
                    <th>🏭 Producido</th>
                    <th>⚠️ % Merma Hist.</th>
                    <th>✨ Sugerido</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {sugerencias.map(s => (
                    <tr key={s.producto_id}>
                      <td>{s.producto_nombre}</td>
                      <td>{s.demanda_estimada}</td>
                      <td>{s.vendido_hoy}</td>
                      <td>{s.producido_hoy}</td>
                      <td>{s.tasa_merma_historica_pct}%</td>
                      <td><strong>{s.produccion_sugerida}</strong></td>
                      <td>
                        <button className="btn-action" onClick={() => usarSugerencia(s)} title="Usar esta cantidad">
                          ➕ Usar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '30px' }}>
              <p style={{ color: '#8892a4' }}>🔮 No hay predicciones para hoy. Ve a <strong>Predicciones</strong> y genera las predicciones primero.</p>
            </div>
          )}
        </>
      )}

      {tabSec === 'historial' && (
        <div className="card">
          <h3>📋 Producción Reciente</h3>
          <div id="produccionTable">
            <Pagination
              data={produccion}
              pageSize={20}
              columns={['ID', 'Producto', 'Fecha', 'Producido']}
              renderRow={(r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.producto_nombre}</td>
                  <td>{formatDateShort(r.fecha)}</td>
                  <td>{r.cantidad_producida}</td>
                </tr>
              )}
            />
          </div>
        </div>
      )}

      {tabSec === 'pan_pasado' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0 }}>🥖 Pan del Día Anterior</h3>
            <button className="btn" style={{ fontSize: '12px', padding: '6px 14px' }} onClick={cargarPanPasado}>🔄 Actualizar</button>
          </div>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '15px' }}>
            Pan no vendido recuperado automáticamente al registrar producción. Se vende a <strong>costo × 1.10</strong> (10% ganancia). El pan que pasa más de 7 días se convierte en merma.
          </p>
          {ppLoading ? (
            <p style={{ color: '#8892a4' }}>Cargando...</p>
          ) : panPasadoItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '20px', color: '#8892a4' }}>
              <p>🥖 No hay pan recuperado disponible en este momento.</p>
              <p style={{ fontSize: '13px' }}>Al registrar producción de panes, el excedente aparece aquí automáticamente.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {panPasadoItems.map(pp => {
                const disp = pp.cantidad - (pp.cantidad_vendida || 0)
                return (
                  <div key={pp.id} style={{
                    display: 'flex', alignItems: 'center', gap: '12px',
                    padding: '10px 14px', borderRadius: '8px',
                    border: '1px solid var(--border-color)', background: 'var(--bg-card)',
                  }}>
                    <span style={{ fontSize: '24px' }}>🥖</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>{pp.producto_nombre}</div>
                      <div style={{ fontSize: '12px', color: '#8892a4' }}>
                        {disp} disponibles · S/ {pp.precio_unitario.toFixed(2)} c/u
                      </div>
                    </div>
                    <div style={{ fontWeight: 700, fontSize: '16px', color: '#e67e22', minWidth: '70px', textAlign: 'right' }}>
                      S/ {(disp * pp.precio_unitario).toFixed(2)}
                    </div>
                    <button className="btn" style={{ padding: '6px 14px', fontSize: '12px', background: '#e67e22', color: '#fff' }}
                      onClick={() => venderPanPasado(pp.id, disp)}>Vender {disp} uds</button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {toast && <div className={`toast ${toast.tipo}`}>{toast.msg}</div>}
    </>
  )
}
