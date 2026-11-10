import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ArrowDown, ArrowRight, AtSign, Bot as BotIcon, Check, CheckCheck, ChevronDown,
  ChevronRight, CircleAlert, Clock3, Code2, Hash, Layers3, LoaderCircle, LogOut, Menu,
  MessageSquare, Network, Plus, Send, Settings2, Sparkles, Terminal, Users, WifiOff, X } from 'lucide-react'
import { api, merge, savedUser, saveUser } from './api'
import type { Bot, Health, Message, Room, Snapshot, Task, ToolCall, User } from './types'

const toolLabels: Record<string, string> = { calculator: '安全计算器', get_current_time: '当前时间', delegate_to_bot: 'Bot 任务委派' }
const statusLabels = { running: '执行中', completed: '已完成', failed: '失败' }
const time = (value: string) => new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
const sortMessages = (messages: Message[]) => [...messages].sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id.localeCompare(b.id))

function Logo() {
  return <div className="logo"><div className="logo-mark"><Network size={22} strokeWidth={2.4} /></div><span>relay<span className="logo-dot">.</span></span></div>
}
function Avatar({ name, bot = false, small = false }: { name: string; bot?: boolean; small?: boolean }) {
  return <div className={`avatar ${bot ? 'bot-avatar' : ''} ${small ? 'small' : ''}`}>{bot ? <BotIcon size={small ? 16 : 20} /> : name.slice(0, 1).toUpperCase()}</div>
}
function Status({ status }: { status: Task['status'] }) {
  return <span className={`status ${status}`}>{status === 'running' ? <LoaderCircle size={12} className="spin" /> : status === 'completed' ? <Check size={12} /> : <CircleAlert size={12} />}{statusLabels[status]}</span>
}
function Modal({ title, subtitle, children, close }: { title: string; subtitle?: string; children: ReactNode; close: () => void }) {
  const container = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const first = container.current?.querySelector<HTMLElement>('input, button, textarea')
    first?.focus()
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
      if (e.key === 'Tab') {
        const elements = container.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input, textarea, select, [tabindex="0"]')
        if (!elements?.length) return
        const a = elements[0], b = elements[elements.length - 1]
        if (e.shiftKey && document.activeElement === a) { e.preventDefault(); b.focus() }
        else if (!e.shiftKey && document.activeElement === b) { e.preventDefault(); a.focus() }
      }
    }
    document.addEventListener('keydown', key)
    return () => { document.removeEventListener('keydown', key); previous?.focus() }
  }, [close])
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) close() }}>
    <div className="modal" role="dialog" aria-modal="true" aria-label={title} ref={container}>
      <button className="icon-btn modal-close" aria-label="关闭弹窗" onClick={close}><X size={19} /></button>
      <div className="eyebrow">YOUR COLLABORATION SPACE</div><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}{children}
    </div>
  </div>
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [nickname, setNickname] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try { const user = await api<User>('/users', { method: 'POST', body: JSON.stringify({ nickname: nickname.trim() }) }); saveUser(user); onLogin(user) }
    catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <div className="login-layout">
    <section className="login-story"><Logo /><div className="story-main"><div className="eyebrow light">A LITTLE TEAM. A BIG POSSIBILITY.</div>
      <h1>每一个好想法，<br />都值得<span>接力完成。</span></h1><p>把你、伙伴和 AI 队友放进同一个房间。<br />一起讨论、调用工具，让协作自然发生。</p>
      <div className="collab-illustration"><div className="illustration-node"><Users size={25} /><span>你和伙伴</span></div><div className="connection-line" /><div className="illustration-node mint"><BotIcon size={25} /><span>AI 队友</span></div><div className="connection-line" /><div className="illustration-node"><CheckCheck size={25} /><span>共同完成</span></div></div>
    </div><span className="story-footer">HUMAN IDEAS, CONNECTED INTELLIGENCE.</span></section>
    <main className="login-form"><div className="login-card"><span className="welcome-icon"><Sparkles size={25} /></span><div className="eyebrow">WELCOME TO RELAY</div><h2>开启你的协作空间</h2><p className="muted">一个昵称，就可以和团队开始对话。</p>
      <form onSubmit={submit}><label htmlFor="nickname">怎么称呼你？</label><input id="nickname" autoFocus placeholder="输入你的昵称" value={nickname} onChange={e => setNickname(e.target.value)} maxLength={24} required autoComplete="nickname" />
        {error && <div className="form-error" role="alert"><CircleAlert size={16} />{error}</div>}
        <button className="primary full" disabled={busy || !nickname.trim()}>{busy ? <LoaderCircle size={18} className="spin" /> : <>进入工作空间 <ArrowRight size={18} /></>}</button>
      </form><p className="login-note"><span className="tiny-dot" />本地演示身份 · 无需注册 · 每个标签页可使用不同昵称</p></div>
    </main>
  </div>
}

