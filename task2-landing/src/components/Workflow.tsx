import { AtSign, ArrowRight, CheckCheck, MessageSquarePlus, UserPlus } from 'lucide-react'
import { SectionHeading, WorkspaceLink } from './ui'

const steps = [
  { icon: MessageSquarePlus, title: '创建一个聊天室', text: '围绕项目或目标，建立专属协作空间。', detail: '给好想法一个起点' },
  { icon: UserPlus, title: '邀请你的协作伙伴', text: '让团队成员和合适的 AI Bot 一起加入。', detail: '人类 + AI，一起就位' },
  { icon: AtSign, title: '@Bot，让任务开始', text: '像和同事沟通一样，把需求交给 AI。', detail: '自然表达，轻松分工' },
  { icon: CheckCheck, title: '协同推进，沉淀成果', text: '跟进执行过程，让结果留在团队上下文中。', detail: '让每次协作都有积累' },
]

export default function Workflow() {
  return <section id="workflow" className="section workflow-section"><div className="container">
    <div className="workflow-heading"><SectionHeading eyebrow="FROM IDEA TO DONE" title={<>像聊天一样自然，<br />让协作真正发生。</>} description="没有复杂的开始方式。四步，把你的下一件事交给团队。" /><a href="#product-preview" className="text-link">看看它如何工作 <ArrowRight size={16} /></a></div>
    <div className="workflow-steps">{steps.map(({ icon: Icon, ...step }, index) => <article className="workflow-step" key={step.title}><div className="workflow-step-top"><span className="workflow-icon"><Icon size={24} /></span><span className="step-number">0{index + 1}</span></div><h3>{step.title}</h3><p>{step.text}</p><span className="step-detail">{step.detail}</span></article>)}</div>
    <div className="workflow-bottom"><span><span className="live-dot" /> 下一个好项目，就从一句话开始。</span><WorkspaceLink className="button-small">创建我的工作空间</WorkspaceLink></div>
  </div></section>
}
