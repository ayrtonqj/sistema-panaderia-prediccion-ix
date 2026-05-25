import { useState, useEffect } from 'react'
import { api } from '../api/api'
import { openPrintWindow, tableHeaderHtml } from '../utils/pdf'
import { formatDateShort } from '../utils/formatters'

export default function OrdenesCompraPage() {
  const [ordenes, setOrdenes] = useState([])
  const [proveedores, setProveedores] = useState([])
  const [insumos, setInsumos] = useState([])
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState('')
  const [tab, setTab] = useState('historial')
  const [editCantidad, setEditCantidad] = useState({})
  const [showProvForm, setShowProvForm] = useState(false)
  const [provForm, setProvForm] = useState({ nombre: '', contacto: '', telefono: '', direccion: '' })
  const [provResult, setProvResult] = useState('')

  const [form, setForm] = useState({
    proveedor_id: '',
    insumo_id: '',
    fecha_orden: new Date().toISOString().split('T')[0],
    cantidad: '',
    precio_unitario: '',
  })

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/ordenes-compra/'),
      api.get('/proveedores/'),
      api.get('/insumos/'),
    ]).then(([ords, provs, ins]) => {
      setOrdenes(Array.isArray(ords) ? ords : [])
      setProveedores(Array.isArray(provs) ? provs : [])
      setInsumos(Array.isArray(ins) ? ins : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const sugeridas = ordenes.filter(o => o.es_sugerida && o.estado === 'pendiente')
  const otras = ordenes.filter(o => !o.es_sugerida || o.estado !== 'pendiente')
  const pendientes = ordenes.filter(o => o.estado === 'pendiente')
  const completadas = ordenes.filter(o => o.estado !== 'pendiente').sort((a, b) => new Date(b.fecha_orden) - new Date(a.fecha_orden))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      proveedor_id: parseInt(form.proveedor_id),
      insumo_id: parseInt(form.insumo_id),
      fecha_orden: form.fecha_orden,
      cantidad: parseFloat(form.cantidad),
    }
    if (form.precio_unitario) payload.precio_unitario = parseFloat(form.precio_unitario)
    try {
      await api.post('/ordenes-compra/', payload)
      setResult('✅ Orden creada correctamente')
      setForm(f => ({ ...f, cantidad: '', precio_unitario: '' }))
      setTimeout(() => setResult(''), 2000)
      fetchData()
    } catch {
      setResult('⚠️ Error de conexión')
    }
  }

  const handleCrearProveedor = async (e) => {
    e.preventDefault()
    try {
      await api.post('/proveedores/', {
        nombre: provForm.nombre,
        contacto: provForm.contacto,
        telefono: provForm.telefono,
        direccion: provForm.direccion,
      })
      setProvResult('✅ Proveedor creado correctamente')
      setProvForm({ nombre: '', contacto: '', telefono: '', direccion: '' })
      setTimeout(() => {
        setProvResult('')
        setShowProvForm(false)
        api.get('/proveedores/').then(provs => setProveedores(Array.isArray(provs) ? provs : []))
      }, 1500)
    } catch {
      setProvResult('⚠️ Error de conexión')
    }
  }

  const sugerirAhora = async () => {
    setResult('⏳ Calculando...')
    try {
      const data = await api.post('/ordenes-compra/sugerir')
      setResult(`✅ ${data.mensaje}`)
      setTimeout(() => setResult(''), 2000)
      fetchData()
    } catch {
      setResult('⚠️ Error al generar sugerencias')
    }
  }

  const confirmarOrden = async (ordenId) => {
    if (!confirm('¿Confirmar esta orden sugerida?')) return
    try {
      const data = await api.post(`/ordenes-compra/${ordenId}/confirmar`)
      setResult(`✅ ${data.mensaje}`)
      setTimeout(() => setResult(''), 2000)
      fetchData()
    } catch {
      setResult('⚠️ Error al confirmar')
    }
  }

  const cancelarOrden = async (ordenId) => {
    if (!confirm('¿Cancelar esta orden?')) return
    try {
      const data = await api.post(`/ordenes-compra/${ordenId}/cancelar`)
      setResult(`✅ ${data.mensaje}`)
      setTimeout(() => setResult(''), 2000)
      fetchData()
    } catch {
      setResult('⚠️ Error al cancelar')
    }
  }

  const confirmarTodas = async () => {
    if (!confirm(`¿Procesar las ${pendientes.length} órdenes pendientes?`)) return
    setResult(`⏳ Procesando ${pendientes.length} órdenes...`)
    const results = await Promise.allSettled(
      pendientes.map(o =>
        api.post(o.es_sugerida ? `/ordenes-compra/${o.id}/confirmar` : `/ordenes-compra/${o.id}/recibir`)
      )
    )
    const count = results.filter(r => r.status === 'fulfilled').length
    setResult(`✅ ${count} de ${pendientes.length} órdenes procesadas`)
    setTimeout(() => setResult(''), 3000)
    fetchData()
  }

  const generarPDF = () => {
    const tbody = [...ordenes].sort((a, b) => new Date(b.fecha_orden) - new Date(a.fecha_orden)).map(o => `
      <tr>
        <td>${o.id}</td>
        <td>${o.proveedor_nombre}</td>
        <td>${o.insumo_nombre}</td>
        <td>${formatDateShort(o.fecha_orden)}</td>
        <td>${o.cantidad}</td>
        <td>${o.precio_unitario ? `S/ ${o.precio_unitario}` : '-'}</td>
        <td>${(o.estado || '').toUpperCase()}</td>
      </tr>
    `).join('')
    openPrintWindow('Órdenes de Compra - Panadería Victoria',
      tableHeaderHtml('Órdenes de Compra') +
      '<table><thead><tr><th>ID</th><th>Proveedor</th><th>Insumo</th><th>Fecha</th><th>Cantidad</th><th>Precio</th><th>Estado</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
    )
  }

  const guardarCantidadEditada = async (ordenId) => {
    const nuevaCantidad = editCantidad[ordenId]
    if (!nuevaCantidad || parseFloat(nuevaCantidad) <= 0) return
    try {
      await api.put(`/ordenes-compra/${ordenId}`, { cantidad: parseFloat(nuevaCantidad) })
      setResult('✅ Cantidad actualizada')
      setTimeout(() => setResult(''), 2000)
      setEditCantidad(e => ({ ...e, [ordenId]: undefined }))
      fetchData()
    } catch {
      setResult('⚠️ Error al actualizar')
    }
  }

  const recibirOrden = async (ordenId) => {
    if (!confirm('¿Confirmas que has recibido este pedido?')) return
    setResult('⏳ Procesando...')
    try {
      const data = await api.post(`/ordenes-compra/${ordenId}/recibir`)
      if (data.error) {
        setResult(`⚠️ ${data.error}`)
      } else {
        setResult(`✅ ${data.mensaje}. Stock de ${data.insumo}: ${data.stock_anterior} → ${data.stock_nuevo}`)
        setTimeout(() => { setResult(''); fetchData() }, 2000)
      }
    } catch {
      setResult('⚠️ Error de conexión')
    }
  }

  const estadoColor = (estado) => {
    if (estado === 'pendiente') return '#e74c3c'
    if (estado === 'confirmado') return '#f39c12'
    if (estado === 'recibido') return '#27ae60'
    return '#8892a4'
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>🛒 Órdenes de Compra</h1>
          <p style={{ color: '#8892a4' }}>Gestiona tus compras de insumos</p>
        </div>
        <button className="btn btn-danger" onClick={generarPDF}>📄 Descargar PDF</button>
      </div>

      {result && (
        <div className="card" style={{ padding: '10px 18px', marginBottom: '15px', borderLeft: `4px solid ${result.includes('✅') ? '#27ae60' : result.includes('⚠️') ? '#e74c3c' : '#f39c12'}`, color: result.includes('✅') ? '#27ae60' : result.includes('⚠️') ? '#e74c3c' : '#667eea', fontWeight: 600, fontSize: '14px' }}>
          {result}
        </div>
      )}

      <div className="card">
        <h3>➕ Nueva Orden de Compra Manual</h3>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
            <select value={form.proveedor_id} onChange={e => setForm(f => ({ ...f, proveedor_id: e.target.value }))} required
              style={{ flex: 1 }}>
              <option value="">Seleccionar proveedor</option>
              {proveedores.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
            <button type="button" className="btn" style={{ padding: '6px 10px', fontSize: '12px', whiteSpace: 'nowrap' }}
              onClick={() => setShowProvForm(!showProvForm)}>+ Prov</button>
          </div>
          <select value={form.insumo_id} onChange={e => setForm(f => ({ ...f, insumo_id: e.target.value }))} required>
            <option value="">Seleccionar insumo</option>
            {insumos.map(i => <option key={i.id} value={i.id}>{i.nombre}</option>)}
          </select>
          <input type="date" value={form.fecha_orden} onChange={e => setForm(f => ({ ...f, fecha_orden: e.target.value }))} required />
          <input type="number" placeholder="Cantidad" step="0.01" required
            value={form.cantidad} onChange={e => setForm(f => ({ ...f, cantidad: e.target.value }))} />
          <input type="number" placeholder="Precio unitario" step="0.01"
            value={form.precio_unitario} onChange={e => setForm(f => ({ ...f, precio_unitario: e.target.value }))} />
          <button type="submit" className="btn" style={{ gridColumn: 'span 2' }}>Crear Orden</button>
        </form>

        {showProvForm && (
          <div style={{ marginTop: '15px', padding: '15px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#f8fafc' }}>
            <h4 style={{ marginBottom: '10px' }}>Nuevo Proveedor</h4>
            <form onSubmit={handleCrearProveedor} style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              <input type="text" placeholder="Nombre del proveedor" required
                value={provForm.nombre} onChange={e => setProvForm(f => ({ ...f, nombre: e.target.value }))} />
              <input type="text" placeholder="Contacto"
                value={provForm.contacto} onChange={e => setProvForm(f => ({ ...f, contacto: e.target.value }))} />
              <input type="text" placeholder="Teléfono"
                value={provForm.telefono} onChange={e => setProvForm(f => ({ ...f, telefono: e.target.value }))} />
              <input type="text" placeholder="Dirección"
                value={provForm.direccion} onChange={e => setProvForm(f => ({ ...f, direccion: e.target.value }))} />
              <button type="submit" className="btn" style={{ gridColumn: 'span 2' }}>Crear Proveedor</button>
              <button type="button" className="btn" style={{ gridColumn: 'span 2', background: '#95a5a6' }}
                onClick={() => { setShowProvForm(false); setProvResult('') }}>Cancelar</button>
            </form>
            {provResult && <p style={{ marginTop: '10px', color: provResult.includes('✅') ? '#27ae60' : '#e74c3c' }}>{provResult}</p>}
          </div>
        )}
      </div>

      <div className="card" style={{ padding: '8px 15px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button onClick={() => setTab('historial')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'historial' ? '700' : '400',
            background: tab === 'historial' ? '#667eea' : 'transparent',
            color: tab === 'historial' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>📋 Pendientes {pendientes.length > 0 && `(${pendientes.length})`}</button>
          <button onClick={() => setTab('sugerencias')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'sugerencias' ? '700' : '400',
            background: tab === 'sugerencias' ? '#667eea' : 'transparent',
            color: tab === 'sugerencias' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>📋 Órdenes Sugeridas {sugeridas.length > 0 && `(${sugeridas.length})`}</button>
          <button onClick={() => setTab('completadas')} style={{
            padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: tab === 'completadas' ? '700' : '400',
            background: tab === 'completadas' ? '#667eea' : 'transparent',
            color: tab === 'completadas' ? '#fff' : '#4a5568',
            transition: 'all 0.2s',
          }}>📦 Historial Órdenes</button>
        </div>
      </div>

      {tab === 'sugerencias' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3>📋 Órdenes Sugeridas</h3>
            <button className="btn" onClick={sugerirAhora}>🔄 Ejecutar Sugerencia</button>
          </div>
          <p style={{ color: '#8892a4', fontSize: '13px', marginBottom: '15px' }}>
            El sistema analiza insumos con stock &lt; mínimo, calcula la necesidad según predicciones ML y sugiere órdenes de compra. Revísalas antes de confirmar.
          </p>
          {loading ? <p>Cargando...</p> : sugeridas.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Insumo</th><th>Proveedor</th><th>Cantidad</th><th>Fecha Nec.</th><th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {sugeridas.map(o => (
                  <tr key={o.id} style={{ background: '#fff8e1' }}>
                    <td><strong>{o.insumo_nombre}</strong></td>
                    <td>{o.proveedor_nombre}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                        {editCantidad[o.id] !== undefined ? (
                          <>
                            <input type="number" value={editCantidad[o.id]} step="0.01" min="0"
                              onChange={e => setEditCantidad(c => ({ ...c, [o.id]: e.target.value }))}
                              style={{ width: '80px', padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: '4px' }} />
                            <button className="btn" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => guardarCantidadEditada(o.id)}>💾</button>
                            <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', background: '#95a5a6' }} onClick={() => setEditCantidad(c => ({ ...c, [o.id]: undefined }))}>✕</button>
                          </>
                        ) : (
                          <>
                            {o.cantidad}
                            {o.cantidad_sugerida_original && o.cantidad !== o.cantidad_sugerida_original && (
                              <span style={{ fontSize: '11px', color: '#f39c12' }}> (editado)</span>
                            )}
                            <button className="btn" style={{ padding: '2px 6px', fontSize: '10px', marginLeft: '5px' }}
                              onClick={() => setEditCantidad(c => ({ ...c, [o.id]: String(o.cantidad) }))}>✏️</button>
                          </>
                        )}
                      </div>
                    </td>
                    <td>{o.fecha_necesaria ? formatDateShort(o.fecha_necesaria) : '-'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#27ae60', color: '#fff' }}
                          onClick={() => confirmarOrden(o.id)}>✅ Confirmar</button>
                        <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#e74c3c', color: '#fff' }}
                          onClick={() => cancelarOrden(o.id)}>🛑 Cancelar</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '30px', background: 'transparent', border: 'none', boxShadow: 'none' }}>
              <p style={{ color: '#8892a4' }}>✅ No hay órdenes sugeridas pendientes. Todos los insumos están en nivel adecuado o ya tienen órdenes pendientes.</p>
            </div>
          )}
        </div>
      )}

      {tab === 'historial' && (
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>📋 Órdenes Pendientes</h3>
          {pendientes.length > 0 ? (
            <>
              <div style={{ background: '#27ae6015', border: '1px solid #27ae6040', borderRadius: '8px', padding: '12px 16px', marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '14px', color: '#27ae60', fontWeight: 600 }}>{pendientes.length} orden(es) pendiente(s) por procesar</span>
                <button className="btn" style={{ background: '#27ae60', color: '#fff', padding: '8px 20px' }} onClick={confirmarTodas}>✅ Aceptar Todas</button>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th><th>Proveedor</th><th>Insumo</th><th>Fecha</th>
                    <th>Cantidad</th><th>Precio</th><th>Estado</th><th>Origen</th><th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {pendientes.map(o => (
                    <tr key={o.id}>
                      <td>{o.id}</td>
                      <td>{o.proveedor_nombre}</td>
                      <td>{o.insumo_nombre}</td>
                      <td>{formatDateShort(o.fecha_orden)}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                          {editCantidad[o.id] !== undefined ? (
                            <>
                              <input type="number" value={editCantidad[o.id]} step="0.01" min="0"
                                onChange={e => setEditCantidad(c => ({ ...c, [o.id]: e.target.value }))}
                                style={{ width: '80px', padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: '4px' }} />
                              <button className="btn" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => guardarCantidadEditada(o.id)}>💾</button>
                              <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', background: '#95a5a6' }} onClick={() => setEditCantidad(c => ({ ...c, [o.id]: undefined }))}>✕</button>
                            </>
                          ) : (
                            <>
                              {o.cantidad}
                              <button className="btn" style={{ padding: '2px 6px', fontSize: '10px', marginLeft: '5px' }}
                                onClick={() => setEditCantidad(c => ({ ...c, [o.id]: String(o.cantidad) }))}>✏️</button>
                            </>
                          )}
                        </div>
                      </td>
                      <td>{o.precio_unitario ? `S/ ${o.precio_unitario}` : '-'}</td>
                      <td><span style={{ color: estadoColor(o.estado), fontWeight: 600 }}>{(o.estado || '').toUpperCase()}</span></td>
                      <td>{o.es_sugerida ? <span style={{ color: '#f39c12' }}>🤖 Sugerida</span> : <span style={{ color: '#667eea' }}>👤 Manual</span>}</td>
                      <td>
                        {!o.es_sugerida && (
                          <div style={{ display: 'flex', gap: '5px' }}>
                            <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#27ae60', color: '#fff' }} onClick={() => recibirOrden(o.id)}>✅ Recibir</button>
                            <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#e74c3c', color: '#fff' }} onClick={() => cancelarOrden(o.id)}>🛑 Cancelar</button>
                          </div>
                        )}
                        {o.es_sugerida && (
                          <div style={{ display: 'flex', gap: '5px' }}>
                            <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#27ae60', color: '#fff' }} onClick={() => confirmarOrden(o.id)}>✅ Confirmar</button>
                            <button className="btn" style={{ padding: '5px 10px', fontSize: '12px', background: '#e74c3c', color: '#fff' }} onClick={() => cancelarOrden(o.id)}>🛑 Cancelar</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p style={{ color: '#8892a4' }}>No hay órdenes pendientes.</p>
          )}
        </div>
      )}

      {tab === 'completadas' && (
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>📦 Órdenes Completadas</h3>
          {completadas.length > 0 ? (
            <table id="historialTable">
              <thead>
                <tr>
                  <th>ID</th><th>Proveedor</th><th>Insumo</th><th>Fecha</th>
                  <th>Cantidad</th><th>Precio</th><th>Estado</th><th>Origen</th>
                </tr>
              </thead>
              <tbody>
                {completadas.map(o => (
                  <tr key={o.id}>
                    <td>{o.id}</td>
                    <td>{o.proveedor_nombre}</td>
                    <td>{o.insumo_nombre}</td>
                    <td>{formatDateShort(o.fecha_orden)}</td>
                    <td>
                      {o.cantidad}
                      {o.cantidad_sugerida_original && o.cantidad !== o.cantidad_sugerida_original && (
                        <span style={{ fontSize: '11px', color: '#f39c12' }}> (editado)</span>
                      )}
                    </td>
                    <td>{o.precio_unitario ? `S/ ${o.precio_unitario}` : '-'}</td>
                    <td><span style={{ color: estadoColor(o.estado), fontWeight: 600 }}>{(o.estado || '').toUpperCase()}</span></td>
                    <td>{o.es_sugerida ? <span style={{ color: '#f39c12' }}>🤖 Sugerida</span> : <span style={{ color: '#667eea' }}>👤 Manual</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#8892a4' }}>No hay órdenes completadas.</p>
          )}
        </div>
      )}
    </>
  )
}