function CreateForm({ kind, done }: { kind: 'room' | 'bot'; done: (value: Room | Bot) => Promise<void> }) {
  const [name, setName] = useState(''), [role, setRole] = useState(''), [prompt, setPrompt] = useState('')
  const [tools, setTools] = useState(['calculator', 'get_current_time'])
  const [error, setError] = useState(''), [busy, setBusy] = useState(false)
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const value = await api<Room | Bot>(kind === 'bot' ? '/bots' : '/rooms', { method: 'POST', body: JSON.stringify(kind === 'bot' ?
        { name: name.trim(), role: role.trim(), system_prompt: prompt.trim(), tools } : { name: name.trim(), description: role.trim() }) })
      await done(value)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <form className="create-form" onSubmit={submit}>
    <label htmlFor="entity-name">{kind === 'bot' ? 'Bot 名称' : '房间名称'}</label>
    <input id="entity-name" value={name} onChange={e => setName(e.target.value)} placeholder={kind === 'bot' ? '例如：研究员' : '例如：产品灵感站'} maxLength={kind === 'bot' ? 24 : 40} required />
    {kind === 'bot' && <span className="field-help">使用中文、字母、数字、下划线或短横线，方便 @ 提及。</span>}
    <label htmlFor="entity-role">{kind === 'bot' ? '角色描述' : '房间描述（选填）'}</label>
    <input id="entity-role" value={role} onChange={e => setRole(e.target.value)} placeholder={kind === 'bot' ? '这个队友擅长什么？' : '这个房间用来做什么？'} maxLength={kind === 'bot' ? 120 : 240} required={kind === 'bot'} />
    {kind === 'bot' && <><label htmlFor="system-prompt">System Prompt</label><textarea id="system-prompt" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="你是一位严谨的研究员。请使用工具核验计算，并用中文回答…" rows={4} maxLength={6000} required />
      <label>启用工具</label><div className="tool-options">{Object.entries(toolLabels).map(([id, label]) => <label key={id} className="check-option"><input type="checkbox" checked={tools.includes(id)} onChange={e => setTools(e.target.checked ? [...tools, id] : tools.filter(t => t !== id))} /><span>{label}<small>{id}</small></span></label>)}</div></>}
    {error && <div className="form-error" role="alert">{error}</div>}<button className="primary full" disabled={busy || !name.trim() || (kind === 'bot' && (!role.trim() || !prompt.trim()))}>{busy ? <LoaderCircle size={17} className="spin" /> : <Plus size={17} />}{kind === 'bot' ? '创建并加入当前房间' : '创建聊天室'}</button>
  </form>
}

function InviteBots({ bots, selected, save }: { bots: Bot[]; selected: string[]; save: (ids: string[]) => Promise<void> }) {
  const [ids, setIds] = useState(selected), [busy, setBusy] = useState(false), [error, setError] = useState('')
  return <div className="invite-list">{bots.length === 0 && <p className="muted">还没有 Bot，请先创建一个队友。</p>}{bots.map(bot => <label className="invite-bot" key={bot.id}><Avatar name={bot.name} bot /><span><strong>{bot.name}</strong><small>{bot.role}</small></span><input type="checkbox" checked={ids.includes(bot.id)} onChange={e => setIds(e.target.checked ? [...ids, bot.id] : ids.filter(id => id !== bot.id))} /></label>)}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary full" disabled={busy} onClick={async () => { setBusy(true); try { await save(ids) } catch (e) { setError((e as Error).message) } finally { setBusy(false) } }}>{busy ? <LoaderCircle size={17} className="spin" /> : <Check size={17} />}保存房间队友</button>
  </div>
}

