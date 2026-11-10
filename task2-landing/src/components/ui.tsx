import { ArrowUpRight, Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'
import { APP_URL, IS_WORKSPACE_DEMO } from '../lib/config'

export function Logo({ light = false }: { light?: boolean }) {
  return <a className={`brand ${light ? 'brand-light' : ''}`} href="#home" aria-label="CollabAI 首页">
    <span className="brand-mark"><Sparkles size={22} strokeWidth={2} /></span>
    <span>Collab<span className="brand-ai">AI</span><span className="brand-dot">.</span></span>
  </a>
}

export function WorkspaceLink({ children = '进入工作台', className = '', arrow = true }: { children?: ReactNode; className?: string; arrow?: boolean }) {
  return <a className={`button button-primary ${className}`} href={APP_URL} data-workspace-mode={IS_WORKSPACE_DEMO ? 'demo' : 'workspace'} title={IS_WORKSPACE_DEMO ? '工作台尚未公开部署，点击查看产品演示' : undefined}>
    {IS_WORKSPACE_DEMO ? <>查看产品演示 <span className="demo-cta-badge">演示</span></> : children}{arrow && <ArrowUpRight size={17} aria-hidden="true" />}
  </a>
}

export function SectionHeading({ eyebrow, title, description }: { eyebrow: string; title: ReactNode; description?: string }) {
  return <div className="section-heading">
    <span className="eyebrow"><span />{eyebrow}</span>
    <h2>{title}</h2>
    {description && <p>{description}</p>}
  </div>
}
