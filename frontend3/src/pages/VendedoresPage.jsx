import { useState, useEffect } from 'react'
import { api } from '../api/api'
import { openPrintWindow, tableHeaderHtml, descargarExcel, enviarPorCorreo } from '../utils/pdf'

const MEDALS = ['🥇', '🥈', '🥉']

export default function VendedoresPage() {
  const [vendedores, setVendedores] = useState([])
  const [loading, setLoading] = useState(true)
  const [ventasHoy, setVentasHoy] = useState([])
  const [form, setForm] = useState({ nombre: '', apellido: '', dni: '', telefono: '', email: '', username: '', password: '' })
  const [editando, setEditando] = useState(null)
  const [result, setResult] = useState('')
  const [busqueda, setBusqueda] = useState('')

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/vendedores/todos'),
      api.get('/vendedores/ventas-hoy'),
    ]).then(([vends, ventas]) => {
      setVendedores(Array.isArray(vends) ? vends : [])
      setVentasHoy(Array.isArray(ventas) ? ventas : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const resetForm = () => {
    setForm({ nombre: '', apellido: '', dni: '', telefono: '', email: '', username: '', password: '' })
    setEditando(null)
  }

  const abrirEditar = (v) => {
    setForm({
      nombre: v.nombre || '',
      apellido: v.apellido || '',
      dni: v.dni || '',
      telefono: v.telefono || '',
      email: v.email || '',
      username: v.username || '',
      password: '',
    })
    setEditando(v)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.nombre || !form.dni) {
      setResult('⚠️ Nombre y DNI son obligatorios')
      return
    }
    try {
      const body = {
        nombre: form.nombre.trim(),
        apellido: form.apellido.trim() || null,
        dni: form.dni.trim(),
        telefono: form.telefono.trim() || null,
        email: form.email.trim() || null,
      }
      if (editando) {
        if (form.username.trim()) body.username = form.username.trim()
        if (form.password.trim()) body.password = form.password.trim()
        await api.put(`/vendedores/${editando.id}`, body)
        setResult('✅ Vendedor actualizado correctamente')
      } else {
        await api.post('/vendedores/', body)
        const usuario = form.telefono.trim() || form.dni.trim()
        const clave = form.dni.trim()
        setResult(`✅ Vendedor creado • Usuario: ${usuario} • Clave: ${clave}`)
      }
      resetForm()
      setTimeout(() => { setResult(''); fetchData() }, 1200)
    } catch (e) {
      setResult(`⚠️ ${e.message || 'Error de conexión'}`)
    }
  }

  const toggleActivo = async (v) => {
    try {
      await api.put(`/vendedores/${v.id}`, { activo: !v.activo })
      fetchData()
    } catch {
      setResult('⚠️ Error al cambiar estado')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este vendedor permanentemente?')) return
    try {
      const res = await api.del(`/vendedores/${id}`)
      setResult(res.mensaje || '✅ Vendedor eliminado')
      setTimeout(() => { setResult(''); fetchData() }, 1200)
    } catch (e) {
      setResult(`⚠️ ${e.message || 'Error al eliminar'}`)
    }
  }

  const ventasMap = {}
  ventasHoy.forEach(v => { ventasMap[v.vendedor_id] = v })
  const top3 = [...ventasHoy].sort((a, b) => b.total_unidades - a.total_unidades).slice(0, 3)

  const filtrados = vendedores.filter(v => {
    if (!busqueda) return true
    const q = busqueda.toLowerCase()
    return v.nombre?.toLowerCase().includes(q) ||
           v.apellido?.toLowerCase().includes(q) ||
           v.dni?.includes(q)
  })

  const generarPDF = () => {
    const tbody = filtrados.map(v => {
      const vh = ventasMap[v.id]
      return `
      <tr>
        <td>${v.id}</td>
        <td>${v.nombre} ${v.apellido || ''}</td>
        <td>${v.dni}</td>
        <td>${v.telefono || '—'}</td>
        <td>${v.email || '—'}</td>
        <td>${vh ? `${vh.total_unidades} u.` : '0 u.'}</td>
        <td>${vh ? `S/ ${vh.total_ingreso}` : '—'}</td>
        <td>${v.activo ? 'Activo' : 'Inactivo'}</td>
      </tr>`
    }).join('')
    openPrintWindow('Vendedores - Panadería Victoria',
      tableHeaderHtml('Vendedores') +
      '<table><thead><tr><th>ID</th><th>Nombre</th><th>DNI</th><th>Teléfono</th><th>Email</th><th>Ventas Hoy</th><th>Ingreso Hoy</th><th>Estado</th></tr></thead><tbody>' +
      tbody + '</tbody></table>' +
      '<div class="footer">Sistema de Gestión Predictiva - Panadería Victoria</div>'
    )
  }

  if (loading) return <div className="card"><p>Cargando...</p></div>

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div>
          <h1>👥 Vendedores</h1>
          <p style={{ color: '#8892a4' }}>Administra a los vendedores de la panadería</p>
        </div>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
        <button className="btn btn-danger" onClick={generarPDF} style={{ fontSize: '11px', padding: '3px 8px', flexShrink: 0 }}>📄 PDF</button>
        <button className="btn" onClick={() => enviarPorCorreo('Vendedores', ['ID', 'Nombre', 'DNI', 'Teléfono', 'Email', 'Ventas Hoy', 'Estado'], (filtrados || []).map(v => { const vh = ventasMap[v.id] || {}; return [v.id, v.nombre + ' ' + (v.apellido || ''), v.dni, v.telefono || '-', v.email || '-', vh.total_unidades ? vh.total_unidades + ' u.' : '0 u.', v.activo ? 'Activo' : 'Inactivo'] }))} style={{ fontSize: '11px', padding: '3px 8px', background: '#e74c3c', color: '#fff', flexShrink: 0 }}>📧 Enviar</button>
        <button className="btn" onClick={() => descargarExcel('Vendedores', [{ key: "id", label: "ID" }, { key: "nombre", label: "Nombre", render: (i) => i.nombre + " " + (i.apellido || "") }, { key: "dni", label: "DNI" }, { key: "telefono", label: "Telefono" }, { key: "email", label: "Email" }], filtrados)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', flexShrink: 0 }}>📊 Excel</button>
        </div>
      </div>

      {top3.length > 0 && (
        <div style={{
          display: 'flex', gap: '20px', padding: '10px 20px', marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(102,126,234,0.06), rgba(118,75,162,0.06))',
          border: '1px solid rgba(102,126,234,0.1)', borderRadius: '10px',
          alignItems: 'center', fontSize: '14px',
        }}>
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)', marginRight: '4px' }}>🏆 Hoy</span>
          {top3.map((v, i) => (
            <span key={v.vendedor_id}>
              {MEDALS[i]} <strong>{v.nombre}</strong> — {v.total_unidades} u. <span style={{ opacity: 0.6 }}>(S/ {v.total_ingreso})</span>
              {i < top3.length - 1 && <span style={{ marginLeft: '20px', opacity: 0.15 }}>|</span>}
            </span>
          ))}
        </div>
      )}

      <div className="card">
        <h3>{editando ? 'Editar Vendedor' : 'Nuevo Vendedor'}</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '10px' }}>
            <input type="text" placeholder="Nombre *" required
              value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} />
            <input type="text" placeholder="Apellido"
              value={form.apellido} onChange={e => setForm(f => ({ ...f, apellido: e.target.value }))} />
            <input type="text" placeholder="DNI * (8 dígitos)" required maxLength={8}
              value={form.dni} onChange={e => setForm(f => ({ ...f, dni: e.target.value.replace(/\D/g, '') }))} />
            <input type="text" placeholder="Teléfono"
              value={form.telefono} onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))} />
            <input type="email" placeholder="Email"
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            {editando && (
              <>
              <input type="text" placeholder="Usuario (login)"
                value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
              <input type="text" placeholder="Contraseña (login)"
                value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
              </>
            )}
          </div>
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            <button type="submit" className="btn">
              {editando ? 'Guardar Cambios' : 'Agregar Vendedor'}
            </button>
            {editando && (
              <button type="button" className="btn btn-danger" onClick={resetForm}>
                Cancelar
              </button>
            )}
          </div>
        </form>
        {result && <p style={{ marginTop: '10px', color: result.includes('✅') ? '#27ae60' : '#e74c3c' }}>{result}</p>}
      </div>

      <div className="card" id="vendedoresTable">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, border: 'none', padding: 0 }}>Vendedores Registrados</h3>
          <input type="text" placeholder="🔍 Buscar por nombre o DNI..."
            value={busqueda} onChange={e => setBusqueda(e.target.value)}
            style={{ width: '260px', padding: '8px 14px', border: '2px solid var(--border-color)',
                     borderRadius: '8px', background: 'var(--bg-card)', color: 'var(--text-primary)',
                     fontSize: '13px', outline: 'none' }} />
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>DNI</th>
                <th>Teléfono</th>
                <th>Email</th>
                <th>Ventas Hoy</th>
                <th>Ingreso Hoy</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtrados.map(v => {
                const vh = ventasMap[v.id]
                return (
                <tr key={v.id}>
                  <td>{v.id}</td>
                  <td><strong>{v.nombre} {v.apellido}</strong></td>
                  <td>{v.dni}</td>
                  <td>{v.telefono || '—'}</td>
                  <td>{v.email || '—'}</td>
                  <td>
                    <span className="badge-ventas">
                      {vh ? `${vh.total_unidades} u.` : '0 u.'}
                    </span>
                  </td>
                  <td style={{ fontSize: '13px' }}>
                    {vh ? <strong>S/ {vh.total_ingreso}</strong> : '—'}
                  </td>
                  <td>
                    <span className={`badge-estado ${v.activo ? 'activo' : 'inactivo'}`}>
                      {v.activo ? '🟢 Activo' : '🔴 Inactivo'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn-action" onClick={() => abrirEditar(v)} title="Editar">✏️</button>
                      <button className="btn-action" onClick={() => toggleActivo(v)} title={v.activo ? 'Desactivar' : 'Reactivar'}>
                        {v.activo ? '⛔' : '✅'}
                      </button>
                      <button className="btn-action" onClick={() => handleDelete(v.id)} title="Eliminar" style={{ background: '#e74c3c20' }}>🗑️</button>
                    </div>
                  </td>
                </tr>
              )})}
              {filtrados.length === 0 && (
                <tr><td colSpan={9} style={{ textAlign: 'center', color: '#8892a4' }}>No se encontraron vendedores</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
