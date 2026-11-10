import { useState } from 'react'
import { ArrowUpRight, Plus } from 'lucide-react'
import { SectionHeading } from './ui'
import { IS_WORKSPACE_DEMO } from '../lib/config'

const questions = [
  { question: 'CollabAI 和普通 AI 聊天工具有什么不同？', answer: 'CollabAI 将团队成员与多个 AI Bot 放在同一个聊天室中。你可以和同事讨论、@Bot 分配任务，并在同一处查看工具执行和协作结果，让上下文随着工作持续积累。' },
  { question: '可以让多个 AI Bot 一起完成任务吗？', answer: '可以。你可以邀请不同职责的 Bot 加入聊天室，通过 @ 指定协作伙伴，让它们分别参与研究、分析或整理等环节。具体执行能力取决于工作台中为 Bot 配置的模型和工具。' },
  { question: '我需要编程基础才能使用吗？', answer: '日常协作通过自然语言进行。创建聊天室、邀请成员或使用已配置的 Bot 不需要编写代码；部署工作台、配置模型服务或接入自定义工具时，可能需要相应的技术配置。' },
  { question: '聊天记录和任务结果在哪里查看？', answer: '对话、Bot 的执行过程以及返回的结果会在对应聊天室中展示，方便团队结合上下文继续讨论。记录的保存方式与可用范围，以你实际运行的工作台配置为准。' },
  { question: '如何体验 CollabAI 工作台？', answer: IS_WORKSPACE_DEMO ? '当前公开版本为产品官网演示，工作台尚未公开部署。页面中的体验按钮将带你查看本页产品演示，不会跳转到访问者电脑的本地地址，也不会执行真实 AI 请求。工作台上线后即可连接实际服务。' : '点击体验按钮即可打开配置的 CollabAI 工作台。本地开发请先启动任务一聊天室；官网内的产品预览仍为界面演示，不会执行真实 AI 请求。' },
]

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(0)
  return <section id="faq" className="section faq-section"><div className="container faq-layout"><div className="faq-intro"><SectionHeading eyebrow="A LITTLE MORE CLARITY" title={<>你可能还想<br />了解这些。</>} description="关于 CollabAI 的几个常见问题。" /><a href="#product-preview" className="text-link">再看看产品演示 <ArrowUpRight size={16} /></a></div><div className="faq-list">{questions.map((item, index) => <article className={`faq-item ${open === index ? 'is-open' : ''}`} key={item.question}><h3><button id={`faq-trigger-${index}`} aria-controls={`faq-panel-${index}`} aria-expanded={open === index} onClick={() => setOpen(open === index ? null : index)}>{item.question}<span><Plus size={18} /></span></button></h3><div id={`faq-panel-${index}`} role="region" aria-labelledby={`faq-trigger-${index}`} hidden={open !== index}><p>{item.answer}</p></div></article>)}</div></div></section>
}
