import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../api/api'
import { descargarExcel } from '../utils/pdf'
import { useAuth } from '../context/AuthContext'
import { useNav } from '../context/NavContext'
import { generarFacturaHTML, getNextInvoiceNumber, openPrintWindow, numeroALetras } from '../utils/pdf'

const CATEGORY_EMOJIS = {
  'Pan de mesa': '🍞',
  'Pan especial': '🥖',
  'Bollería': '🥐',
  'Salados': '🥟',
  'Pasteles': '🎂',
  'Dulces': '🍪',
}

function getEmoji(categoria) {
  return CATEGORY_EMOJIS[categoria] || '🥐'
}

import { formatDateShort, formatTime } from '../utils/formatters'

function formatearHora(d) { return formatTime(d) }
function formatearFecha(d) { return formatDateShort(d) }
function formatearFechaFactura(d) { return formatDateShort(d) }

export default function VentaRapidaPage() {
  const { user } = useAuth()
  const navigate = useNav()
  const [productos, setProductos] = useState([])
  const [ventasHoy, setVentasHoy] = useState(null)
  const [loading, setLoading] = useState(true)
  const [cart, setCart] = useState([])
  const [toast, setToast] = useState(null)
  const [invoiceModal, setInvoiceModal] = useState(null)
  const [vendedorNombre, setVendedorNombre] = useState('')
  const [vendedorDni, setVendedorDni] = useState('')
  const [search, setSearch] = useState('')
  const [catFilter, setCatFilter] = useState('todas')
  const [sugerencias, setSugerencias] = useState([])
  const [produccionHoy, setProduccionHoy] = useState([])
  const [metodoPago, setMetodoPago] = useState('efectivo')
  const [panPasado, setPanPasado] = useState([])
  const [ppCantidades, setPpCantidades] = useState({})
  const [ppExpandido, setPpExpandido] = useState(false)
  const scrollRef = useRef(null)
  const scrollPos = useRef(0)
  const [condiciones, setCondiciones] = useState(null)

  useEffect(() => {
    if (!user?.vendedor_id) { setVendedorNombre(''); setVendedorDni(''); return }
    api.get(`/vendedores/${user.vendedor_id}`)
      .then(v => {
        setVendedorNombre(`${v.nombre}${v.apellido ? ' ' + v.apellido : ''}`)
        setVendedorDni(v.dni || '')
      })
      .catch(() => {
        setVendedorNombre(user.username)
        setVendedorDni('')
      })
  }, [user])

  const cargarDatos = useCallback(async () => {
    scrollPos.current = scrollRef.current?.scrollTop || 0
    try {
      const [prods, hoy, sug, prodHoy, pp, cond] = await Promise.all([
        api.get('/productos/'),
        api.get('/ventas/hoy'),
        api.get('/produccion/sugerida').catch(() => null),
        api.get('/produccion/hoy'),
        api.get('/pan-pasado/disponible').catch(() => []),
        api.get('/dashboard/condiciones-venta').catch(() => null),
      ])
      setProductos(Array.isArray(prods) ? prods : [])
      setVentasHoy(hoy)
      setSugerencias(Array.isArray(sug) ? sug : [])
      setProduccionHoy(Array.isArray(prodHoy) ? prodHoy : [])
      setCondiciones(cond)
      if (Array.isArray(pp) && pp.length === 0) {
        const gen = await api.post('/pan-pasado/auto-generar?dias=3', {}).catch(() => null)
        if (gen && gen.creados > 0) {
          const pp2 = await api.get('/pan-pasado/disponible').catch(() => [])
          setPanPasado(Array.isArray(pp2) ? pp2 : [])
        } else {
          setPanPasado([])
        }
      } else {
        setPanPasado(Array.isArray(pp) ? pp : [])
      }
    } catch {
      setToast({ tipo: 'error', msg: '⚠️ Error de conexión' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!loading && scrollRef.current) {
      scrollRef.current.scrollTop = scrollPos.current
    }
  }, [loading])

  useEffect(() => {
    cargarDatos()
  }, [cargarDatos])

  useEffect(() => {
    if (!toast) return
    const id = setTimeout(() => setToast(null), 3000)
    return () => clearTimeout(id)
  }, [toast])

  const agregarAlCarrito = (producto, panPasadoId) => {
    setCart(prev => {
      const key = panPasadoId || producto.id
      const existente = prev.find(c => c.cartKey === key)
      if (existente) {
        return prev.map(c =>
          c.cartKey === key
            ? { ...c, cantidad: c.cantidad + 1 }
            : c
        )
      }
      return [...prev, { producto, cantidad: 1, panPasadoId, cartKey: key }]
    })
  }

  const actualizarCantidad = (cartKey, nuevaCantidad) => {
    if (nuevaCantidad <= 0) {
      setCart(prev => prev.filter(c => c.cartKey !== cartKey))
      return
    }
    setCart(prev =>
      prev.map(c =>
        c.cartKey === cartKey
          ? { ...c, cantidad: nuevaCantidad }
          : c
      )
    )
  }

  const eliminarDelCarrito = (cartKey) => {
    setCart(prev => prev.filter(c => c.cartKey !== cartKey))
  }

  const vendedorId = user?.vendedor_id || undefined

  const ejecutarVenta = async () => {
    try {
      const regulares = invoiceModal.items.filter(c => !c.panPasadoId)
      const panPasados = invoiceModal.items.filter(c => c.panPasadoId)
      if (regulares.length > 0) {
        await api.post('/ventas/rapida/lote', {
          items: regulares.map(c => ({
            producto_id: c.producto.id,
            cantidad_vendida: c.cantidad,
            vendedor_id: vendedorId,
            metodo_pago: invoiceModal.metodo_pago || 'efectivo',
          })),
        })
      }
      if (panPasados.length > 0) {
        for (const c of panPasados) {
          await api.post(`/pan-pasado/${c.panPasadoId}/vender`, {
            cantidad_vender: c.cantidad,
            vendedor_id: vendedorId,
            metodo_pago: invoiceModal.metodo_pago || 'efectivo',
          })
        }
      }
      const total = invoiceModal.items.reduce((sum, c) => sum + c.cantidad, 0)
      setToast({ tipo: 'ok', msg: `✅ ${total} producto(s) registrado(s)` })
      playBeep()
      setCart([])
      setInvoiceModal(null)
      const [hoy, pp2] = await Promise.all([
        api.get('/ventas/hoy'),
        api.get('/pan-pasado/disponible').catch(() => []),
      ])
      setVentasHoy(hoy)
      setPanPasado(Array.isArray(pp2) ? pp2 : [])
    } catch {
      setToast({ tipo: 'error', msg: '❌ Error al registrar venta' })
    }
  }

  const mostrarFactura = () => {
    if (cart.length === 0) return
    const soloPanPasado = cart.every(c => c.panPasadoId)
    if (!todosProducidos && !soloPanPasado) {
      setToast({ tipo: 'error', msg: '⚠️ Todos los productos deben tener producción registrada hoy. Redirigiendo...' })
      setTimeout(() => navigate('registro_diario'), 1200)
      return
    }
    const ahora = new Date()
    const fecha = formatearFechaFactura(ahora)
    const horaStr = formatearHora(ahora)
    const numero = getNextInvoiceNumber()
    const total = cart.reduce((sum, c) => sum + c.producto.precio * c.cantidad, 0)
    const igv = total * 0.18 / 1.18
    const subtotal = total - igv

    setInvoiceModal({
      items: [...cart],
      fecha,
      hora: horaStr,
      numero,
      subtotal,
      igv,
      total,
      vendedor_nombre: vendedorNombre,
      vendedor_dni: vendedorDni,
      metodo_pago: metodoPago,
    })
  }

  const imprimirFactura = () => {
    if (!invoiceModal) return
    const html = generarFacturaHTML(invoiceModal.items, {
      numero: invoiceModal.numero,
      fecha: invoiceModal.fecha,
      hora: invoiceModal.hora,
      items: invoiceModal.items,
      subtotal: invoiceModal.subtotal,
      igv: invoiceModal.igv,
      total: invoiceModal.total,
      totalLetras: numeroALetras(invoiceModal.total),
      vendedor_nombre: invoiceModal.vendedor_nombre,
      vendedor_dni: invoiceModal.vendedor_dni,
    })
    openPrintWindow(`Boleta ${invoiceModal.numero}`, html)
  }

  const totalCarrito = cart.reduce((sum, c) => sum + c.producto.precio * c.cantidad, 0)
  const itemsCount = cart.reduce((sum, c) => sum + c.cantidad, 0)

  const categorias = ['todas', ...new Set(productos.map(p => p.categoria))]
  const filtrados = productos.filter(p =>
    (catFilter === 'todas' || p.categoria === catFilter) &&
    p.nombre.toLowerCase().includes(search.toLowerCase())
  )
  const stockMap = {}
  produccionHoy.forEach(p => {
    stockMap[p.producto_id] = {
      producido: p.producido_hoy || 0,
      vendido: p.vendido_hoy || 0,
      disponible: Math.max(0, (p.producido_hoy || 0) - (p.vendido_hoy || 0)),
    }
  })
  const ingresos = ventasHoy?.productos || []
  const ingresoTotal = ingresos.reduce((s, v) => s + (v.ingreso || 0), 0)
  const totalTransacciones = ingresos.reduce((s, v) => s + (v.transacciones || 0), 0)
  const ticketPromedio = totalTransacciones > 0 ? ingresoTotal / totalTransacciones : 0

  const produccionMap = {}
  produccionHoy.forEach(p => { produccionMap[p.id || p.producto_id] = p })
  const todosProducidos = productos.length > 0 && productos.every(p => {
    const prod = produccionMap[p.id]
    return prod && prod.producido_hoy > 0
  })

  const puedeRegistrar = cart.length > 0 && todosProducidos

  function playBeep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = 880
      osc.type = 'sine'
      gain.gain.setValueAtTime(0.5, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2)
      osc.start()
      osc.stop(ctx.currentTime + 0.2)
    } catch { /* fallback silencioso */ }
  }

  const PAYMENT_EMOJIS = { efectivo: '💵', yape: '📱', plin: '🟣', tarjeta: '💳' }

  const showToast = toast ? (
    <div className={`toast ${toast.tipo}`}>{toast.msg}</div>
  ) : null

  if (loading) return <div className="card"><p>Cargando...</p></div>

  const ventasProductos = ventasHoy?.productos || []

  return (
    <>
      <div className="page-header">
        <h1>🛒 Venta Rápida</h1>
        <div className="venta-rapida-totales">
          {user?.vendedor_id && (
            <span className="header-vendedor">👤 {vendedorNombre}</span>
          )}
        </div>
      </div>
      <div className="venta-rapida-layout">
        <div className="productos-section" ref={scrollRef}>

          {panPasado.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div onClick={() => setPpExpandido(e => !e)} style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                background: 'linear-gradient(135deg, #fff3e0, #ffe0b2)',
                borderRadius: '8px', padding: '7px 12px',
                border: '1px solid #ffcc80', cursor: 'pointer',
              }}>
                <span style={{ fontSize: '16px' }}>🥖</span>
                <span style={{ fontWeight: 700, fontSize: '13px', color: '#e65100', flex: 1 }}>Pan del Día Anterior</span>
                <span style={{ fontSize: '11px', color: '#bf360c' }}>Agregar al carrito</span>
                <span style={{
                  background: '#e65100', color: '#fff', borderRadius: '10px',
                  padding: '1px 8px', fontSize: '11px', fontWeight: 600,
                }}>{panPasado.reduce((s, p) => s + p.disponible, 0)} uds</span>
                <span style={{ fontSize: '11px', color: '#e65100', fontWeight: 600, transition: 'transform 0.2s', transform: ppExpandido ? 'rotate(180deg)' : '' }}>▼</span>
              </div>

              {ppExpandido && (
                <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {panPasado.map(pp => {
                    const ppCant = ppCantidades[pp.id] || 1
                    return (
                      <div key={pp.id} style={{
                        display: 'flex', alignItems: 'center', gap: '6px',
                        background: '#fff', borderRadius: '6px', padding: '5px 10px',
                        border: '1px solid #ffe0b2', cursor: 'pointer',
                      }} onClick={() => {
                        const prod = { id: pp.producto_id, nombre: pp.producto_nombre, precio: pp.precio_unitario, categoria: 'Pan de mesa' }
                        agregarAlCarrito(prod, pp.id)
                      }}>
                        <span style={{ fontWeight: 600, fontSize: '12px', color: '#333', flex: 1, minWidth: 0 }}>
                          🥖 {pp.producto_nombre}
                          <span style={{ fontSize: '10px', color: '#999', marginLeft: '4px' }}>({pp.disponible})</span>
                        </span>
                        <span style={{ fontSize: '11px', color: '#e65100', fontWeight: 600, whiteSpace: 'nowrap' }}>S/ {pp.precio_unitario.toFixed(2)}</span>
                        <span style={{ fontSize: '10px', color: '#999', fontStyle: 'italic' }}>+ Carrito</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          <div className="search-filter-row">
            <div className="search-wrapper">
              <span className="search-icon">🔍</span>
              <input className="search-bar" type="text" placeholder="Buscar producto..."
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="category-pills">
              {categorias.map(cat => (
                <button key={cat} className={`category-pill${catFilter === cat ? ' active' : ''}`}
                  onClick={() => setCatFilter(cat)}>
                  {cat === 'todas' ? 'Todas' : cat}
                </button>
              ))}
            </div>
          </div>

          {condiciones && (
            <div style={{
              padding: '8px 14px', borderRadius: '8px', marginBottom: '12px',
              background: condiciones.sugerir_mas_produccion ? 'linear-gradient(135deg, #e8f5e9, #c8e6c9)' : 'linear-gradient(135deg, #e3f2fd, #bbdefb)',
              border: `1px solid ${condiciones.sugerir_mas_produccion ? '#a5d6a7' : '#90caf9'}`,
              display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap',
            }}>
              <span style={{ fontSize: '18px' }}>{condiciones.es_finde || condiciones.es_feriado ? '📈' : condiciones.clima === 'Lluvia' ? '🌧️' : '🌤️'}</span>
              <span style={{ fontSize: '12px', color: '#555', flex: 1 }}>
                <strong>{condiciones.dia_semana}</strong> · {condiciones.clima} · {condiciones.hora}:00 hs · <strong>{condiciones.recomendacion}</strong>
              </span>
              {condiciones.sugerir_mas_produccion && (
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#2e7d32', background: '#e8f5e9', padding: '2px 10px', borderRadius: '12px' }}>
                  ⬆️ Sugerido aumentar producción
                </span>
              )}
            </div>
          )}

          {!todosProducidos && (
            <div className="card" style={{ borderLeft: '4px solid #e74c3c', padding: '12px 18px', marginBottom: '15px' }}>
              <p style={{ color: '#e74c3c', fontWeight: 600 }}>⚠️ Faltan productos por producir hoy</p>
              <p style={{ color: '#8892a4', fontSize: '13px' }}>Registra producción para todos los productos antes de vender.</p>
            </div>
          )}
          <div className="product-grid">
            {filtrados.map(p => {
              const stock = stockMap[p.id]
              const sinProduccion = stock && stock.producido === 0
              const sinStock = stock && stock.producido > 0 && stock.disponible === 0
              const deshabilitado = sinProduccion || sinStock
              return (
                <div key={p.id} className={`product-card${deshabilitado ? ' stock-low' : ''}`}
                  onClick={() => !deshabilitado && agregarAlCarrito(p)}>
                  <span className="product-card-emoji">{getEmoji(p.categoria)}</span>
                  <span className="product-card-nombre">{p.nombre}</span>
                  <span className="product-card-categoria">{p.categoria}</span>
                  <span className="product-card-precio">S/ {p.precio.toFixed(2)}</span>
                  {sinProduccion ? (
                    <span className="stock-badge sin-produccion">🚫 Sin producción hoy</span>
                  ) : stock ? (
                    <span className={`stock-badge ${stock.disponible > 0 ? 'disponible' : 'agotado'}`}>
                      🏭 {stock.producido} · ✅ {stock.vendido}
                      {stock.disponible > 0 ? ` · Disp: ${stock.disponible}` : condiciones?.sugerir_mas_produccion ? ' ⬆️ Sugerir +' : ''}
                    </span>
                  ) : (
                    <span className="stock-badge sin-stock">Sin registro</span>
                  )}
                </div>
              )
            })}
            {filtrados.length === 0 && (
              <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
                <p style={{ color: '#8892a4' }}>🔍 No se encontraron productos con ese filtro.</p>
              </div>
            )}
          </div>

          {ventasProductos.length > 0 && (
            <div className="card" style={{ marginTop: '15px' }}>
              <h3>Ventas de Hoy</h3>
          <button className="btn" onClick={() => descargarExcel('VentaRapidaPage', [{ key: "producto_nombre", label: "Producto" }, { key: "total_vendido", label: "Unidades" }, { key: "transacciones", label: "Trans." }, { key: "ingreso", label: "Ingreso" }], ventasProductos)} style={{ fontSize: '11px', padding: '3px 8px', background: '#27ae60', color: '#fff', marginLeft: '8px' }}>📊 Excel</button>
              <table>
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Unidades</th>
                    <th>Transacciones</th>
                    <th>Ingreso</th>
                  </tr>
                </thead>
                <tbody>
                  {ventasProductos.map(v => (
                    <tr key={v.producto_id}>
                      <td>{v.producto_nombre}</td>
                      <td>{v.total_vendido}</td>
                      <td>{v.transacciones}</td>
                      <td>S/ {v.ingreso.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="cart-panel-fixed">
          {ventasHoy && (
            <div className="day-summary">
              <div className="day-summary-item">
                <span>💰</span>
                <div>
                  <div className="ds-value">S/ {ingresoTotal.toFixed(2)}</div>
                  <div className="ds-label">Ingreso hoy</div>
                </div>
              </div>
              <div className="day-summary-item">
                <span>🧾</span>
                <div>
                  <div className="ds-value">{totalTransacciones}</div>
                  <div className="ds-label">Transacciones</div>
                </div>
              </div>
              <div className="day-summary-item">
                <span>📊</span>
                <div>
                  <div className="ds-value">S/ {ticketPromedio.toFixed(2)}</div>
                  <div className="ds-label">Ticket prom.</div>
                </div>
              </div>
            </div>
          )}
          <div className="cart-header">
            <span>🛒 Carrito ({itemsCount})</span>
          </div>
          <div className="cart-items">
            {cart.length === 0 ? (
              <div className="cart-empty">Selecciona un producto</div>
            ) : (
              cart.map(c => (
                <div key={c.cartKey} className="cart-item">
                  <span className="cart-item-emoji">{c.panPasadoId ? '🥖' : getEmoji(c.producto.categoria)}</span>
                  <div className="cart-item-info">
                    <span className="cart-item-name">
                      {c.producto.nombre}
                      {c.panPasadoId && <span style={{ fontSize: '10px', color: '#e65100', marginLeft: '4px' }}>Pan anterior</span>}
                    </span>
                    <span className="cart-item-price">S/ {c.producto.precio.toFixed(2)}</span>
                  </div>
                  <div className="cart-item-controls">
                    <button className="cart-item-btn" onClick={() => actualizarCantidad(c.cartKey, c.cantidad - 1)}>−</button>
                    <span className="cart-item-qty">{c.cantidad}</span>
                    <button className="cart-item-btn" onClick={() => actualizarCantidad(c.cartKey, c.cantidad + 1)}>+</button>
                  </div>
                  <span className="cart-item-subtotal">S/ {(c.producto.precio * c.cantidad).toFixed(2)}</span>
                  <button className="cart-item-remove" onClick={() => eliminarDelCarrito(c.cartKey)}>✕</button>
                </div>
              ))
            )}
          </div>
          <div className="cart-footer">
            <div className="payment-methods">
              {Object.entries(PAYMENT_EMOJIS).map(([key, emoji]) => (
                <button key={key} className={`payment-btn${metodoPago === key ? ' active' : ''}`}
                  onClick={() => setMetodoPago(key)}>
                  {emoji} {key.charAt(0).toUpperCase() + key.slice(1)}
                </button>
              ))}
            </div>
            <div className="cart-total">
              <span>Total</span>
              <span>S/ {totalCarrito.toFixed(2)}</span>
            </div>
            <button
              className="btn btn-primary btn-block"
              onClick={mostrarFactura}
              disabled={!puedeRegistrar}
            >
              Registrar Venta
            </button>
          </div>
        </div>
      </div>

      {invoiceModal && (
        <div className="invoice-modal-overlay" onClick={() => setInvoiceModal(null)}>
          <div className="invoice-modal-content" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setInvoiceModal(null)}>✕</button>
            <h2>🧾 Vista Previa de Factura</h2>

            <div className="invoice-preview">
              <div className="inv-header">
                <div className="inv-logo">🥖</div>
                <div>
                  <div className="inv-business">PANADERÍA VICTORIA</div>
                  <div className="inv-ruc">RUC: 10456789012</div>
                  <div className="inv-addr">Av. Principal 123 - Pacasmayo</div>
                </div>
              </div>

              <div className="inv-divider"></div>

              <div className="inv-title">BOLETA DE VENTA ELECTRÓNICA</div>
              <div className="inv-number">{invoiceModal.numero}</div>

              <div className="inv-divider"></div>

              <div className="inv-info">
                <span>FECHA: {invoiceModal.fecha}</span>
                <span>HORA: {invoiceModal.hora}</span>
              </div>
              <div className="inv-info">
                <span>PAGO: {PAYMENT_EMOJIS[invoiceModal.metodo_pago] || '💵'} {invoiceModal.metodo_pago?.toUpperCase() || 'EFECTIVO'}</span>
              </div>
              {invoiceModal.vendedor_nombre && (
                <div className="inv-info">VENDEDOR: {invoiceModal.vendedor_nombre.toUpperCase()}{invoiceModal.vendedor_dni ? ` / DNI ${invoiceModal.vendedor_dni}` : ''}</div>
              )}

              <div className="inv-divider-solid"></div>

              <table className="inv-table">
                <thead>
                  <tr>
                    <th className="right">CANT.</th>
                    <th>DESCRIPCIÓN</th>
                    <th className="right">P.UNIT</th>
                    <th className="right">TOTAL</th>
                  </tr>
                </thead>
                <tbody>
                  {invoiceModal.items.map((c, i) => (
                    <tr key={i}>
                      <td className="right">{c.cantidad.toFixed(2)}</td>
                      <td>{c.producto.nombre.toUpperCase()}</td>
                      <td className="right">{c.producto.precio.toFixed(2)}</td>
                      <td className="right">{(c.producto.precio * c.cantidad).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="inv-divider-solid"></div>

              <table className="inv-totales">
                <tbody>
                  <tr><td>OP. GRAVADAS</td><td className="right">S/ {invoiceModal.subtotal.toFixed(2)}</td></tr>
                  <tr><td>IGV (18%)</td><td className="right">S/ {invoiceModal.igv.toFixed(2)}</td></tr>
                  <tr><td colSpan="2"><div className="inv-divider"></div></td></tr>
                  <tr className="inv-total-row">
                    <td>TOTAL</td>
                    <td className="right">S/ {invoiceModal.total.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="invoice-actions">
              <button className="btn btn-primary" onClick={imprimirFactura}>
                🖨️ Imprimir Factura
              </button>
              <button className="btn btn-primary" onClick={ejecutarVenta}>
                ✅ Confirmar Venta
              </button>
              <button className="btn btn-danger" onClick={() => setInvoiceModal(null)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {showToast}
    </>
  )
}