function TaskDetail({ root, tasks, calls }: { root: Task; tasks: Task[]; calls: ToolCall[] }) {
  const chain = tasks.filter(t => t.root_id === root.id).sort((a, b) => a.created_at.localeCompare(b.created_at))
  const toolCalls = calls.filter(c => c.root_id === root.id)
  const delegationPaths = toolCalls.filter(c => c.name === 'delegate_to_bot' && c.child_task_id).map(c => {
    const parent = chain.find(t => t.id === c.task_id), child = chain.find(t => t.id === c.child_task_id)
    return parent && child ? `${parent.bot_name} → ${child.bot_name} → ${parent.bot_name}` : null
  }).filter(Boolean)
  return <div className="task-detail"><div className="detail-top"><span className="eyebrow">TASK TRACE</span><code>{root.id.slice(0, 8)}</code></div>
    <div className="trace-summary"><span>{root.mode === 'demo' ? 'DEMO / MOCK' : 'LIVE MODEL'}</span><span>工具 {toolCalls.length}/6 · 深度 {Math.max(...chain.map(t => t.depth), 0)}/2</span></div>
    <p className="task-input">{root.input}</p>
    <div className="trace-chain">{chain.map(t => <div key={t.id} className="chain-node" style={{ marginLeft: t.depth * 12 }}><div className="chain-dot" /><div className="chain-body"><strong>{t.bot_name}</strong><Status status={t.status} /><small>{t.parent_id ? '接收委派 · 完成后返回上级 Bot' : '接收任务 · 汇总并回复聊天室'}</small>{t.error && <p className="form-error">{t.error}</p>}</div></div>)}</div>
    {delegationPaths.map((path, i) => <div className="return-path" key={i}><Network size={14} />{path}</div>)}
    <div className="detail-label"><Terminal size={14} />工具执行记录 <span>{toolCalls.length}</span></div>
    {toolCalls.length === 0 && <p className="empty-small">此任务尚无工具调用。</p>}
    {toolCalls.map(call => <details className="tool-record" key={call.id} open={call.status === 'running' || undefined}><summary><Code2 size={14} /><span>{call.name}</span><Status status={call.status} /></summary><div className="tool-body"><label>INPUT</label><pre>{JSON.stringify(call.input, null, 2)}</pre><label>OUTPUT</label><pre>{call.output || '等待工具返回…'}</pre>{call.child_task_id && <small>委派任务：{call.child_task_id.slice(0, 8)}</small>}</div></details>)}
    {root.output && <details className="result-record"><summary>查看任务最终结果<ChevronDown size={14} /></summary><pre>{root.output}</pre></details>}
  </div>
}

