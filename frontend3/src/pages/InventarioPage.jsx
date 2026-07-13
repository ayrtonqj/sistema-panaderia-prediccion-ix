import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'
import { openPrintWindow, tableHeaderHtml, descargarExcel, enviarPorCorreo } from '../utils/pdf'

function proyDias(d) {
  if (d === null || d === undefined) return { label: '—', color: '#95a5a6' }
  if (d > 15) return { label: `${d}d`, color: '#27ae60' }
  if (d >= 7) return { label: `${d}d`, color: '#f39c12' }
  return { label: `${d}d`, color: '#e74c3c' }
}

export default function InventarioPage() {
  const [insumos, setInsumos] = useState([])
  const [proveedores, setProveedores] = useState([])
  const [alertas, setAlertas] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ nombre: '', stock_actual: '', stock_minimo: '', unidad_medida: '', proveedor_id: '' })
  const [editingId, setEditingId] = useState(null)
  const [result, setResult] = useState('')
  const [ajustandoId, setAjustandoId] = useState(null)
  const [ajusteForm, setAjusteForm] = useState({ cantidad: '', motivo: '' })

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/insumos/'),
      api.get('/insumos/alertas/'),
      api.get('/proveedores/').catch(() => []),
    ]).then(([ins, al, prov]) => {
      setInsumos(Array.isArray(ins) ? ins : [])
      setAlertas(Array.isArray(al) ? al : [])
      setProveedores(Array.isArray(prov) ? prov : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const body = {
        nombre: form.nombre,
        stock_actual: parseFloat(form.stock_actual),
        stock_minimo: parseFloat(form.stock_minimo),
        unidad_medida: form.unidad_medida,
        proveedor_id: form.proveedor_id ? parseInt(form.proveedor_id) : null,
      }
      if (editingId) {
        await api.put(`/insumos/${editingId}`, body)
        setResult('✅ Insumo actualizado correctamente')
      } else {
        await api.post('/insumos/', body)
        setResult('✅ Insumo agregado correctamente')
      }
      setForm({ nombre: '', stock_actual: '', stock_minimo: '', unidad_medida: '', proveedor_id: '' })
      setEditingId(null)
      setTimeout(() => { setResult(''); fetchData() }, 1000)
    } catch {
      setResult('⚠️ Error de conexión')
    }
  }

  const handleEdit = (i) => {
    setEditingId(i.id)
    setForm({
      nombre: i.nombre,
      stock_actual: String(i.stock_actual),
      stock_minimo: String(i.stock_minimo),
      unidad_medida: i.unidad_medida,
      proveedor_id: i.proveedor_id ? String(i.proveedor_id) : '',
    })
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este insumo?')) return
    try {
      await api.del(`/insumos/${id}`)
      setResult('✅ Insumo eliminado correctamente')
      setTimeout(() => { setResult(''); fetchData() }, 1000)
    } catch {
      setResult('⚠️ Error al eliminar')
    }
  }

  const cancelEdit = () => {
    setEditingId(null)
    setForm({ nombre: '', stock_actual: '', stock_minimo: '', unidad_medida: '', proveedor_id: '' })
  }

  const iniciarAjuste = (id) => {
    setAjustandoId(id)
    setAjusteForm({ cantidad: '', motivo: '' })
  }

  const confirmarAjuste = async () => {
    if (!ajusteForm.cantidad || !ajusteForm.motivo) return
    try {
      const res = await api.post(`/insumos/${ajustandoId}/ajustar`, {
        cantidad: parseFloat(ajusteForm.cantidad),
        motivo: ajusteForm.motivo,
      })
      setResult(res.mensaje || '✅ Stock ajustado')
      setAjustandoId(null)
      setTimeout(() => { setResult(''); fetchData() }, 1000)
    } catch {
      setResult('⚠️ Error al ajustar stock')
    }
  }

  const generarPDF = () => {
    const tbody = insumos.map(i => {
      const proy = proyDias(i.dias_restantes)
      return `
      <tr>
        <td>${i.id}</td>
        <td>${i.nombre}</td>
        <td>${i.proveedor_nombre || '—'}</td>
        <td>${i.stock_actual}</td>
        <td>${i.stock_minimo}</td>
        <td>${i.unidad_medida}</td>
        <td>${proy.label}</td>
        <td>${i.stock_actual < i.stock_minimo ? '⚠️ Bajo' : '✅ OK'}</td>
      </tr>`
    }).join('')
    openPrintWindow('Inventario de Insumos - Panadería Victoria',
      tableHeaderHtml('Inventario de Insumos') +
      '<table><thead><tr><th>ID</th><th>Nombre</th><th>Proveedor</th><th>Stock Actual</th><th>Stock Mínimo</th><th>Unidad</th><th>Proyección</th><th>Estado</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
    )
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div>
          <h1>🏪 Inventario de Insumos</h1>
          <p style={{ color: '#8892a4' }}>Controla tus materias primas e insumos</p>
        </div>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
        <button className="btn btn-danger" onClick={generarPDF} style={{ fontSize: '11px', padding: '3px 8px', flexShrink: 0 }}>📄 PDF</button>
        <button className="btn" onClick={() => enviarPorCorreo('Inventario de Insumos', ['ID', 'Nombre', 'Stock Actual', 'Stock Mínimo', 'Unidad', 'Estado'], (insumos || []).map(i => [i.id, i.nombre, i.stock_actual, i.stock_minimo, i.unidad_medida, i.stock_actual < i.stock_minimo ? '⚠️ Bajo' : '✅ OK']))} style={{ fontSize: '11px', padding: '3px 8px', background: '#e74c3c', color: '#fff', flexShrink: 0 }}>📧 Enviar</button>
        <button className="btn" onClick={() => descargarExcel('Inventario', [{ key: "id", label: "ID" }, { key: "nombre", label: "Nombre" }, { key: "proveedor_nombre", label: "Proveedor" }, { key: "stock_actual", label: "Stock Actual" }, { key: "stock_minimo", label: "Stock Min" }, { key: "unidad_medida", label: "Unidad" }], insumos)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', flexShrink: 0 }}>📊 Excel</button>
        </div>
      </div>

      {alertas.length > 0 && (
        <div className="alert alert-error">
          <strong>⚠️ Alertas de Stock:</strong>
          <br />
          {alertas.map(a => (
            <span key={a.id} style={{ marginRight: '15px' }}>
              • {a.nombre} ({a.stock_actual}/{a.stock_minimo} {a.unidad_medida})
            </span>
          ))}
        </div>
      )}

      <div className="card">
        <h3>{editingId ? '✏️ Editar Insumo' : 'Nuevo Insumo'}</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
            <input type="text" placeholder="Nombre del insumo" required
              value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} />
            <input type="number" placeholder="Stock actual" step="0.01" min="0" required
              value={form.stock_actual} onChange={e => setForm(f => ({ ...f, stock_actual: e.target.value }))} />
            <input type="number" placeholder="Stock mínimo" step="0.01" min="0" required
              value={form.stock_minimo} onChange={e => setForm(f => ({ ...f, stock_minimo: e.target.value }))} />
            <input type="text" placeholder="Unidad (kg, lt, und)" required
              value={form.unidad_medida} onChange={e => setForm(f => ({ ...f, unidad_medida: e.target.value }))} />
            <select value={form.proveedor_id} onChange={e => setForm(f => ({ ...f, proveedor_id: e.target.value }))}
              style={{ padding: '10px', border: '1px solid var(--border-color)', borderRadius: '8px', background: 'var(--bg-card)', color: 'var(--text-primary)' }}>
              <option value="">Sin proveedor</option>
              {proveedores.map(p => (
                <option key={p.id} value={p.id}>{p.nombre}</option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            <button type="submit" className="btn">{editingId ? 'Actualizar Insumo' : 'Agregar Insumo'}</button>
            {editingId && <button type="button" className="btn" style={{ background: '#95a5a6' }} onClick={cancelEdit}>Cancelar</button>}
          </div>
        </form>
        {result && <p style={{ marginTop: '10px', color: result.includes('✅') ? '#27ae60' : '#e74c3c' }}>{result}</p>}
      </div>

      <div className="card" id="InventarioPageTable">
        <h3>Inventario Actual</h3>
        {loading ? <p>Cargando...</p> : (
          <Pagination
            data={insumos}
            pageSize={20}
            columns={['ID', 'Nombre', 'Proveedor', 'Stock Actual', 'Stock Mín.', 'Unidad', 'Proyección', 'Estado', 'Acciones']}
            renderRow={(i) => (
              <>
              <tr key={i.id} style={{ color: i.stock_actual < i.stock_minimo ? '#e74c3c' : undefined }}>
                <td>{i.id}</td>
                <td>{i.nombre}</td>
                <td style={{ fontSize: '13px' }}>{i.proveedor_nombre || '—'}</td>
                <td>{i.stock_actual}</td>
                <td>{i.stock_minimo}</td>
                <td>{i.unidad_medida}</td>
                <td style={{ color: proyDias(i.dias_restantes).color, fontWeight: 600, fontSize: '13px' }}>
                  {proyDias(i.dias_restantes).label}
                </td>
                <td>{i.stock_actual < i.stock_minimo ? '⚠️ Bajo' : '✅ OK'}</td>
                <td>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', marginRight: '3px' }} onClick={() => handleEdit(i)}>✏️</button>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', marginRight: '3px', background: '#f39c12', color: '#fff' }} onClick={() => iniciarAjuste(i.id)}>📦</button>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', background: '#e74c3c', color: '#fff' }} onClick={() => handleDelete(i.id)}>🗑️</button>
                </td>
              </tr>
              {ajustandoId === i.id && (
                <tr key={`ajuste-${i.id}`}>
                  <td colSpan={9} style={{ padding: '8px', background: 'var(--bg-card)' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input type="number" step="0.01" placeholder="Cantidad (+ entrada, - salida)" style={{ flex: 1, padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                        value={ajusteForm.cantidad} onChange={e => setAjusteForm(f => ({ ...f, cantidad: e.target.value }))} />
                      <input type="text" placeholder="Motivo del ajuste" style={{ flex: 2, padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                        value={ajusteForm.motivo} onChange={e => setAjusteForm(f => ({ ...f, motivo: e.target.value }))} />
                      <button className="btn" style={{ padding: '6px 14px', background: '#27ae60', color: '#fff' }} onClick={confirmarAjuste}>✅</button>
                      <button className="btn" style={{ padding: '6px 14px', background: '#95a5a6', color: '#fff' }} onClick={() => setAjustandoId(null)}>❌</button>
                    </div>
                  </td>
                </tr>
              )}
              </>
            )}
          />
        )}
      </div>
    </>
  )
}
