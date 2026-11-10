import { ArrowRight, Check, MoveUpRight, Sparkles } from 'lucide-react'
import ProductPreview from './ProductPreview'
import { WorkspaceLink } from './ui'
import { IS_WORKSPACE_DEMO } from '../lib/config'

export default function Hero() {
  return <section className="hero" aria-labelledby="hero-title">
    <div className="hero-grid" aria-hidden="true" />
    <div className="container hero-content">
      <a className="hero-pill" href="#workflow"><span><Sparkles size={13} /> 为人机协作而生</span><span className="pill-divider" /><span>认识你的新团队</span><ArrowRight size={13} /></a>
      <h1 id="hero-title">好想法，<br /><span>和 AI 一起实现。</span></h1>
      <p className="hero-description">一个聊天室，连接你的团队与 AI 伙伴。<br />从灵感碰撞到任务完成，让每一次对话，都向前一步。</p>
      <div className="hero-actions"><WorkspaceLink>开始体验 <ArrowRight size={17} /></WorkspaceLink><a className="button button-secondary" href="#features">了解产品功能 <MoveUpRight size={16} /></a></div>
      <div className="hero-notes"><span><Check size={13} /> 多人实时协作</span><span><Check size={13} /> 专属 AI 伙伴</span><span><Check size={13} /> 从对话到执行</span></div>
      {IS_WORKSPACE_DEMO && <p className="demo-notice">当前为产品演示 · 工作台尚未公开部署</p>}
      <ProductPreview />
    </div>
  </section>
}
