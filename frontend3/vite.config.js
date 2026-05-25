import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/productos': 'http://localhost:8000',
      '/ventas': 'http://localhost:8000',
      '/insumos': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/mermas': 'http://localhost:8000',
      '/predicciones': 'http://localhost:8000',
      '/clima': 'http://localhost:8000',
      '/ordenes-compra': 'http://localhost:8000',
      '/proveedores': 'http://localhost:8000',
      '/fichas-tecnicas': 'http://localhost:8000',
      '/reportes': 'http://localhost:8000',
      '/ml': 'http://localhost:8000',
      '/datos': 'http://localhost:8000',
      '/chatbot': 'http://localhost:8000',
      '/sistema': 'http://localhost:8000',
    },
  },
})
