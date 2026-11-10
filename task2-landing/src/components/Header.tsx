import { useEffect, useRef, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { navigation } from '../lib/config'
import { Logo, WorkspaceLink } from './ui'

export default function Header() {
  const [open, setOpen] = useState(false)
  const menuButton = useRef<HTMLButtonElement>(null)
  const header = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!open) return
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setOpen(false); menuButton.current?.focus() }
    }
    const handleClick = (event: PointerEvent) => {
      if (!header.current?.contains(event.target as Node)) setOpen(false)
    }
    const media = window.matchMedia('(min-width: 768px)')
    const closeOnDesktop = () => { if (media.matches) setOpen(false) }
    document.addEventListener('keydown', handleKey)
    document.addEventListener('pointerdown', handleClick)
    media.addEventListener('change', closeOnDesktop)
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.removeEventListener('pointerdown', handleClick)
      media.removeEventListener('change', closeOnDesktop)
    }
  }, [open])

  return <header className="site-header" ref={header}>
    <div className="container header-inner">
      <Logo />
      <nav className="desktop-nav" aria-label="主导航">
        {navigation.map(item => <a key={item.href} href={item.href}>{item.label}</a>)}
      </nav>
      <div className="header-actions"><WorkspaceLink className="header-cta" />
        <button ref={menuButton} className="menu-toggle" aria-label={open ? '关闭导航菜单' : '打开导航菜单'} aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
    </div>
    <nav id="mobile-navigation" className="mobile-nav" aria-label="移动端导航" hidden={!open}>
      {navigation.map(item => <a key={item.href} href={item.href} onClick={() => setOpen(false)}>{item.label}</a>)}
      <WorkspaceLink />
    </nav>
  </header>
}
