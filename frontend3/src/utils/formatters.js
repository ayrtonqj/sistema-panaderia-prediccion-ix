const LOCALE = 'es-PE'
const DAYS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

export function parseDate(d) {
  if (!d) return null
  if (d instanceof Date && !isNaN(d)) return d
  if (typeof d === 'string') {
    const parsed = new Date(d + (d.includes('T') ? '' : 'T00:00:00'))
    if (!isNaN(parsed)) return parsed
  }
  return null
}

export function formatDateTime(d) {
  const date = parseDate(d)
  if (!date) return '—'
  return `${DAYS[date.getDay()]}, ${date.getDate()} de ${MONTHS[date.getMonth()]} de ${date.getFullYear()} · ${date.toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit' })}`
}

export function formatDateFull(d) {
  const date = parseDate(d)
  if (!date) return '—'
  return `${DAYS[date.getDay()]}, ${date.getDate()} de ${MONTHS[date.getMonth()]} de ${date.getFullYear()}`
}

export function formatDateShort(d) {
  const date = parseDate(d)
  if (!date) return '—'
  return date.toLocaleDateString(LOCALE, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatTime(d) {
  const date = parseDate(d)
  if (!date) return '—'
  return date.toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatTimeShort(d) {
  const date = parseDate(d)
  if (!date) return '—'
  return date.toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit' })
}

export function formatDateChart(fechaStr) {
  if (!fechaStr) return ''
  const parts = fechaStr.split('-')
  if (parts.length !== 3) return fechaStr
  const month = parseInt(parts[1], 10)
  const day = parseInt(parts[2], 10)
  return `${day} ${MONTHS[month - 1]?.slice(0, 3)}`
}

export function formatDayShort(fechaStr) {
  if (!fechaStr) return ''
  const date = parseDate(fechaStr)
  if (!date) return fechaStr
  const dayName = DAYS[date.getDay()].slice(0, 3)
  return `${dayName} ${date.getDate()}/${String(date.getMonth() + 1).padStart(2, '0')}`
}

export function formatRelative(fechaStr) {
  if (!fechaStr) return ''
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const date = parseDate(fechaStr)
  if (!date) return fechaStr
  date.setHours(0, 0, 0, 0)
  const diff = (today - date) / (1000 * 60 * 60 * 24)
  if (diff === 0) return 'Hoy'
  if (diff === 1) return 'Ayer'
  if (diff > 1 && diff <= 7) return `Hace ${diff} días`
  return formatDateShort(fechaStr)
}

export function formatWeekday(fechaStr) {
  const date = parseDate(fechaStr)
  if (!date) return ''
  return DAYS[date.getDay()]
}
