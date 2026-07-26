import { useState, useEffect } from 'react'

export default function DemoLoadingScreen({ elapsed, attempts, error, onRetry, onManualLogin }) {
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    if (mins > 0) {
      return `${mins}m ${secs < 10 ? '0' : ''}${secs}s`
    }
    return `${secs}s`
  }

  const isColdStart = elapsed >= 10

  return (
    <div style={styles.overlay}>
      <div style={styles.card}>
        {/* Logo & Header */}
        <div style={styles.header}>
          <div style={styles.logoBadge}>
            <span style={styles.logoIcon}>🍞</span>
          </div>
          <h2 style={styles.title}>Panadería Victoria</h2>
          <div style={styles.demoBadge}>
            <span style={styles.pulseDot}></span>
            MODO DEMO ACTIVADO
          </div>
        </div>

        {/* Status Indicator */}
        <div style={styles.spinnerContainer}>
          <div style={styles.spinnerRing}></div>
          <div style={styles.spinnerIcon}>⚡</div>
        </div>

        {/* Main Status Text */}
        <h3 style={styles.statusText}>
          {isColdStart ? 'Despertando el servidor backend...' : 'Iniciando sesión automáticamente...'}
        </h3>

        <p style={styles.statusSubtext}>
          {isColdStart
            ? 'El servidor alojado en Render está saliendo del estado de reposo (cold start). La primera conexión puede tardar entre 1 y 2 minutos.'
            : 'Conectando con el servidor backend como Administrador...'}
        </p>

        {/* Progress Bar */}
        <div style={styles.progressBarBg}>
          <div style={styles.progressBarFill}></div>
        </div>

        {/* Live Metrics Pills */}
        <div style={styles.pillsContainer}>
          <div style={styles.pill}>
            <span style={styles.pillLabel}>⏱️ Tiempo:</span>
            <span style={styles.pillValue}>{formatTime(elapsed)}</span>
          </div>
          <div style={styles.pill}>
            <span style={styles.pillLabel}>🔄 Intentos:</span>
            <span style={styles.pillValue}>#{attempts}</span>
          </div>
          <div style={styles.pill}>
            <span style={styles.pillLabel}>👤 Rol:</span>
            <span style={styles.pillValue}>Administrador</span>
          </div>
        </div>

        {error && (
          <div style={styles.errorBanner}>
            ⚠️ {error}
          </div>
        )}

        {/* Action Buttons */}
        <div style={styles.actions}>
          <button style={styles.btnSecondary} onClick={onRetry}>
            🔄 Reintentar conexión
          </button>
          <button style={styles.btnLink} onClick={onManualLogin}>
            Ingresar manualmente
          </button>
        </div>
      </div>

      {/* Embedded Styles */}
      <style>{`
        @keyframes demoPulse {
          0% { transform: scale(0.95); opacity: 0.8; }
          50% { transform: scale(1.05); opacity: 1; }
          100% { transform: scale(0.95); opacity: 0.8; }
        }
        @keyframes demoSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes demoShimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes demoDotPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}

const styles = {
  overlay: {
    minHeight: '100vh',
    width: '100vw',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%)',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    padding: '20px',
    boxSizing: 'border-box',
    color: '#f8fafc',
  },
  card: {
    background: 'rgba(30, 41, 59, 0.75)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '24px',
    padding: '40px 36px',
    maxWidth: '480px',
    width: '100%',
    textAlign: 'center',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 30px rgba(99, 102, 241, 0.15)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '28px',
  },
  logoBadge: {
    width: '64px',
    height: '64px',
    borderRadius: '18px',
    background: 'linear-gradient(135deg, #d4a574 0%, #b8845c 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 8px 20px rgba(184, 132, 92, 0.3)',
    marginBottom: '4px',
  },
  logoIcon: {
    fontSize: '32px',
  },
  title: {
    margin: 0,
    fontSize: '22px',
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: '0.5px',
  },
  demoBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 14px',
    borderRadius: '20px',
    background: 'rgba(99, 102, 241, 0.2)',
    border: '1px solid rgba(129, 140, 248, 0.3)',
    color: '#a5b4fc',
    fontSize: '12px',
    fontWeight: '700',
    letterSpacing: '1px',
  },
  pulseDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#34d399',
    boxShadow: '0 0 8px #34d399',
    animation: 'demoDotPulse 1.5s infinite',
  },
  spinnerContainer: {
    position: 'relative',
    width: '80px',
    height: '80px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '24px',
  },
  spinnerRing: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    border: '4px solid rgba(255, 255, 255, 0.1)',
    borderTopColor: '#818cf8',
    borderRightColor: '#c084fc',
    animation: 'demoSpin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite',
  },
  spinnerIcon: {
    fontSize: '28px',
    animation: 'demoPulse 2s ease-in-out infinite',
  },
  statusText: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: '600',
    color: '#f1f5f9',
  },
  statusSubtext: {
    margin: '0 0 24px 0',
    fontSize: '13px',
    lineHeight: '1.6',
    color: '#94a3b8',
    maxWidth: '380px',
  },
  progressBarBg: {
    width: '100%',
    height: '6px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '3px',
    overflow: 'hidden',
    marginBottom: '24px',
  },
  progressBarFill: {
    height: '100%',
    width: '100%',
    background: 'linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #6366f1 100%)',
    backgroundSize: '200% 100%',
    animation: 'demoShimmer 2s linear infinite',
  },
  pillsContainer: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
    justifyContent: 'center',
    width: '100%',
    marginBottom: '24px',
  },
  pill: {
    background: 'rgba(15, 23, 42, 0.6)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '8px 14px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
  },
  pillLabel: {
    color: '#94a3b8',
  },
  pillValue: {
    color: '#f8fafc',
    fontWeight: '600',
  },
  errorBanner: {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '10px',
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    color: '#fca5a5',
    fontSize: '12px',
    marginBottom: '20px',
    boxSizing: 'border-box',
  },
  actions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    width: '100%',
  },
  btnSecondary: {
    width: '100%',
    padding: '12px',
    borderRadius: '12px',
    border: '1px solid rgba(129, 140, 248, 0.4)',
    background: 'rgba(99, 102, 241, 0.15)',
    color: '#818cf8',
    fontWeight: '600',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  btnLink: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    fontSize: '13px',
    cursor: 'pointer',
    textDecoration: 'underline',
    padding: '6px',
  },
}
