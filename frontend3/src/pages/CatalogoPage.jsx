import { useState, useEffect } from 'react'
import { api } from '../api/api'
import Pagination from '../components/Pagination'
import { openPrintWindow, tableHeaderHtml } from '../utils/pdf'

function estadoDias(dias) {
  if (dias === null || dias === undefined) return { label: 'Sin registro', color: '#95a5a6', icon: '⚪' }
  if (dias <= 1) return { label: 'Hoy', color: '#27ae60', icon: '🟢' }
  if (dias <= 3) return { label: `${dias}d`, color: '#27ae60', icon: '🟢' }
  if (dias <= 7) return { label: `${dias}d`, color: '#f39c12', icon: '🟡' }
  return { label: `${dias}d`, color: '#e74c3c', icon: '🔴' }
}

export default function CatalogoPage() {
  const [productos, setProductos] = useState([])
  const [actividad, setActividad] = useState({})
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ nombre: '', categoria: '', precio: '', costo: '' })
  const [editingId, setEditingId] = useState(null)
  const [result, setResult] = useState('')

  const fetchData = () => {
    setLoading(true)
    api.get('/productos/').then(data => {
      const list = Array.isArray(data) ? data : []
      setProductos(list.map(p => ({
        ...p,
        margen_pct: p.precio > 0 ? Math.round(((p.precio - p.costo) / p.precio) * 100 * 10) / 10 : 0,
      })))
      api.get('/productos/actividad').then(data => {
        const map = {}
        ;(Array.isArray(data) ? data : []).forEach(a => { map[a.id] = a })
        setActividad(map)
      }).catch(() => {})
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingId) {
        await api.put(`/productos/${editingId}`, {
          nombre: form.nombre,
          categoria: form.categoria,
          precio: parseFloat(form.precio),
          costo: parseFloat(form.costo),
        })
        setResult('✅ Producto actualizado correctamente')
      } else {
        await api.post('/productos/', {
          nombre: form.nombre,
          categoria: form.categoria,
          precio: parseFloat(form.precio),
          costo: parseFloat(form.costo),
        })
        setResult('✅ Producto agregado correctamente')
      }
      setForm({ nombre: '', categoria: '', precio: '', costo: '' })
      setEditingId(null)
      setTimeout(() => { setResult(''); fetchData() }, 1000)
    } catch {
      setResult('⚠️ Error de conexión')
    }
  }

  const handleEdit = (p) => {
    setEditingId(p.id)
    setForm({ nombre: p.nombre, categoria: p.categoria, precio: String(p.precio), costo: String(p.costo) })
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este producto?')) return
    try {
      await api.del(`/productos/${id}`)
      setResult('✅ Producto eliminado correctamente')
      setTimeout(() => { setResult(''); fetchData() }, 1000)
    } catch {
      setResult('⚠️ Error al eliminar')
    }
  }

  const cancelEdit = () => {
    setEditingId(null)
    setForm({ nombre: '', categoria: '', precio: '', costo: '' })
  }

  const generarPDF = () => {
    const tbody = productos.map(p => {
      const a = actividad[p.id] || {}
      return `
      <tr>
        <td>${p.id}</td>
        <td>${p.nombre}</td>
        <td>${p.categoria}</td>
        <td>S/ ${p.precio}</td>
        <td>S/ ${p.costo}</td>
        <td>${p.margen_pct}%</td>
        <td>${a.ultima_produccion || '—'}</td>
        <td>${a.ultima_venta || '—'}</td>
      </tr>`
    }).join('')
    openPrintWindow('Catálogo de Productos - Panadería Victoria',
      tableHeaderHtml('Catálogo de Productos') +
      '<table><thead><tr><th>ID</th><th>Nombre</th><th>Categoría</th><th>Precio</th><th>Costo</th><th>Margen</th><th>Últ. Producción</th><th>Últ. Venta</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
    )
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>📦 Catálogo de Productos</h1>
          <p style={{ color: '#8892a4' }}>Administra los productos que vendes</p>
        </div>
        <button className="btn btn-danger" onClick={generarPDF}>📄 Descargar PDF</button>
      </div>

      <div className="card">
        <h3>{editingId ? '✏️ Editar Producto' : 'Nuevo Producto'}</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <input type="text" placeholder="Nombre del producto" required
              value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} />
            <input type="text" placeholder="Categoría (Pan, Dulce, Salado)" required
              value={form.categoria} onChange={e => setForm(f => ({ ...f, categoria: e.target.value }))} />
            <input type="number" placeholder="Precio de venta" step="0.01" min="0" required
              value={form.precio} onChange={e => setForm(f => ({ ...f, precio: e.target.value }))} />
            <input type="number" placeholder="Costo de producción" step="0.01" min="0" required
              value={form.costo} onChange={e => setForm(f => ({ ...f, costo: e.target.value }))} />
          </div>
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            <button type="submit" className="btn">{editingId ? 'Actualizar Producto' : 'Agregar Producto'}</button>
            {editingId && <button type="button" className="btn" style={{ background: '#95a5a6' }} onClick={cancelEdit}>Cancelar</button>}
          </div>
        </form>
        {result && <p style={{ marginTop: '10px', color: result.includes('✅') ? '#27ae60' : '#e74c3c' }}>{result}</p>}
      </div>

      <div className="card">
        <h3>Productos Registrados {!loading && <span style={{ fontSize: '14px', color: '#8892a4', fontWeight: 400 }}>({productos.length})</span>}</h3>
        {loading ? <p>Cargando...</p> : (
          <Pagination
            data={productos}
            pageSize={20}
            columns={['ID', 'Nombre', 'Categoría', 'Precio', 'Costo', 'Margen', 'Últ. Producción', 'Últ. Venta', 'Acciones']}
            renderRow={(p) => {
              const a = actividad[p.id] || {}
              const estProd = estadoDias(a.dias_sin_producir)
              const estVenta = estadoDias(a.dias_sin_vender)
              return (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    {estProd.icon}
                    {p.nombre}
                  </span>
                </td>
                <td>{p.categoria}</td>
                <td>S/ {p.precio}</td>
                <td>S/ {p.costo}</td>
                <td style={{ color: p.margen_pct >= 30 ? '#27ae60' : '#e74c3c' }}>{p.margen_pct}%</td>
                <td style={{ color: estProd.color, fontSize: '13px' }} title={a.ultima_produccion || ''}>
                  {a.ultima_produccion || '—'}
                  {a.dias_sin_producir !== null && a.dias_sin_producir !== undefined && (
                    <span style={{ opacity: 0.6, marginLeft: 4 }}>({estProd.label})</span>
                  )}
                </td>
                <td style={{ color: estVenta.color, fontSize: '13px' }} title={a.ultima_venta || ''}>
                  {a.ultima_venta || '—'}
                  {a.dias_sin_vender !== null && a.dias_sin_vender !== undefined && (
                    <span style={{ opacity: 0.6, marginLeft: 4 }}>({estVenta.label})</span>
                  )}
                </td>
                <td>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', marginRight: '5px' }} onClick={() => handleEdit(p)}>✏️</button>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '12px', background: '#e74c3c', color: '#fff' }} onClick={() => handleDelete(p.id)}>🗑️</button>
                </td>
              </tr>
            )}}
          />
        )}
      </div>
    </>
  )
}
