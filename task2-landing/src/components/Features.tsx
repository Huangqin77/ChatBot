import { ArrowUpRight, Bot, Braces, Check, CheckCheck, Code2, FileText, GitBranch, MessageSquare, MousePointer2, Plus, Search, Sparkles, Users, Wrench } from 'lucide-react'
import { SectionHeading } from './ui'

function CollaborationVisual() {
  return <div className="feature-visual collaboration-visual" aria-hidden="true"><div className="mini-chat"><span className="mini-avatar lavender">林</span><div>这个方向不错，一起完善一下？<span className="mini-time">刚刚 <CheckCheck size={12} /></span></div></div><div className="mini-chat mini-chat-right"><span className="mini-avatar green"><Bot size={14} /></span><div>已经为团队整理好下一步计划。</div></div><span className="collab-cursor"><MousePointer2 size={16} fill="currentColor" /> 陈一正在协作</span></div>
}
function BotVisual() {
  return <div className="feature-visual bot-visual" aria-hidden="true"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><span className="orbit-bot bot-node-one"><Code2 size={20} /></span><span className="orbit-bot bot-node-two"><Search size={20} /></span><span className="orbit-bot bot-node-three"><FileText size={20} /></span><span className="central-bot"><Bot size={35} /><span><Plus size={11} /></span></span><span className="bot-skill-tag"><span className="live-dot" /> 为你的工作量身定制</span></div>
}
function ToolVisual() {
  return <div className="feature-visual tool-visual" aria-hidden="true"><div className="tool-mini-header"><span><Braces size={14} /> 工具执行</span><span><Check size={12} /> Success</span></div><code><span>await</span> tools.execute({'{'}<br />&nbsp; action: <b>"analyze_data"</b>,<br />&nbsp; context: <b>"current_room"</b><br />{'}'})</code><div className="tool-mini-footer"><Check size={12} /> 结果已同步至当前对话</div></div>
}
function AgentsVisual() {
  return <div className="feature-visual agents-visual" aria-hidden="true"><div className="agent-source"><span><Users size={15} /></span>一个共同目标</div><div className="agent-connectors"><i /><i /><i /></div><div className="agent-nodes"><span><Search size={17} />研究</span><span><Code2 size={17} />执行</span><span><FileText size={17} />整理</span></div><div className="agent-result"><CheckCheck size={13} /> 分工协同，汇聚成果</div></div>
}

const features = [
  { icon: Users, label: 'CONNECT', title: '多人协作，想法实时同频', description: '把同事与 AI 邀请进同一个空间。信息同步、讨论连贯，团队始终站在同一页。', visual: CollaborationVisual, className: 'feature-connect' },
  { icon: Bot, label: 'PERSONALIZE', title: '你的团队，你的 AI 伙伴', description: '为不同任务创建专属 Bot，设定角色与能力。让每一个 AI，都成为懂业务的搭档。', visual: BotVisual, className: 'feature-personalize' },
  { icon: Wrench, label: 'EXECUTE', title: '不止会说，更能动手完成', description: '让 AI 在对话中调用工具、执行任务。把繁琐步骤交给工具，把精力留给重要的事。', visual: ToolVisual, className: 'feature-execute' },
  { icon: GitBranch, label: 'ORCHESTRATE', title: '多个智能体，一个共同目标', description: '用 @ 分配任务，让多个 Bot 各展所长。过程可追溯，成果和上下文一起留在团队里。', visual: AgentsVisual, className: 'feature-orchestrate' },
]

export default function Features() {
  return <section id="features" className="section features-section"><div className="container">
    <SectionHeading eyebrow="BUILT FOR BETTER TOGETHER" title={<>不只是聊天，<span className="text-muted">更是一起把事情做好。</span></>} description="把沟通、智能与执行连接起来，让团队协作拥有新的可能。" />
    <div className="features-grid">{features.map(({ icon: Icon, visual: Visual, ...feature }) => <article key={feature.label} className={`feature-card ${feature.className}`}><div className="feature-topline"><span className="feature-icon"><Icon size={20} /></span><span>{feature.label}</span><ArrowUpRight size={16} /></div><h3>{feature.title}</h3><p>{feature.description}</p><Visual /></article>)}</div>
    <div className="features-footnote"><MessageSquare size={15} /><span>对话不再散落，工作不再断线。</span><span className="footnote-divider" /><Sparkles size={15} /><span>每一步协作，都有迹可循。</span></div>
  </div></section>
}
