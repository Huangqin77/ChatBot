import { useState } from 'react'
import { ArrowDownToLine, ArrowUp, AtSign, BarChart3, Bot, Check, ChevronDown, ChevronRight, CircleHelp, FileText, Hash, Layers3, Link2, MessageSquare, MoreHorizontal, Paperclip, Plus, Search, Settings2, Sparkles, Terminal, Users, Zap } from 'lucide-react'

export const previewScenes = [
  { id: 'project', name: '产品发布计划', title: '一起策划下一次产品发布', task: '帮我们整理一下新产品发布的执行计划，重点关注官网、内容和数据。', reply: '收到。我会和团队里的 Bot 一起，把想法变成可执行的计划。', file: '产品发布执行计划.md', detail: '3 个阶段 · 8 项待办 · 已整理', action: '生成项目执行计划', tool: '创建任务清单', icon: Layers3 },
  { id: 'research', name: '研究资料整理', title: '让每一份资料都有迹可循', task: '请把这次研究的资料按主题分类，提炼关键结论，并保留来源。', reply: '我会先整理资料，再请分析助手提炼观点，最后汇总到同一份文档。', file: '主题研究与来源索引.md', detail: '主题归类 · 观点摘要 · 来源记录', action: '归纳资料与关键观点', tool: '整理来源索引', icon: FileText },
  { id: 'data', name: '数据分析看板', title: '从数据中找到下一步方向', task: '请分析这份项目数据，整理趋势和异常，再给出下一步的行动建议。', reply: '好的。我会调用分析工具检查数据，和研究助手一起整理值得关注的变化。', file: '项目数据分析报告.md', detail: '趋势分析 · 异常标记 · 行动建议', action: '分析数据并生成报告', tool: '执行数据分析', icon: BarChart3 },
]

export default function ProductPreview() {
  const [selected, setSelected] = useState(0)
  const scene = previewScenes[selected]
  return <div className="preview-wrap" id="product-preview">
    <div className="preview-top-label"><span><span className="live-dot" /> YOUR NEXT WORKSPACE</span><span>更少切换，更多创造 <ArrowDownToLine size={12} /></span></div>
    <div className="product-window">
      <aside className="product-sidebar" aria-label="产品演示场景">
        <div className="workspace-brand"><span className="workspace-symbol"><Sparkles size={16} /></span><strong>创意实验室</strong><ChevronDown size={12} /><span className="demo-tag">演示</span></div>
        <div className="sidebar-search"><Search size={13} /><span>搜索工作空间</span><kbd>⌘ K</kbd></div>
        <div className="sidebar-item"><MessageSquare size={14} /><span>所有对话</span><span className="sidebar-count">03</span></div>
        <div className="sidebar-item"><Layers3 size={14} /><span>任务记录</span></div>
        <div className="sidebar-section"><span>我的聊天室</span><Plus size={13} /></div>
        {previewScenes.map((item, index) => <button key={item.id} className={`room-button ${selected === index ? 'active' : ''}`} onClick={() => setSelected(index)} aria-pressed={selected === index}><Hash size={15} /><span>{item.name}</span>{index === selected && <span className="room-dot" />}</button>)}
        <div className="sidebar-section"><span>AI 团队</span><Plus size={13} /></div>
        <div className="sidebar-bot"><span className="tiny-bot purple"><Bot size={13} /></span>创意助手<span className="online-dot" /></div>
        <div className="sidebar-bot"><span className="tiny-bot blue"><BarChart3 size={13} /></span>分析助手<span className="online-dot" /></div>
        <div className="sidebar-bot"><span className="tiny-bot mint"><Search size={13} /></span>研究助手<span className="online-dot" /></div>
        <div className="sidebar-bottom"><span className="person-avatar small">林</span><span>林晓的工作空间<small>一起创造更多可能</small></span><Settings2 size={15} /></div>
      </aside>
      <div className="product-main">
        <div className="chat-toolbar"><div><Hash size={19} /><strong>{scene.name}</strong><span className="room-type">团队空间</span></div><div className="toolbar-members"><span className="stacked-avatar one">林</span><span className="stacked-avatar two">陈</span><span className="stacked-avatar three"><Bot size={12} /></span><span className="member-total">+2</span><span className="toolbar-divider" /><MoreHorizontal size={18} /></div></div>
        <div className="chat-content" aria-live="polite" aria-atomic="true">
          <div className="conversation-date"><span />今天，灵感正在发生<span /></div>
          <div className="chat-message"><span className="person-avatar">林</span><div><div className="message-author">林晓 <span>10:24</span></div><p><span className="mention">@创意助手</span> {scene.task}</p></div></div>
          <div className="chat-message bot-message"><span className="bot-avatar"><Sparkles size={19} /></span><div className="bot-message-content"><div className="message-author">创意助手 <span className="bot-badge">BOT</span><span>10:24</span></div><p>{scene.reply}</p>
            <div className="execution-card"><div className="execution-header"><span><Zap size={13} /> 多智能体协作</span><span className="success-label"><Check size={11} /> 已完成</span></div><div className="execution-step"><span className="step-check"><Check size={11} /></span><span>研究助手</span><span className="execution-task">{scene.action}</span><Check size={12} className="execution-done" /></div><div className="execution-step"><span className="step-check"><Check size={11} /></span><span>分析助手</span><span className="execution-task">{scene.tool}</span><Check size={12} className="execution-done" /></div><div className="tool-command"><Terminal size={12} /><code>tools.execute</code><span>执行成功</span><ChevronRight size={12} /></div></div>
            <p className="result-text">已整理完成，团队可以在这里继续讨论、补充和推进。</p>
            <div className="result-file"><span className="file-icon"><FileText size={20} /></span><div><strong>{scene.file}</strong><small>{scene.detail}</small></div><span className="file-check"><Check size={14} /></span></div>
          </div></div>
          <div className="chat-message final-message"><span className="person-avatar peach">陈</span><div><div className="message-author">陈一 <span>10:25</span></div><p>方向很清晰，我来跟进内容部分。<span className="mention">@分析助手</span> 帮我一起看看。</p></div></div>
        </div>
        <div className="chat-composer"><div><AtSign size={15} /><span>让想法继续，@ 一位伙伴加入协作…</span></div><div className="composer-bottom"><span><Plus size={15} /><Paperclip size={14} /><Link2 size={14} /></span><span className="composer-hint">Enter 发送 <span className="send-illustration"><ArrowUp size={14} /></span></span></div></div>
        <div className="preview-disclaimer"><CircleHelp size={10} /> 产品交互示意 · 点击左侧聊天室切换场景</div>
      </div>
    </div>
    <div className="preview-caption"><span><Users size={14} /> 人与 AI，共享同一个上下文</span><span><Check size={13} /> 对话、执行、结果，始终在一起</span></div>
  </div>
}
