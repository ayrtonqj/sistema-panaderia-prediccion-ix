import { useState, useEffect } from 'react'
import { formatDateFull, formatTime } from '../utils/formatters'
import Sidebar from './Sidebar'
import ChatbotWidget from './ChatbotWidget'

export default function Layout({ children, currentPage, setCurrentPage, darkMode, setDarkMode }) {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="app-layout">
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
      />
      <main className="main-content">
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
