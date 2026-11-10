import { useState } from 'react'
import { ArrowRight, BarChart3, BookOpen, Check, ChevronRight, Coffee, FolderKanban, Lightbulb, Sparkles } from 'lucide-react'
import { APP_URL, IS_WORKSPACE_DEMO } from '../lib/config'
import { SectionHeading } from './ui'

const cases = [
  { icon: FolderKanban, name: '团队项目协作', label: 'PROJECT & TEAMWORK', title: '从一个想法，到一次漂亮的交付。', description: '让产品、设计、开发与 AI 同处一个聊天室。一起拆解需求、同步进度，把讨论变成明确的下一步。', prompt: '帮我们把官网改版的想法，整理成一份执行计划。', tasks: ['梳理项目目标与需求', '按角色拆解执行任务', '汇总讨论与阶段成果'], tag: '项目启动计划', summary: '让信息与行动保持同步' },
  { icon: BookOpen, name: '研究资料整理', label: 'RESEARCH & KNOWLEDGE', title: '把零散的信息，变成清晰的认知。', description: '和研究助手一起梳理资料、提炼重点，把关键观点和来源留在同一个上下文，方便团队持续补充。', prompt: '整理这些研究资料，提炼观点并保留对应来源。', tasks: ['按主题归类研究资料', '提炼核心观点与摘要', '沉淀可继续讨论的结论'], tag: '研究资料摘要', summary: '让团队知识持续积累' },
  { icon: BarChart3, name: '数据分析辅助', label: 'DATA & INSIGHTS', title: '和数据聊一聊，找到下一步方向。', description: '让分析助手协助处理数据、识别趋势，再和团队一起讨论结果。把分析过程和行动建议放在一处。', prompt: '分析本周项目数据，标记异常并给出行动建议。', tasks: ['整理数据与分析维度', '查看趋势与异常变化', '汇总发现与行动建议'], tag: '数据洞察报告', summary: '让分析推动实际决策' },
  { icon: Coffee, name: '日常办公自动化', label: 'EVERYDAY PRODUCTIVITY', title: '重复的事交给 AI，专注值得做的事。', description: '从会议纪要到工作计划，让 AI 帮你整理日常信息、调用工具执行，让琐碎工作有条理地推进。', prompt: '把今天的会议讨论整理成纪要，列出后续待办。', tasks: ['整理会议要点与结论', '生成待办与跟进清单', '保留执行过程与结果'], tag: '会议纪要与待办', summary: '让每一天轻松有序' },
]

export default function UseCases() {
  const [active, setActive] = useState(0)
  const item = cases[active]
  return <section id="use-cases" className="section use-cases-section"><div className="container">
    <SectionHeading eyebrow="ONE SPACE, MANY POSSIBILITIES" title={<>适合你的工作，<span className="text-muted">也适合你的工作方式。</span></>} description="无论正在推进什么，都有一位合适的 AI 伙伴与你同行。" />
    <div className="use-case-tabs" role="tablist" aria-label="应用场景">{cases.map(({ icon: Icon, name }, index) => <button role="tab" aria-selected={active === index} aria-controls="use-case-panel" id={`case-tab-${index}`} tabIndex={active === index ? 0 : -1} key={name} onClick={() => setActive(index)} onKeyDown={event => { let next = index; if (event.key === 'ArrowRight') next = (index + 1) % cases.length; else if (event.key === 'ArrowLeft') next = (index + cases.length - 1) % cases.length; else if (event.key === 'Home') next = 0; else if (event.key === 'End') next = cases.length - 1; else return; event.preventDefault(); setActive(next); document.getElementById(`case-tab-${next}`)?.focus() }}><Icon size={17} />{name}</button>)}</div>
    <div className="use-case-panel" id="use-case-panel" role="tabpanel" aria-labelledby={`case-tab-${active}`} tabIndex={0}>
      <div className="use-case-copy"><span className="eyebrow">{item.label}</span><h3>{item.title}</h3><p>{item.description}</p><ul>{item.tasks.map(task => <li key={task}><Check size={14} />{task}</li>)}</ul><a className="text-link" href={APP_URL}>{IS_WORKSPACE_DEMO ? '查看协作演示（工作台暂未上线）' : '让 AI 加入我的团队'} <ArrowRight size={16} /></a></div>
      <div className="use-case-illustration"><div className="case-orbit" aria-hidden="true" /><div className="idea-label"><Lightbulb size={14} /> 产品演示 · 从这里开始你的下一个项目</div><div className="case-prompt"><span className="mini-avatar lavender">你</span><p>{item.prompt}</p></div><div className="case-response"><div className="case-response-heading"><span className="tiny-bot purple"><Sparkles size={15} /></span><strong>创意助手</strong><span>任务完成示意</span></div><div className="case-document"><div className="case-document-icon"><item.icon size={24} /></div><div><strong>{item.tag}</strong><small>{item.summary}</small></div><ChevronRight size={16} /></div><div className="case-document-lines" aria-hidden="true"><i /><i /><i /></div><div className="case-done"><Check size={12} /> 演示结果 · 不执行真实 AI 请求</div></div><div className="case-bottom-tag"><span className="live-dot" /> YOUR TEAM, SUPERCHARGED.</div></div>
    </div>
  </div></section>
}
