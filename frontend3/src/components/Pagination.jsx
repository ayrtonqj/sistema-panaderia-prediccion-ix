import { useState, useEffect } from 'react'

export default function Pagination({ data, pageSize = 20, renderRow, columns }) {
  const [page, setPage] = useState(1)
  const totalPages = Math.ceil(data.length / pageSize)
  const slice = data.slice((page - 1) * pageSize, page * pageSize)

  useEffect(() => { setPage(1) }, [data])

  return (
    <>
      <div className="table-container">
        <table>
          <thead>
            <tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {slice.length === 0
              ? <tr><td colSpan={columns.length} style={{textAlign:'center',color:'#8892a4',padding:'30px'}}>Sin registros</td></tr>
              : slice.map((row, i) => renderRow(row, i))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>Anterior</button>
          <span>Página {page} de {totalPages}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Siguiente</button>
        </div>
      )}
    </>
  )
}
