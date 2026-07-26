import { useState, useEffect } from 'react'
import { api } from '../api/api'

export default function PodiosPage() {
  const [podios, setPodios] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [periodo, setPeriodo] = useState('mes')

  const fetchPodios = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.get(`/dashboard/podios?periodo=${periodo}`)
      setPodios(data)
    } catch (e) {
      setError(e.message || 'Error al cargar los podios')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPodios() }, [periodo])

  const medalBadge = (idx) => {
    if (idx === 0) return { emoji: '🥇', bg: 'linear-gradient(135deg, #fef08a 0%, #fde047 100%)', text: '#854d0e', border: '#facc15' }
    if (idx === 1) return { emoji: '🥈', bg: 'linear-gradient(135deg, #f4f4f5 0%, #e4e4e7 100%)', text: '#3f3f46', border: '#d4d4d8' }
    if (idx === 2) return { emoji: '🥉', bg: 'linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)', text: '#9a3412', border: '#fb923c' }
    return { emoji: `#${idx + 1}`, bg: '#f1f5f9', text: '#64748b', border: '#cbd5e1' }
  }

  const formatValor = (item, campoValor, unidad) => {
    const val = item[campoValor] ?? item.total_vendido ?? item.total_ventas ?? item.cantidad_merma ?? item.margen ?? item.total_consumo
    if (typeof val === 'number') {
      const formatted = val.toLocaleString('es-PE', { minimumFractionDigits: unidad === 'S/' ? 2 : 0, maximumFractionDigits: 2 })
      return unidad === 'S/' ? `S/ ${formatted}` : `${formatted} ${unidad}`.trim()
    }
    return val || '-'
  }

  const renderCardSection = (titulo, icono, lista, campoNombre, campoValor, unidad = '', subtitulo = '') => {
    const itemsList = Array.isArray(lista) ? lista : []
    return (
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <div style={styles.cardTitleBox}>
            <span style={styles.cardIcon}>{icono}</span>
            <div>
              <h3 style={styles.cardTitle}>{titulo}</h3>
              {subtitulo && <span style={styles.cardSub}>{subtitulo}</span>}
            </div>
          </div>
          <span style={styles.itemCountBadge}>{itemsList.length} items</span>
        </div>

        {itemsList.length === 0 ? (
          <div style={styles.emptyCard}>
            <span>📊</span>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
              Sin datos registrados para este período.
            </p>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Prueba seleccionando <b>Semana</b> o <b>Mes</b>.</span>
          </div>
        ) : (
          <div style={styles.itemsList}>
            {itemsList.slice(0, 7).map((item, i) => {
              const badge = medalBadge(i)
              const nombre = item[campoNombre] || item.nombre || item.producto || item.vendedor || '-'
              const valorFormateado = formatValor(item, campoValor, unidad)
              return (
                <div key={i} style={{ ...styles.rowItem, borderLeft: `4px solid ${badge.border}` }}>
                  <div style={{ ...styles.medalPill, background: badge.bg, color: badge.text }}>
                    {badge.emoji}
                  </div>
                  <div style={styles.nameCol}>
                    <span style={styles.itemName}>{nombre}</span>
                    {item.transacciones !== undefined && (
                      <span style={styles.subDetail}>{item.transacciones} transacciones</span>
                    )}
                    {item.costo_merma !== undefined && (
                      <span style={styles.subDetail}>Pérdida est: S/ {Number(item.costo_merma).toFixed(2)}</span>
                    )}
                  </div>
                  <div style={styles.valueCol}>
                    <span style={{ ...styles.valueText, color: i === 0 ? '#1e293b' : '#334155' }}>
                      {valorFormateado}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="page-container" style={{ paddingBottom: '40px' }}>
      {/* Header Banner */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '700', color: '#1e293b' }}>
            🏆 Podios y Rankings
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#64748b' }}>
            Métricas de liderazgo en ventas, rendimiento de personal, margen y control de pérdidas.
          </p>
        </div>

        {/* Period Selector Tabs */}
        <div style={styles.periodTabs}>
          {[
            { value: 'dia', label: 'Hoy' },
            { value: 'semana', label: 'Semana (7d)' },
            { value: 'mes', label: 'Mes (30d)' },
            { value: 'anio', label: 'Año (365d)' },
          ].map(p => (
            <button
              key={p.value}
              style={{
                ...styles.tabBtn,
                ...(periodo === p.value ? styles.tabBtnActive : {}),
              }}
              onClick={() => setPeriodo(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div style={styles.centerLoading}>
          <div style={styles.spinner}></div>
          <p style={{ marginTop: '12px', color: '#64748b', fontSize: '14px' }}>Calculando podios y rankings...</p>
        </div>
      )}

      {error && (
        <div style={styles.errorBanner}>
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && podios && (
        <div style={styles.gridContainer}>
          {renderCardSection(
            'Productos Más Vendidos',
            '🍞',
            podios.productos_mas_vendidos || podios.productos_top,
            'nombre',
            'total_uds',
            'uds',
            'Volumen de ventas acumuladas'
          )}

          {renderCardSection(
            'Mejores Vendedores',
            '👤',
            podios.vendedores_top,
            'nombre',
            'total_ventas',
            'S/',
            'Ingresos generados en caja'
          )}

          {renderCardSection(
            'Mayor Registro de Mermas',
            '📉',
            podios.mas_mermas || podios.mermas_top,
            'nombre',
            'cantidad_merma',
            'uds',
            'Desperdicio físico acumulado'
          )}

          {renderCardSection(
            'Mayor Margen de Ganancia',
            '💰',
            podios.productos_mayor_margen,
            'nombre',
            'margen',
            'S/',
            'Diferencia entre precio y costo'
          )}

          {renderCardSection(
            'Insumos Más Consumidos',
            '🧪',
            podios.insumos_mas_usados,
            'nombre',
            'total_consumo',
            '',
            'Consumo estimado en recetas'
          )}
        </div>
      )}
    </div>
  )
}

const styles = {
  periodTabs: {
    display: 'inline-flex',
    background: '#f1f5f9',
    padding: '4px',
    borderRadius: '14px',
    gap: '4px',
    border: '1px solid #e2e8f0',
  },
  tabBtn: {
    border: 'none',
    background: 'transparent',
    padding: '8px 16px',
    borderRadius: '10px',
    fontSize: '13px',
    fontWeight: '600',
    color: '#64748b',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  tabBtnActive: {
    background: '#ffffff',
    color: '#4f46e5',
    boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
  },
  gridContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '20px',
  },
  card: {
    background: '#ffffff',
    borderRadius: '18px',
    padding: '20px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 4px 15px rgba(0,0,0,0.03)',
    display: 'flex',
    flexDirection: 'column',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    paddingBottom: '12px',
    borderBottom: '1px solid #f1f5f9',
  },
  cardTitleBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  cardIcon: {
    fontSize: '22px',
  },
  cardTitle: {
    margin: 0,
    fontSize: '16px',
    fontWeight: '700',
    color: '#1e293b',
  },
  cardSub: {
    fontSize: '11px',
    color: '#94a3b8',
  },
  itemCountBadge: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#64748b',
    background: '#f8fafc',
    padding: '4px 10px',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
  },
  emptyCard: {
    textAlign: 'center',
    padding: '24px 12px',
    background: '#f8fafc',
    borderRadius: '12px',
    border: '1px dashed #cbd5e1',
  },
  itemsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  rowItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 14px',
    background: '#f8fafc',
    borderRadius: '12px',
    transition: 'transform 0.15s ease',
  },
  medalPill: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    fontWeight: '700',
    flexShrink: 0,
  },
  nameCol: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  itemName: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#1e293b',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  subDetail: {
    fontSize: '11px',
    color: '#64748b',
  },
  valueCol: {
    textAlign: 'right',
    flexShrink: 0,
  },
  valueText: {
    fontSize: '14px',
    fontWeight: '700',
  },
  centerLoading: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  spinner: {
    width: '36px',
    height: '36px',
    border: '4px solid #e2e8f0',
    borderTopColor: '#6366f1',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto',
  },
  errorBanner: {
    padding: '16px',
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '12px',
    color: '#dc2626',
    fontSize: '14px',
  },
}

