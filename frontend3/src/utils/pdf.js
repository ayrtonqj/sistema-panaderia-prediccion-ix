import { formatDateFull } from './formatters'

export const LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 70" width="160" height="50">
  <defs>
    <linearGradient id="panGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#d4a574"/>
      <stop offset="50%" style="stop-color:#c9956c"/>
      <stop offset="100%" style="stop-color:#b8845c"/>
    </linearGradient>
  </defs>
  <rect x="5" y="8" width="55" height="55" rx="12" fill="url(#panGrad)"/>
  <ellipse cx="32" cy="38" rx="20" ry="16" fill="#e8c9a0"/>
  <ellipse cx="32" cy="35" rx="17" ry="13" fill="#f5deb3"/>
  <path d="M20 32 Q32 24 44 32" stroke="#c9956c" stroke-width="2" fill="none"/>
  <path d="M22 38 Q32 30 42 38" stroke="#c9956c" stroke-width="2" fill="none"/>
  <path d="M24 44 Q32 36 40 44" stroke="#c9956c" stroke-width="2" fill="none"/>
  <text x="70" y="36" font-family="Arial" font-size="18" font-weight="700" fill="#667eea" letter-spacing="2">VICTORIA</text>
  <text x="70" y="54" font-family="Arial" font-size="13" font-weight="500" fill="#764ba2" letter-spacing="3">PANADERÍA</text>
</svg>`

export const PDF_BASE_STYLES = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Arial, sans-serif; padding: 20px; color: #333; }
  .header { display: flex; align-items: center; justify-content: center; gap: 20px; padding: 20px 0; border-bottom: 3px solid #667eea; margin-bottom: 20px; }
  .header-text h1 { margin: 0; font-size: 20px; color: #667eea; }
  .header-text p { margin: 4px 0 0; font-size: 12px; color: #888; }
  table { width: 100%; border-collapse: collapse; margin-top: 15px; }
  th, td { border: 1px solid #ddd; padding: 9px 12px; text-align: left; font-size: 12px; }
  th { background: #667eea; color: white; }
  tr:nth-child(even) { background: #f9f9f9; }
  .footer { margin-top: 30px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #ddd; padding-top: 10px; }
  .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
  .metric-box { text-align: center; padding: 15px 25px; background: #f5f5f5; border-radius: 8px; border: 1px solid #ddd; }
  .metric-box .value { font-size: 22px; font-weight: bold; color: #667eea; }
  .metric-box .label { font-size: 11px; color: #888; margin-top: 4px; }
`

