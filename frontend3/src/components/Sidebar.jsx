import { useState, useRef } from 'react'
import { useAuth } from '../context/AuthContext'

const LOGO_SVG = (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 70" width="210" height="62">
    <defs>
      <linearGradient id="panGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#d4a574"/>
        <stop offset="50%" stopColor="#c9956c"/>
        <stop offset="100%" stopColor="#b8845c"/>
      </linearGradient>
    </defs>
    <rect x="5" y="8" width="55" height="55" rx="12" fill="url(#panGradient)"/>
    <ellipse cx="32" cy="38" rx="20" ry="16" fill="#e8c9a0"/>
    <ellipse cx="32" cy="35" rx="17" ry="13" fill="#f5deb3"/>
    <path d="M20 32 Q32 24 44 32" stroke="#c9956c" strokeWidth="2" fill="none"/>
    <path d="M22 38 Q32 30 42 38" stroke="#c9956c" strokeWidth="2" fill="none"/>
    <path d="M24 44 Q32 36 40 44" stroke="#c9956c" strokeWidth="2" fill="none"/>
    <ellipse cx="26" cy="30" rx="4" ry="3" fill="#fff5e6" opacity="0.7"/>
    <text x="70" y="34" fontFamily="Poppins, Arial" fontSize="18" fontWeight="700" fill="#667eea" letterSpacing="2">VICTORIA</text>
    <text x="70" y="54" fontFamily="Poppins, Arial" fontSize="13" fontWeight="500" fill="#764ba2" letterSpacing="3">PANADERIA</text>
  </svg>
)

const LOGO_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 70 70" width="38" height="38">
    <defs>
      <linearGradient id="panGradient2" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#d4a574"/>
        <stop offset="50%" stopColor="#c9956c"/>
        <stop offset="100%" stopColor="#b8845c"/>
      </linearGradient>
    </defs>
    <rect x="5" y="8" width="60" height="55" rx="12" fill="url(#panGradient2)"/>
    <ellipse cx="35" cy="38" rx="22" ry="16" fill="#e8c9a0"/>
    <ellipse cx="35" cy="35" rx="19" ry="13" fill="#f5deb3"/>
    <path d="M22 32 Q35 24 48 32" stroke="#c9956c" strokeWidth="2" fill="none"/>
    <path d="M24 38 Q35 30 46 38" stroke="#c9956c" strokeWidth="2" fill="none"/>
    <path d="M26 44 Q35 36 44 44" stroke="#c9956c" strokeWidth="2" fill="none"/>
  </svg>
)

const MENU_SECTIONS = [
  {
    title: 'Operacion Diaria',
    items: [
      { key: 'dashboard',        icon: '🏠', label: 'Dashboard',       roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'venta_rapida',    icon: '⚡', label: 'Venta Rapida',    roles: ['administrador','gerente','vendedor'] },
      { key: 'registro_diario', icon: '📝', label: 'Registro Diario', roles: ['administrador','gerente','cocina'] },
    ],
  },
  {
    title: 'Gestion',
    items: [
      { key: 'catalogo',       icon: '📦', label: 'Catalogo',          roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'inventario',     icon: '🏪', label: 'Inventario',        roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'proveedores',    icon: '🤝', label: 'Proveedores',       roles: ['administrador','gerente'] },
      { key: 'vendedores',     icon: '👥', label: 'Vendedores',        roles: ['administrador','gerente'] },
      { key: 'ordenes_compra', icon: '🛒', label: 'Ordenes de Compra', roles: ['administrador','gerente'] },
    ],
  },
  {
    title: 'Analisis',
    items: [
      { key: 'predicciones',         icon: '🔮', label: 'Predicciones',          roles: ['administrador','gerente'] },
      { key: 'control_perdidas',     icon: '📊', label: 'Control de Perdidas',   roles: ['administrador','gerente'] },
      { key: 'reportes_financieros', icon: '💰', label: 'Reportes Financieros',  roles: ['administrador','gerente'] },
      { key: 'anomalias',            icon: '🔍', label: 'Anomalias',             roles: ['administrador','gerente'] },
      { key: 'podios',               icon: '🏆', label: 'Podios',                roles: ['administrador','gerente','vendedor'] },
    ],
  },
]

const ADMIN_SECTION = {
  title: 'Sistema',
  items: [
    { key: 'modelo_estadistico', icon: '📈', label: 'Estadisticas del Modelo', roles: ['administrador'] },
    { key: 'notificaciones', icon: '🔔', label: 'Notificaciones', roles: ['administrador','gerente'] },
    { key: 'seguridad', icon: '🔐', label: 'Seguridad', roles: ['administrador','gerente','vendedor','cocina'] },
  ],
}

export default function Sidebar({ currentPage, setCurrentPage, darkMode, setDarkMode, collapsed, onToggle, className }) {
  const { user, logout } = useAuth()
  const [hoveredSection, setHoveredSection] = useState(null)
  const hoverTimerRef = useRef(null)

  const handleSectionEnter = (title) => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    setHoveredSection(title)
  }

  const handleSectionLeave = () => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    hoverTimerRef.current = setTimeout(() => {
      setHoveredSection(null)
    }, 300)
  }

  const allSections = [...MENU_SECTIONS, ADMIN_SECTION]

  return (
    <div className={className || `sidebar${collapsed ? ' collapsed' : ''}`}>
      <div className="sidebar-logo" onClick={() => setCurrentPage('dashboard')}>
        {collapsed ? LOGO_ICON : LOGO_SVG}
      </div>

      {allSections.map(section => {
        const visibleItems = section.items.filter(m => m.roles.includes(user.rol))
        if (visibleItems.length === 0) return null
        const isExpanded = collapsed || hoveredSection === section.title
        return (
          <div
            className="menu-section"
            key={section.title}
            onMouseEnter={() => handleSectionEnter(section.title)}
            onMouseLeave={handleSectionLeave}
          >
            {!collapsed && (
              <h3 className="section-header">
                <span className={`section-chevron${isExpanded ? ' open' : ''}`}>▸</span>
                {section.title}
              </h3>
            )}
            {isExpanded && visibleItems.map(item => (
              <div
                key={item.key}
                className={`menu-item${currentPage === item.key ? ' active' : ''}`}
                onClick={() => setCurrentPage(item.key)}
                title={collapsed ? item.label : undefined}
              >
                <span className="menu-icon">{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </div>
            ))}
          </div>
        )
      })}

      <div className="user-profile">
        <div className="user-info">
          <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
          {!collapsed && (
            <div className="user-details">
              <div className="user-name">{user.username}</div>
              <div className={`user-role ${user.rol}`}>{user.rol}</div>
            </div>
          )}
        </div>
        <div className="profile-actions">
          {!collapsed && (
            <button className="theme-toggle" onClick={() => setDarkMode(d => !d)} title="Cambiar tema">
              {darkMode ? '☀️' : '🌙'}
            </button>
          )}
          <button className="btn-logout" onClick={logout} title="Cerrar sesion">⏻</button>
        </div>
      </div>
    </div>
  )
}
