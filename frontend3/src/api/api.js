const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`

const TIMEOUTS = {
  'POST:/ml/entrenar': 300000,
  'POST:/ml/comparar': 300000,
  'POST:/datos/semilla': 120000,
}

async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const method = options.method || 'GET'
  const key = `${method}:${path.split('?')[0]}`
  const ms = TIMEOUTS[key] || 15000
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), ms)
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...options,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      const err = new Error(body?.detail || `HTTP ${res.status}`)
      err.response = { data: body, status: res.status }
      throw err
    }
    return res.json()
  } finally {
    clearTimeout(timeout)
  }
}

export const api = {
  get:    (path)        => apiFetch(path),
  post:   (path, data)  => apiFetch(path, { method: 'POST',   body: JSON.stringify(data) }),
  put:    (path, data)  => apiFetch(path, { method: 'PUT',    body: JSON.stringify(data) }),
  del:    (path)        => apiFetch(path, { method: 'DELETE' }),
}