export function openPrintWindow(title, bodyHtml) {
  const w = window.open('', '_blank')
  w.document.write(`<!DOCTYPE html><html><head><title>${title}</title><style>${PDF_BASE_STYLES}</style></head><body>${bodyHtml}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 500)
}

export function tableHeaderHtml(title) {
  return `<div class="header">${LOGO_SVG}<div class="header-text"><h1>${title}</h1><p>Generado: ${formatDateFull(new Date())}</p></div></div>`
}

export function numeroALetras(num) {
  const entero = Math.floor(num)
  const decimal = Math.round((num - entero) * 100)

  const unidades = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
  const especiales = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
  const decenas = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
  const centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']

  function convertirTres(n) {
    let r = ''
    if (n >= 100) {
      r += n === 100 ? 'CIEN ' : centenas[Math.floor(n / 100)] + ' '
      n %= 100
    }
    if (n >= 20) {
      if (n < 30) {
        r += n === 20 ? 'VEINTE ' : 'VEINTI' + unidades[n - 20].toLowerCase() + ' '
        n = 0
      } else {
        r += decenas[Math.floor(n / 10)] + ' '
        n %= 10
        if (n > 0) r += 'Y '
      }
    } else if (n >= 10) {
      r += especiales[n - 10] + ' '
      n = 0
    }
    if (n > 0) r += unidades[n] + ' '
    return r.trim()
  }

  function convertirMiles(n) {
    if (n === 0) return 'CERO'
    let r = ''
    const miles = Math.floor(n / 1000)
    const resto = n % 1000
    if (miles > 0) {
      r += miles === 1 ? 'MIL ' : convertirTres(miles) + ' MIL '
    }
    if (resto > 0) r += convertirTres(resto)
    return r.trim()
  }

  const letras = convertirMiles(entero)
  return `${letras} CON ${String(decimal).padStart(2, '0')}/100 SOLES`
}

export function getNextInvoiceNumber() {
  const today = new Date().toISOString().slice(0, 10)
  const key = `invoice_counter_${today}`
  const count = parseInt(localStorage.getItem(key) || '0') + 1
  localStorage.setItem(key, count.toString())
  return `B001-${String(count).padStart(8, '0')}`
}

const INVOICE_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inconsolata&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Courier New', Courier, monospace; font-size: 11px; color: #000; width: 80mm; padding: 8px; }
  .factura { width: 100%; }
  .center { text-align: center; }
  .right { text-align: right; }
  .bold { font-weight: bold; }
  .header-line { font-size: 10px; line-height: 1.4; }
  .title { font-size: 14px; font-weight: bold; margin: 4px 0; letter-spacing: 2px; }
  .subtitle { font-size: 11px; font-weight: bold; margin: 2px 0; }
  .serie { font-size: 13px; font-weight: bold; margin: 6px 0; letter-spacing: 1px; }
  .sep { border-top: 1px dashed #000; margin: 6px 0; }
  .sep-solid { border-top: 1px solid #000; margin: 6px 0; }
  .detalle { width: 100%; border-collapse: collapse; font-size: 10px; }
  .detalle th { border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 4px 2px; font-size: 9px; text-align: left; background: none; color: #000; }
  .detalle td { padding: 3px 2px; vertical-align: top; }
  .detalle tr:nth-child(even) { background: none; }
  .totales { width: 100%; margin-top: 4px; font-size: 10px; }
  .totales td { padding: 2px 0; }
  .total-final { font-size: 14px; font-weight: bold; }
  .leyenda { font-size: 9px; margin-top: 4px; text-transform: uppercase; font-weight: bold; }
  .footer-text { font-size: 8px; margin-top: 8px; text-align: center; }
  .ruc-line { font-size: 12px; font-weight: bold; letter-spacing: 1px; }
`

export function generarFacturaHTML(cart, invoiceData) {
  const { numero, fecha, hora, items, subtotal, igv, total, totalLetras, vendedor_nombre, vendedor_dni } = invoiceData

  const filas = items.map(item => `
    <tr>
      <td class="right">${item.cantidad.toFixed(2)}</td>
      <td>${item.producto.nombre.toUpperCase()}</td>
      <td class="right">${item.producto.precio.toFixed(2)}</td>
      <td class="right">${(item.producto.precio * item.cantidad).toFixed(2)}</td>
    </tr>
  `).join('\n')

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Boleta ${numero}</title>
  <style>${INVOICE_CSS}</style>
</head>
<body>
  <div class="factura">
    <div class="center header-line">
      ${LOGO_SVG.replace(/width="160" height="50"/, 'width="120" height="40"')}
      <div class="title">PANADERÍA VICTORIA</div>
      <div class="ruc-line">RUC: 10456789012</div>
      <div>Av. Principal 123 - Pacasmayo</div>
      <div>Tel: (044) 123456</div>
    </div>

    <div class="sep"></div>

    <div class="center">
      <div class="subtitle">BOLETA DE VENTA ELECTRÓNICA</div>
      <div class="serie">${numero}</div>
    </div>

    <div class="sep"></div>

    <div class="header-line">
      <div>FECHA: ${fecha}${hora ? '    HORA: ' + hora : ''}</div>
      ${vendedor_nombre ? `<div>VENDEDOR: ${vendedor_nombre.toUpperCase()}${vendedor_dni ? ' / DNI ' + vendedor_dni : ''}</div>` : ''}
    </div>

    <div class="sep-solid"></div>

    <table class="detalle">
      <thead>
        <tr>
          <th width="50" class="right">CANT.</th>
          <th width="140">DESCRIPCIÓN</th>
          <th width="55" class="right">P.UNIT</th>
          <th width="55" class="right">TOTAL</th>
        </tr>
      </thead>
      <tbody>
        ${filas}
      </tbody>
    </table>

    <div class="sep-solid"></div>

    <table class="totales">
      <tr><td width="160">OP. GRAVADAS</td><td class="right">S/ ${subtotal.toFixed(2)}</td></tr>
      <tr><td>IGV (18%)</td><td class="right">S/ ${igv.toFixed(2)}</td></tr>
      <tr><td colspan="2"><div class="sep"></div></td></tr>
      <tr class="total-final">
        <td>TOTAL</td>
        <td class="right">S/ ${total.toFixed(2)}</td>
      </tr>
    </table>

    <div class="sep"></div>

    <div class="center leyenda">
      SON: ${totalLetras}
    </div>

    <div class="sep"></div>

    <div class="center" style="font-size: 9px;">
      <div>Autorizado mediante Resolución N° 0000000000</div>
      <div>Representación impresa de la Boleta de Venta Electrónica</div>
      <div>Consulte en: https://www.sunat.gob.pe</div>
    </div>

    <div class="sep"></div>

    <div class="center footer-text">
      ¡Gracias por su preferencia!<br>
      ${fecha} ${hora}
    </div>
  </div>
  <script>
    window.onload = function() { window.print(); window.close(); }
  </script>
</body>
</html>`
}
