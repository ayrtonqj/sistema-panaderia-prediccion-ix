import { useState, useEffect } from 'react'
import { api } from '../api/api'

export default function ProveedoresPage() {
  const [proveedores, setProveedores] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ nombre: '', contacto: '', telefono: '', email: '', direccion: '', productos_que_provee: '' })
  const [editId, setEditId] = useState(null)

  const fetchProveedores = async () => {
    try {
      setLoading(true)
      const data = await api.get('/proveedores/')
      setProveedores(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProveedores() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editId) {
        await api.put(`/proveedores/${editId}`, form)
      } else {
        await api.post('/proveedores/', form)
      }
      setShowForm(false)
      setEditId(null)
      setForm({ nombre: '', contacto: '', telefono: '', email: '', direccion: '', productos_que_provee: '' })
      fetchProveedores()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleEdit = (p) => {
    setForm({ nombre: p.nombre, contacto: p.contacto || '', telefono: p.telefono || '', email: p.email || '', direccion: p.direccion || '', productos_que_provee: p.productos_que_provee || '' })
    setEditId(p.id)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este proveedor?')) return
    try {
      await api.del(`/proveedores/${id}`)
      fetchProveedores()
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Proveedores</h1>
        <button className="btn-primary" onClick={() => { setShowForm(true); setEditId(null); setForm({ nombre: '', contacto: '', telefono: '', email: '', direccion: '', productos_que_provee: '' }) }}>
          + Nuevo Proveedor
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{editId ? 'Editar Proveedor' : 'Nuevo Proveedor'}</h2>
            <form onSubmit={handleSubmit} className="form-grid">
              <label>Nombre *
                <input required value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} />
              </label>
              <label>Contacto
                <input value={form.contacto} onChange={e => setForm({ ...form, contacto: e.target.value })} />
              </label>
              <label>Teléfono
                <input value={form.telefono} onChange={e => setForm({ ...form, telefono: e.target.value })} />
              </label>
              <label>Email
                <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
              </label>
              <label>Dirección
                <input value={form.direccion} onChange={e => setForm({ ...form, direccion: e.target.value })} />
              </label>
              <label>Productos que provee
                <input value={form.productos_que_provee} onChange={e => setForm({ ...form, productos_que_provee: e.target.value })} />
              </label>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
                <button type="submit" className="btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading && <p className="loading-text">Cargando proveedores...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Contacto</th>
                <th>Teléfono</th>
                <th>Email</th>
                <th>Dirección</th>
                <th>Productos</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {proveedores.length === 0 ? (
                <tr><td colSpan="7" style={{ textAlign: 'center' }}>No hay proveedores registrados</td></tr>
              ) : proveedores.map(p => (
                <tr key={p.id}>
                  <td>{p.nombre}</td>
                  <td>{p.contacto || '-'}</td>
                  <td>{p.telefono || '-'}</td>
                  <td>{p.email || '-'}</td>
                  <td>{p.direccion || '-'}</td>
                  <td>{p.productos_que_provee || '-'}</td>
                  <td>
                    <button className="btn-icon" onClick={() => handleEdit(p)} title="Editar">✏️</button>
                    <button className="btn-icon danger" onClick={() => handleDelete(p.id)} title="Eliminar">🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
