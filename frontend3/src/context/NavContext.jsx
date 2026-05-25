import { createContext, useContext } from 'react'

const NavContext = createContext(null)

export function NavProvider({ navigate, children }) {
  return (
    <NavContext.Provider value={navigate}>
      {children}
    </NavContext.Provider>
  )
}

export function useNav() {
  return useContext(NavContext)
}