function Chatroom({ user, logout }: { user: User; logout: () => void }) {
  const [rooms, setRooms] = useState<Room[]>([]), [allBots, setAllBots] = useState<Bot[]>([])
  const [roomId, setRoomId] = useState(() => sessionStorage.getItem('relay.room') || '')
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null), [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState(''), [loading, setLoading] = useState(true)
  const [connection, setConnection] = useState<'connecting' | 'online' | 'offline'>('connecting')
  const [people, setPeople] = useState<{ id: string; nickname: string }[]>([])
  const [draft, setDraft] = useState(''), [pending, setPending] = useState<string | null>(null)
  const [mentionOpen, setMentionOpen] = useState(false), [mentionQuery, setMentionQuery] = useState('')
  const [modal, setModal] = useState<'room' | 'bot' | 'invite' | null>(null)
  const [leftOpen, setLeftOpen] = useState(false), [rightOpen, setRightOpen] = useState(false)
  const [rightTab, setRightTab] = useState<'team' | 'tasks'>('team'), [selectedTask, setSelectedTask] = useState('')
  const [loadingHistory, setLoadingHistory] = useState(false), [retry, setRetry] = useState(0)
  const socket = useRef<WebSocket | null>(null), input = useRef<HTMLTextAreaElement>(null), end = useRef<HTMLDivElement>(null)
  const scroller = useRef<HTMLDivElement>(null), nearBottom = useRef(true), pendingTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const pendingRef = useRef<string | null>(null)
  const closeModal = useCallback(() => setModal(null), [])
  const clearPending = useCallback(() => { pendingRef.current = null; setPending(null); clearTimeout(pendingTimer.current) }, [])

  const refreshLists = useCallback(async () => {
    const [r, b, h] = await Promise.all([api<Room[]>('/rooms'), api<Bot[]>('/bots'), api<Health>('/health')])
    setRooms(r); setAllBots(b); setHealth(h)
    setRoomId(current => r.some(room => room.id === current) ? current : r[0]?.id || '')
  }, [])
  useEffect(() => { refreshLists().catch(e => { setError(e.message); setLoading(false) }) }, [refreshLists, retry])

  useEffect(() => {
    if (!roomId) return
    let disposed = false, reconnect: ReturnType<typeof setTimeout>, heartbeat: ReturnType<typeof setInterval>, attempt = 0
    sessionStorage.setItem('relay.room', roomId)
    setSnapshot(null); setLoading(true); setPeople([]); setSelectedTask(''); setDraft(''); clearPending(); nearBottom.current = true
    const update = (patch: (s: Snapshot) => Snapshot) => setSnapshot(s => s ? patch(s) : s)
    const connect = () => {
      if (disposed) return
      setConnection('connecting')
      const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/rooms/${roomId}?token=${encodeURIComponent(user.token)}`)
      socket.current = ws
      ws.onopen = () => {
        attempt = 0
        heartbeat = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' })) }, 20000)
      }
      ws.onmessage = e => {
        if (disposed) return
        const data = JSON.parse(e.data)
        if (data.type === 'snapshot') { setSnapshot(data as Snapshot); setConnection('online'); setLoading(false); return }
        if (data.type === 'presence') setPeople(data.users)
        if (data.type === 'message') {
          update(s => ({ ...s, messages: sortMessages(merge(s.messages, [data.message as Message])) }))
          if (data.message.client_id && data.message.client_id === pendingRef.current) { setDraft(''); clearPending(); input.current?.focus() }
        }
        if (data.type === 'task') update(s => ({ ...s, tasks: merge(s.tasks, [data.task as Task]) }))
        if (data.type === 'tool_call') update(s => ({ ...s, tool_calls: merge(s.tool_calls, [data.tool_call as ToolCall]) }))
        if (data.type === 'error') { setError(data.message); if (data.client_id === pendingRef.current) clearPending() }
        if (data.type === 'rooms_changed') refreshLists().catch(e => setError(e.message))
        if (data.type === 'bots_changed') {
          api<Bot[]>('/bots').then(setAllBots).catch(e => setError(e.message))
          api<Snapshot>(`/rooms/${roomId}/state`).then(s => { if (!disposed) update(old => ({ ...old, bots: s.bots })) }).catch(e => setError(e.message))
        }
      }
      ws.onerror = () => { if (!disposed) setConnection('offline') }
      ws.onclose = event => {
        clearInterval(heartbeat)
        if (disposed) return
        setConnection('offline'); setLoading(false); clearPending()
        if (event.code === 1008) { setError('会话已失效或房间不存在，请切换昵称重新进入。'); return }
        reconnect = setTimeout(connect, Math.min(1000 * 2 ** attempt++, 10000))
      }
    }
    connect()
    return () => { disposed = true; clearTimeout(reconnect); clearInterval(heartbeat); clearPending(); socket.current?.close() }
  }, [roomId, user.token, clearPending, refreshLists, retry])

  useEffect(() => { if (nearBottom.current) end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [snapshot?.messages.length, snapshot?.tasks.filter(t => t.status === 'running').length])
  const activeRoom = rooms.find(r => r.id === roomId)
  const activeBots = snapshot?.bots || []
  const roots = (snapshot?.tasks || []).filter(t => !t.parent_id).sort((a, b) => b.created_at.localeCompare(a.created_at))
  const running = (snapshot?.tasks || []).filter(t => t.status === 'running')
  const selected = roots.find(t => t.id === selectedTask) || roots[0]
  const suggestions = activeBots.filter(b => b.name.toLowerCase().includes(mentionQuery.toLowerCase()))

  async function openTask(id: string) {
    setRightTab('tasks'); setRightOpen(true)
    const known = snapshot?.tasks.find(t => t.id === id)
    if (known) { setSelectedTask(known.root_id); return }
    try {
      const data = await api<{ root_id: string; room_id: string; tasks: Task[]; tool_calls: ToolCall[] }>(`/tasks/${id}`)
      setSnapshot(s => s?.room.id === data.room_id ? { ...s, tasks: merge(s.tasks, data.tasks), tool_calls: merge(s.tool_calls, data.tool_calls) } : s)
      setSelectedTask(data.root_id)
    } catch (e) { setError((e as Error).message) }
  }
  function mention(bot: Bot) {
    const prefix = draft.replace(/@[^\s@]*$/, '')
    setDraft(`${prefix}${prefix && !/\s$/.test(prefix) ? ' ' : ''}@${bot.name} `)
    setMentionOpen(false); setMentionQuery(''); setRightOpen(false); input.current?.focus()
  }
  function send(e?: FormEvent) {
    e?.preventDefault()
    if (!draft.trim() || pending || socket.current?.readyState !== WebSocket.OPEN || connection !== 'online') return
    const client_id = crypto.randomUUID()
    pendingRef.current = client_id; setPending(client_id); setError(''); setMentionOpen(false); nearBottom.current = true
    socket.current.send(JSON.stringify({ type: 'message', content: draft.trim(), client_id }))
    pendingTimer.current = setTimeout(() => { clearPending(); setError('未收到发送确认。草稿已保留，请检查连接后再发送。') }, 10000)
  }
  async function invite(ids: string[]) {
    await api(`/rooms/${roomId}/bots`, { method: 'PUT', body: JSON.stringify({ bot_ids: ids }) })
    const state = await api<Snapshot>(`/rooms/${roomId}/state`)
    setSnapshot(s => s ? { ...s, bots: state.bots } : state)
    setModal(null)
  }
  async function created(value: Room | Bot) {
    await refreshLists()
    if (modal === 'room') { setRoomId(value.id); setLeftOpen(false); setModal(null) }
    else {
      // Creation is committed even if joining fails; the Bot remains available in the team picker.
      try { await invite([...activeBots.map(b => b.id), value.id]) }
      catch (e) { setModal(null); setError(`Bot 已创建，但加入房间失败：${(e as Error).message}。请通过“管理队友”重新加入。`) }
    }
  }
  async function loadHistory() {
    if (!snapshot?.messages.length || loadingHistory) return
    setLoadingHistory(true)
    const target = roomId, oldHeight = scroller.current?.scrollHeight || 0
    try {
      const result = await api<{ messages: Message[]; has_more: boolean }>(`/rooms/${target}/messages?before_id=${snapshot.messages[0].id}`)
      setSnapshot(s => s?.room.id === target ? { ...s, messages: sortMessages(merge(s.messages, result.messages)), has_more: result.has_more } : s)
      requestAnimationFrame(() => { if (scroller.current) scroller.current.scrollTop += scroller.current.scrollHeight - oldHeight })
    } catch (e) { setError((e as Error).message) } finally { setLoadingHistory(false) }
  }
  function example(text: string) { setDraft(text); input.current?.focus() }

  return <div className="workspace">
    {(leftOpen || rightOpen) && <div className="drawer-overlay" onClick={() => { setLeftOpen(false); setRightOpen(false) }} />}
    <aside className={`sidebar ${leftOpen ? 'open' : ''}`}><div className="sidebar-brand"><Logo /><button className="icon-btn mobile-only" aria-label="收起房间列表" onClick={() => setLeftOpen(false)}><X size={18} /></button></div>
      <div className="workspace-switch"><span className="workspace-initial">R</span><div><strong>我的工作空间</strong><small>一起，把事情做好。</small></div><span className="workspace-tag">LOCAL</span></div>
      <div className="side-section-label"><span>聊天室 <span className="count">{rooms.length}</span></span><button className="icon-btn" title="创建聊天室" aria-label="创建聊天室" onClick={() => setModal('room')}><Plus size={17} /></button></div>
      <nav className="room-list" aria-label="聊天室列表">{rooms.map(room => <button key={room.id} className={`room-item ${room.id === roomId ? 'active' : ''}`} onClick={() => { setRoomId(room.id); setLeftOpen(false) }}><Hash size={18} /><span>{room.name}</span>{room.id === roomId && <span className="room-active-dot" />}</button>)}{!rooms.length && <p className="empty-small">还没有房间，创建一个开始吧。</p>}</nav>
      <button className="new-room" onClick={() => setModal('room')}><Plus size={16} />新建聊天室</button>
      <div className="sidebar-bottom"><div className="side-guide"><div className="guide-icon"><Sparkles size={18} /></div><h4>让队友接力你的想法</h4><p>输入 @ 唤起 AI 队友，计算、委派、协作都在对话里。</p><button onClick={() => { setModal('invite'); setLeftOpen(false) }}>管理我的队友 <ArrowRight size={13} /></button></div>
        <div className="sidebar-user"><Avatar name={user.nickname} small /><span><strong>{user.nickname}</strong><small><i />在线 · 本地身份</small></span><button className="icon-btn" aria-label="切换昵称" title="切换昵称" onClick={logout}><LogOut size={16} /></button></div>
      </div>
    </aside>

    <main className="main-panel">
      <header className="topbar"><div className="breadcrumb"><button className="icon-btn mobile-only" aria-label="展开房间列表" onClick={() => setLeftOpen(true)}><Menu size={20} /></button><Layers3 size={16} /><span>工作空间</span><ChevronRight size={14} /><strong>聊天室</strong></div>
        <div className="topbar-right"><span className={`mode-pill ${health?.mode === 'live' ? 'live' : ''}`}><i />{health?.mode === 'live' ? 'LIVE MODEL' : 'DEMO / MOCK'}</span><button className="icon-btn detail-toggle" aria-label="展开执行详情" onClick={() => setRightOpen(true)}><Settings2 size={19} /></button></div>
      </header>
      <div className="room-heading"><div className="room-heading-main"><div className="room-symbol"><Hash size={25} /></div><div><h1>{activeRoom?.name || '协作工作空间'}</h1><p>{activeRoom?.description || '为团队创建一个新的讨论空间。'}</p></div></div>
        <div className="room-presence"><div className="avatar-stack">{people.slice(0, 3).map(p => <Avatar key={p.id} name={p.nickname} small />)}</div><span title={people.map(p => p.nickname).join('、')}><Users size={14} />{people.length} 人在线</span></div>
      </div>
      <div className="conversation-info"><span><div className={`connection-dot ${connection}`} />{connection === 'online' ? '实时连接' : connection === 'connecting' ? '正在连接…' : '连接断开 · 自动重连中'}</span><span><BotIcon size={13} />{activeBots.length} 位 AI 队友<span className="info-separator">·</span>消息与执行记录自动保存</span></div>
      {health?.mode === 'demo' && <div className="demo-banner"><Sparkles size={14} /><span><strong>Demo 模式</strong> · 回复由规则生成，工具和 Bot 委派在服务端真实执行。</span></div>}
      {error && <div className="error-banner" role="alert"><CircleAlert size={16} /><span>{error}</span><button onClick={() => { setError(''); setRetry(r => r + 1) }} className="text-btn">重新连接</button><button className="icon-btn" aria-label="关闭错误提示" onClick={() => setError('')}><X size={15} /></button></div>}

      <div className="message-scroll" ref={scroller} onScroll={() => { const el = scroller.current!; nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 140 }}>
        {loading ? <div className="loading-state"><LoaderCircle className="spin" size={25} /><p>正在同步房间消息…</p></div> : <>
          {snapshot?.has_more && <button className="load-history" onClick={loadHistory} disabled={loadingHistory}>{loadingHistory ? <LoaderCircle size={14} className="spin" /> : <Clock3 size={14} />}加载更早的消息</button>}
          <div className="conversation-start"><div className="start-icon"><MessageSquare size={27} /><span><Sparkles size={13} /></span></div><div className="eyebrow">GREAT THINGS START WITH A CONVERSATION</div><h2>协作，从这里开始。</h2><p>和伙伴聊聊，或把一个任务交给 AI 队友。</p>
            {activeBots.length > 0 && <div className="starter-prompts"><button onClick={() => example(`@${activeBots.find(b => b.tools.includes('calculator'))?.name || activeBots[0].name} 计算 (128 + 256) * 3`)}><Terminal size={14} />试试工具计算<ArrowRight size={13} /></button><button onClick={() => example(`@${activeBots.find(b => b.tools.includes('delegate_to_bot'))?.name || activeBots[0].name} 请委派协作计算 99 * 12，并汇总结果`)}><Network size={14} />发起一次协作<ArrowRight size={13} /></button></div>}
          </div>
          <div className="day-divider"><span>房间消息</span></div>
          {snapshot?.messages.map(message => message.kind === 'system' ? <div className={`system-message ${message.task_id ? 'system-error' : ''}`} key={message.id}><CircleAlert size={13} /><span>{message.content}</span>{message.task_id && <button onClick={() => openTask(message.task_id!)}>查看任务</button>}</div> :
            <article className={`message ${message.kind === 'bot' ? 'bot-message' : ''} ${message.sender_id === user.id ? 'own-message' : ''}`} key={message.id} data-testid="chat-message"><Avatar name={message.sender_name} bot={message.kind === 'bot'} /><div className="message-body"><div className="message-meta"><strong>{message.sender_name}</strong>{message.kind === 'bot' && <span className="bot-label">AI 队友</span>}{message.sender_id === user.id && <span className="you-label">你</span>}<time>{time(message.created_at)}</time>{message.mode && <span className="message-mode">{message.mode === 'demo' ? 'DEMO / MOCK' : 'LIVE'}</span>}</div><div className="message-content">{message.content}</div>{message.task_id && <button className="message-trace" onClick={() => openTask(message.task_id!)}><Network size={14} />查看任务与工具记录<ChevronRight size={13} /></button>}</div></article>)}
          {!snapshot?.messages.length && <p className="empty-small centered">还没有消息，发送第一条问候吧。</p>}
          {running.length > 0 && <div className="working-indicator"><div className="working-dots"><i /><i /><i /></div><span>{[...new Set(running.map(t => t.bot_name))].join('、')} 正在处理任务</span><button onClick={() => { setRightTab('tasks'); setRightOpen(true) }}>查看进度<ArrowRight size={13} /></button></div>}
          <div ref={end} />
        </>}
      </div>

      <div className="composer-area"><form className={`composer ${connection !== 'online' ? 'disconnected' : ''}`} onSubmit={send}>
        {mentionOpen && <div className="mention-menu"><div className="mention-menu-title">选择一位 AI 队友 <kbd>Esc 关闭</kbd></div>{suggestions.map(b => <button key={b.id} type="button" onClick={() => mention(b)}><Avatar name={b.name} bot small /><span><strong>{b.name}</strong><small>{b.role}</small></span><AtSign size={14} /></button>)}{!suggestions.length && <p className="empty-small">没有匹配的房间 Bot，可先添加队友。</p>}</div>}
        <textarea ref={input} aria-label="聊天消息" placeholder={activeBots.length ? '写点什么，输入 @ 唤起 AI 队友…' : '写点什么，和房间里的伙伴聊聊…'} value={draft} disabled={!!pending} maxLength={4000} rows={2} onChange={e => { setDraft(e.target.value); const match = e.target.value.match(/@([^\s@]*)$/); setMentionOpen(!!match); setMentionQuery(match?.[1] || '') }} onKeyDown={e => { if (e.key === 'Escape') setMentionOpen(false); if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); if (mentionOpen && suggestions.length) mention(suggestions[0]); else send() } }} />
        <div className="composer-toolbar"><div><button type="button" className={`composer-tool ${mentionOpen ? 'selected' : ''}`} onClick={() => { setMentionOpen(v => !v); setMentionQuery(''); input.current?.focus() }}><AtSign size={16} /><span>提及队友</span></button><span className="composer-divider" /><span className="composer-hint">Enter 发送，Shift + Enter 换行</span></div><button className="send-button" aria-label="发送消息" disabled={!draft.trim() || !!pending || connection !== 'online'}>{pending ? <LoaderCircle size={16} className="spin" /> : <Send size={16} />}<span>发送</span></button></div>
      </form><div className="composer-footer"><span><div className="tiny-dot" />{health?.mode === 'demo' ? 'Demo 回复不代表真实模型能力' : `模型：${health?.model || '连接中'}`}</span><span>{draft.length}/4000</span></div></div>
    </main>

    <aside className={`details-panel ${rightOpen ? 'open' : ''}`}><div className="details-header"><span><Settings2 size={17} />房间工作台</span><button className="icon-btn detail-toggle" aria-label="收起执行详情" onClick={() => setRightOpen(false)}><X size={18} /></button></div>
      <div className="detail-tabs"><button className={rightTab === 'team' ? 'active' : ''} onClick={() => setRightTab('team')}><BotIcon size={15} />AI 队友<span>{activeBots.length}</span></button><button className={rightTab === 'tasks' ? 'active' : ''} onClick={() => setRightTab('tasks')}><Network size={15} />执行记录{running.length > 0 && <i className="tab-dot" />}</button></div>
      <div className="details-scroll">{rightTab === 'team' ? <>
        <div className="section-heading"><div><h3>让对的人，接对的任务</h3><p>房间里的 AI 队友，随时待命。</p></div></div>
        <div className="team-list">{activeBots.map(bot => <details className="bot-card" key={bot.id}><summary><Avatar name={bot.name} bot /><span><strong>{bot.name}</strong><small>{bot.role}</small></span><ChevronDown size={15} /></summary><div className="bot-card-tools">{bot.tools.map(t => <span key={t}>{toolLabels[t]}</span>)}</div><button className="mention-bot" onClick={() => mention(bot)}><AtSign size={13} />提及 {bot.name}<ArrowRight size={13} /></button><div className="bot-prompt"><label>SYSTEM PROMPT</label><p>{bot.system_prompt}</p></div></details>)}{!activeBots.length && <div className="empty-panel"><BotIcon size={28} /><p>这个房间还没有 AI 队友。</p><small>创建 Bot，或从已有队友中添加。</small></div>}</div>
        <div className="team-actions"><button className="secondary" onClick={() => setModal('bot')}><Plus size={15} />创建 Bot</button><button className="secondary" onClick={() => setModal('invite')}><Users size={15} />管理队友</button></div>
        <div className="activity-preview"><div className="section-title"><span><Clock3 size={15} />最近任务</span><button className="text-btn" onClick={() => setRightTab('tasks')}>全部<ChevronRight size={13} /></button></div>{roots.slice(0, 3).map(task => <button className="activity-row" key={task.id} onClick={() => openTask(task.id)}><div><strong>{task.bot_name}</strong><small>{time(task.created_at)}</small></div><Status status={task.status} /></button>)}{!roots.length && <div className="empty-small">还没有执行记录。<br />在对话中 @Bot，开始第一个任务。</div>}</div>
        <div className="workspace-note"><Network size={20} /><h4>每一步协作，都有迹可循</h4><p>工具输入、执行结果与委派链路，都会记录在这里。</p><div><span>最多 2 层委派</span><span>每任务 6 次工具</span></div></div>
      </> : <>
        <div className="section-heading"><h3>任务执行记录</h3><p>最近 50 个主任务及完整协作链路。</p></div>
        {roots.length ? <><label className="task-select-label" htmlFor="task-select">选择任务</label><select id="task-select" value={selected?.id || ''} onChange={e => setSelectedTask(e.target.value)}>{roots.map(t => <option key={t.id} value={t.id}>{t.bot_name} · {time(t.created_at)} · {statusLabels[t.status]}</option>)}</select>{selected && <TaskDetail root={selected} tasks={snapshot?.tasks || []} calls={snapshot?.tool_calls || []} />}</> : <div className="empty-panel"><Network size={30} /><p>等待第一个任务</p><small>输入 @Bot 名称，交给队友来处理。</small></div>}
      </>}</div>
      <div className="details-footer"><span className={`connection-dot ${connection}`} />{connection === 'online' ? '已连接到本地工作空间' : <><WifiOff size={13} />正在恢复连接</>}<ArrowDown size={13} /></div>
    </aside>
    {modal && <Modal title={modal === 'room' ? '为新想法，开一个房间' : modal === 'bot' ? '认识你的新 AI 队友' : '把 AI 队友加入房间'} subtitle={modal === 'bot' ? '赋予角色、设定规则，再给它需要的工具。' : modal === 'invite' ? '勾选后保存，房间里的人就可以 @ 它。' : '邀请伙伴加入，在这里一起把事情做好。'} close={closeModal}>{modal === 'invite' ? <InviteBots bots={allBots} selected={activeBots.map(b => b.id)} save={invite} /> : <CreateForm kind={modal} done={created} />}</Modal>}
  </div>
}

export default function App() {
  const [user, setUser] = useState<User | null>(savedUser)
  return user ? <Chatroom user={user} logout={() => { saveUser(null); setUser(null) }} /> : <Login onLogin={setUser} />
}
