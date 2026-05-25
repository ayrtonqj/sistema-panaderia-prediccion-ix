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
    <text x="70" y="54" fontFamily="Poppins, Arial" fontSize="13" fontWeight="500" fill="#764ba2" letterSpacing="3">PANADERÍA</text>
  </svg>
)

const MENU_SECTIONS = [
  {
    title: 'Operación Diaria',
    items: [
      { key: 'dashboard',        icon: '🏠', label: 'Dashboard',       roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'venta_rapida',    icon: '⚡', label: 'Venta Rápida',    roles: ['administrador','gerente','vendedor'] },
      { key: 'registro_diario', icon: '📝', label: 'Registro Diario', roles: ['administrador','gerente','cocina'] },
    ],
  },
  {
    title: 'Gestión',
    items: [
      { key: 'catalogo',       icon: '📦', label: 'Catálogo',          roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'inventario',     icon: '🏪', label: 'Inventario',        roles: ['administrador','gerente','vendedor','cocina'] },
      { key: 'vendedores',     icon: '👥', label: 'Vendedores',        roles: ['administrador','gerente'] },
      { key: 'ordenes_compra', icon: '🛒', label: 'Órdenes de Compra', roles: ['administrador','gerente'] },
    ],
  },
  {
    title: 'Análisis',
    items: [
      { key: 'predicciones',         icon: '🔮', label: 'Predicciones',          roles: ['administrador','gerente'] },
      { key: 'control_perdidas',     icon: '📊', label: 'Control de Pérdidas',   roles: ['administrador','gerente'] },
      { key: 'reportes_financieros', icon: '💰', label: 'Reportes Financieros',  roles: ['administrador','gerente'] },
    ],
  },
]

const ADMIN_SECTION = {
  title: 'Sistema',
  items: [
    { key: 'modelo_estadistico', icon: '📈', label: 'Estadísticas del Modelo', roles: ['administrador'] },
    { key: 'seguridad', icon: '🔐', label: 'Seguridad', roles: ['administrador','gerente','vendedor','cocina'] },
  ],
}

export default function Sidebar({ currentPage, setCurrentPage, darkMode, setDarkMode }) {
  const { user, logout } = useAuth()

  return (
    <div className="sidebar">
      <div className="sidebar-logo" onClick={() => setCurrentPage('dashboard')}>
        {LOGO_SVG}
      </div>

      {MENU_SECTIONS.map(section => {
        const visibleItems = section.items.filter(m => m.roles.includes(user.rol))
        if (visibleItems.length === 0) return null
        return (
          <div className="menu-section" key={section.title}>
            <h3>{section.title}</h3>
            {visibleItems.map(item => (
              <div
                key={item.key}
                className={`menu-item${currentPage === item.key ? ' active' : ''}`}
                onClick={() => setCurrentPage(item.key)}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )
      })}

      {(() => {
        const adminVisible = ADMIN_SECTION.items.filter(m => m.roles.includes(user.rol))
        if (adminVisible.length === 0) return null
        return (
          <div className="menu-section">
            <h3>{ADMIN_SECTION.title}</h3>
            {adminVisible.map(item => (
              <div
                key={item.key}
                className={`menu-item${currentPage === item.key ? ' active' : ''}`}
                onClick={() => setCurrentPage(item.key)}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )
      })()}

      <div className="user-profile">
        <div className="user-info">
          <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
          <div className="user-details">
            <div className="user-name">{user.username}</div>
            <div className={`user-role ${user.rol}`}>{user.rol}</div>
          </div>
        </div>
        <div className="profile-actions">
          <button className="theme-toggle" onClick={() => setDarkMode(d => !d)} title="Cambiar tema">
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button className="btn-logout" onClick={logout} title="Cerrar sesión">⏻</button>
        </div>
      </div>
    </div>
  )
}
