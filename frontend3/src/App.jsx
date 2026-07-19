import { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext'
import { NavProvider } from './context/NavContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import VentaRapidaPage from './pages/VentaRapidaPage'
import RegistroDiarioPage from './pages/RegistroDiarioPage'
import CatalogoPage from './pages/CatalogoPage'
import InventarioPage from './pages/InventarioPage'
import PrediccionesPage from './pages/PrediccionesPage'
import ControlPerdidasPage from './pages/ControlPerdidasPage'
import VendedoresPage from './pages/VendedoresPage'
import OrdenesCompraPage from './pages/OrdenesCompraPage'
import ProveedoresPage from './pages/ProveedoresPage'
import ReportesFinancierosPage from './pages/ReportesFinancierosPage'
import ModeloEstadisticoPage from './pages/ModeloEstadisticoPage'
import AnomaliasPage from './pages/AnomaliasPage'
import PodiosPage from './pages/PodiosPage'
import NotificacionesPage from './pages/NotificacionesPage'

import SecurityPage from './pages/SecurityPage'
import './App.css'

function App() {
  const { user, debeConfigurar2fa } = useAuth()
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem('currentPage')
    return debeConfigurar2fa ? 'seguridad' : saved || 'dashboard'
  })
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark'
  })

  const PAGE_ROLES = {
    dashboard: ['administrador','gerente','vendedor','cocina'],
    venta_rapida: ['administrador','gerente','vendedor'],
    registro_diario: ['administrador','gerente','cocina'],
    catalogo: ['administrador','gerente','vendedor','cocina'],
    inventario: ['administrador','gerente','vendedor','cocina'],
    vendedores: ['administrador','gerente'],
    ordenes_compra: ['administrador','gerente'],
    proveedores: ['administrador','gerente'],

    predicciones: ['administrador','gerente'],
    control_perdidas: ['administrador','gerente'],
    reportes_financieros: ['administrador','gerente'],
    modelo_estadistico: ['administrador','gerente'],
    anomalias: ['administrador'],
    podios: ['administrador','gerente','vendedor'],
    notificaciones: ['administrador'],
    seguridad: ['administrador','gerente','vendedor','cocina'],
  }

  const handleNavigate = (page) => {
    const allowed = PAGE_ROLES[page]
    if (allowed && !allowed.includes(user.rol)) return
    setCurrentPage(page)
    localStorage.setItem('currentPage', page)
  }

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode)
    localStorage.setItem('theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  useEffect(() => {
    localStorage.setItem('currentPage', currentPage)
  }, [currentPage])

  // Forzar a configuración 2FA si es necesario
  useEffect(() => {
    if (debeConfigurar2fa && currentPage !== 'seguridad') {
      setCurrentPage('seguridad')
    }
  }, [debeConfigurar2fa, currentPage])

  if (!user) {
    return <LoginPage />
  }

  const renderPage = () => {
    const allowed = PAGE_ROLES[currentPage]
    if (allowed && !allowed.includes(user.rol)) return <DashboardPage />
    switch (currentPage) {
      case 'dashboard': return <DashboardPage />
      case 'venta_rapida': return <VentaRapidaPage />
      case 'registro_diario': return <RegistroDiarioPage />
      case 'catalogo': return <CatalogoPage />
      case 'inventario': return <InventarioPage />
      case 'vendedores': return <VendedoresPage />
      case 'predicciones': return <PrediccionesPage />
      case 'control_perdidas': return <ControlPerdidasPage />
      case 'ordenes_compra': return <OrdenesCompraPage />
      case 'proveedores': return <ProveedoresPage />
      case 'reportes_financieros': return <ReportesFinancierosPage />
      case 'modelo_estadistico': return <ModeloEstadisticoPage />
      case 'anomalias': return <AnomaliasPage />
      case 'podios': return <PodiosPage />
      case 'notificaciones': return <NotificacionesPage />
      case 'seguridad': return <SecurityPage />
      default: return currentPage === 'seguridad' ? <SecurityPage /> : <DashboardPage />
    }
  }

  return (
    <NavProvider navigate={handleNavigate}>
      <Layout
        currentPage={currentPage}
        setCurrentPage={handleNavigate}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
      >
        <div className="fade-in">
          {renderPage()}
        </div>
      </Layout>
    </NavProvider>
  )
}

export default App
