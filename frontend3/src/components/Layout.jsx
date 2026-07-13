import { useState, useEffect } from 'react'
import { formatDateFull, formatTime } from '../utils/formatters'
import Sidebar from './Sidebar'
import ChatbotWidget from './ChatbotWidget'

const STORAGE_KEY_COLLAPSED = 'sidebarCollapsed'
const STORAGE_KEY_VISIBLE = 'sidebarVisible'

function loadBool(key, fallback) {
  try {
    const v = localStorage.getItem(key)
    if (v === null) return fallback
    return v === 'true'
  } catch { return fallback }
}

function saveBool(key, value) {
  try { localStorage.setItem(key, value ? 'true' : 'false') } catch {}
}

export default function Layout({ children, currentPage, setCurrentPage, darkMode, setDarkMode }) {
  const [now, setNow] = useState(new Date())
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => loadBool(STORAGE_KEY_COLLAPSED, false))
  const [sidebarVisible, setSidebarVisible] = useState(() => loadBool(STORAGE_KEY_VISIBLE, true))
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => { saveBool(STORAGE_KEY_COLLAPSED, sidebarCollapsed) }, [sidebarCollapsed])
  useEffect(() => { saveBool(STORAGE_KEY_VISIBLE, sidebarVisible) }, [sidebarVisible])

  const toggleCollapse = () => setSidebarCollapsed(prev => !prev)
  const toggleSidebar = () => setSidebarVisible(prev => !prev)
  const toggleMobileMenu = () => setMobileMenuOpen(prev => !prev)

  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768
  const showSidebar = sidebarVisible
  const sidebarClass = isMobile
    ? `sidebar${mobileMenuOpen ? ' open' : ''}${sidebarCollapsed ? ' collapsed' : ''}`
    : `sidebar${sidebarCollapsed ? ' collapsed' : ''}`

  return (
    <div className={`app-layout${!sidebarVisible ? ' sidebar-hidden' : ''}${sidebarCollapsed ? ' sidebar-collapsed' : ''}`}>
      {isMobile && <div className={`sidebar-overlay${mobileMenuOpen ? ' visible' : ''}`} onClick={() => setMobileMenuOpen(false)} />}

      <Sidebar
        currentPage={currentPage}
        setCurrentPage={(key) => { setCurrentPage(key); if (isMobile) setMobileMenuOpen(false) }}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        collapsed={isMobile ? false : sidebarCollapsed}
        onToggle={toggleCollapse}
        className={sidebarClass}
      />

      {!isMobile && showSidebar && (
        <button
          className="sidebar-edge-toggle"
          style={{ left: sidebarCollapsed ? '72px' : '260px' }}
          onClick={toggleCollapse}
          title={sidebarCollapsed ? 'Expandir menu' : 'Colapsar menu'}
        >
          {sidebarCollapsed ? '▶' : '◀'}
        </button>
      )}

      {isMobile && (
        <button className="sidebar-float-btn" onClick={toggleMobileMenu} title="Menu">
          &#9776;
        </button>
      )}

      {!isMobile && !showSidebar && (
        <button className="sidebar-float-btn" onClick={toggleSidebar} title="Mostrar menu">
          &#9776;
        </button>
      )}

      <main className={`main-content${!sidebarVisible && !isMobile ? ' full-width' : ''}${sidebarCollapsed && !isMobile ? ' expanded' : ''}`}>
        <div className="global-topbar">
          <div className="datetime-badge">
            <span className="date-icon">📅</span>
            <span className="date-text">{formatDateFull(now)}</span>
            <span className="date-sep">·</span>
            <span className="time-text">{formatTime(now)}</span>
          </div>
        </div>
        {children}
      </main>
      <ChatbotWidget />
    </div>
  )
}
