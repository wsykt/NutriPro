/**
 * Real-assembly-chain integration tests for router-bootstrap (v0.3.0).
 *
 * Drives the ACTUAL preset code through the DeepSeek Harness event ordering,
 * taken from `@deepseek-ai/dsh-agent-loop` preStep/turn (verified against
 * 0.1.0-rc.7):
 *
 *   inbox.claim()                       → emits `agent/inbox/claimed` per message
 *   systemPrompt.assemble(...)          → `system-prompt/assemble` waterfall
 *   dispatch.waterfall("agent/pre-step")→ `agent/pre-step` waterfall
 *   session.append('user/message', ...) → `session/event` (per decision.messages)
 *   step(assembly)                      → model request (NOT simulated here)
 *
 * These tests exist because pure-function tests could not see the first-turn
 * classification hole (#13), the dead `session/event` guidance channel
 * (#34/#36), the missing `extractText`/`bandOf` imports (#11), or the extra
 * API call manufactured by inbox re-append guidance (#55).
 */
import assert from 'node:assert/strict'
import test from 'node:test'
import { apply as applyStandard } from './preset/router-standard/router-bootstrap.mjs'
import { apply as applySpec } from './preset/router-spec/router-bootstrap-v1.mjs'
import { classifyTask, sessionMode } from './preset/router-standard/router-core.mjs'

// ── minimal Cordis-shaped context ──────────────────────────────────────────

function makeHarness(applyFn, config) {
  const listeners = new Map()
  const registeredTools = []
  const agentRef = { current: undefined }
  const ctx = {
    on(name, fn) {
      if (!listeners.has(name)) listeners.set(name, [])
      listeners.get(name).push(fn)
      return () => {}
    },
    effect(fn) { fn() },
    get(name) { return name === 'agent' ? agentRef.current : undefined },
    tools: { register(tool) { registeredTools.push(tool) } },
    llm: { stream() { throw new Error('llm.stream must not be called in integration tests') } },
  }
  applyFn(ctx, config)
  return {
    ctx, listeners, registeredTools, agentRef,
    emit(name, ...args) {
      for (const fn of listeners.get(name) ?? []) fn(...args)
    },
    async assemble(initial, context) {
      const fns = listeners.get('system-prompt/assemble') ?? []
      const run = async (i) => (i >= fns.length ? initial : fns[i](initial, context, () => run(i + 1)))
      return run(0)
    },
    async preStep(payload) {
      const fns = listeners.get('agent/pre-step') ?? []
      const base = { kind: 'enter', messages: [...payload.messages] }
      const run = async (i) => (i >= fns.length ? base : fns[i](payload, () => run(i + 1)))
      return run(0)
    },
  }
}

// ── fixtures ───────────────────────────────────────────────────────────────

const SECTIONS = [
  { name: 'harness-identity', text: 'identity', order: -100 },
  { name: 'persona', text: 'You are a helpful software engineer assistant.', order: 0 },
  { name: 'plan-mode', text: 'You are in plan mode.', order: -50 },
  { name: 'tool-guidance', text: 'guidance', order: 100 },
]

const TOOLS = [
  { name: 'bash' }, { name: 'pwsh' }, { name: 'str_replace_editor' },
  { name: 'read' }, { name: 'write' }, { name: 'edit' }, { name: 'glob' }, { name: 'grep' },
]

function baseAssembled() {
  return {
    sections: SECTIONS.map((s) => ({ ...s })),
    tools: TOOLS.map((t) => ({ ...t })),
    contexts: [],
    variables: { provider: 'deepseek-official', model: 'deepseek-v4-flash' },
  }
}

function userMessage(id, text) {
  return { id, role: 'user', source: { kind: 'user' }, content: [{ type: 'text', text }] }
}

function makeSession(events = []) {
  return { id: `session-${Math.random().toString(36).slice(2, 10)}`, header: {}, events: [...events] }
}

/** Mirror the loop: claim → assemble → pre-step, then persist decision.messages. */
async function runFirstStep(h, { message, session }) {
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' } }
  h.agentRef.current = agent
  h.emit('agent/inbox/claimed', { agent, message })
  const assembled = await h.assemble(baseAssembled(), { agent, scope: agent })
  const claimed = [message]
  const decision = await h.preStep({ agent, messages: claimed, turn: 1, step: 1, signal: undefined })
  for (const message of decision.messages) session.events.push({ type: 'user/message', data: message })
  return { agent, assembled, decision }
}

// ── first-turn classification (#13) ────────────────────────────────────────

test('first request classifies the REAL user message (agent/inbox/claimed → assemble)', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession()
  const build = userMessage('m1', '从零开发一个马里奥网页游戏，生成完整实现，构建可运行的网站应用')
  assert.equal(classifyTask(build.content[0].text), 1) // react

  const { assembled, decision } = await runFirstStep(h, { message: build, session })

  // persona-based routing (v0.1.1 restore design): full sections + classified persona
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /hands-on software engineer/)
  assert.equal(assembled.sections.length, SECTIONS.length, 'sections preserved')
  assert.deepEqual(assembled.tools.map((t) => t.name), ['pwsh', 'read', 'write', 'edit'])
  assert.deepEqual(assembled.contexts, [])
  // react is a strong mode → no guide, no extra request manufactured
  assert.deepEqual(decision.messages.map((m) => m.id), ['m1'])
})

test('weak first message gets near-field guidance in the SAME request (#34/#36/#55)', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession()
  const vague = userMessage('m2', '今天天气怎么样')
  assert.equal(classifyTask(vague.content[0].text), 'weak')

  const { assembled, decision } = await runFirstStep(h, { message: vague, session })

  // weak band → WEAK_FLASH persona on the first request (classified, not fallback)
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /decide the task type/)
  assert.equal(decision.messages.length, 2)
  assert.equal(decision.messages[0].id, 'm2')
  assert.equal(decision.messages[1].id, 'router-guide-m2')
  assert.equal(decision.messages[1].role, 'user')
  assert.deepEqual(decision.messages[1].source, { kind: 'plugin', plugin: 'router-bootstrap' })
  assert.match(decision.messages[1].content[0].text, /classify this task/)
})

test('complex weak tasks get the deep-exploration guide', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession()
  // Long (>120 chars) and keyword-free → complex AND weak (internal routing).
  const complex = userMessage('m3', '请帮我看一下这个项目里的各个模块之间的依赖关系是否合理，以及有哪些可以改进的地方，同时给出具体的建议和后续的步骤安排，以便我们能够稳步推进整个工作并且不遗漏任何重要的细节，另外也希望你能说明每一步的理由和可能的风险点，还有哪些地方值得先做验证再决定怎么做')
  assert.equal(classifyTask(complex.content[0].text), 'weak')
  assert.equal(complex.content[0].text.length > 120, true)
  const { decision } = await runFirstStep(h, { message: complex, session })
  assert.equal(decision.messages.length, 2)
  assert.match(decision.messages[1].content[0].text, /Think deeply about the architecture/)
})

test('plugin-origin claimed messages never pin the band or receive guides', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession()
  const approval = { id: 'a1', role: 'user', source: { kind: 'plugin', plugin: 'user-approval' }, content: [{ type: 'text', text: 'The approval policy changed from "ask" to "never"' }] }
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' } }
  h.agentRef.current = agent
  // Real chain: next-step plugin messages are claimed BEFORE the next-turn user message.
  const fix = userMessage('m4', '修复这个仓库里的 bug')
  h.emit('agent/inbox/claimed', { agent, message: approval })
  h.emit('agent/inbox/claimed', { agent, message: fix })
  const assembled = await h.assemble(baseAssembled(), { agent, scope: agent })
  const decision = await h.preStep({ agent, messages: [approval, fix], turn: 1, step: 1 })
  // Classification comes from the REAL user message → spec band → no guide
  assert.equal(sessionMode({ events: [{ type: 'user/message', data: approval }] }), 'weak') // approval alone would be weak
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /^You are a helpful software engineer assistant\.$/)
  assert.deepEqual(decision.messages.map((m) => m.id), ['a1', 'm4']) // no guide for spec band
})

// ── promotion ──────────────────────────────────────────────────────────────

test('standard preset: after the first tool/call the router stops trimming the surface', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession([
    { type: 'user/message', data: userMessage('m6', '从零开发一个马里奥网页游戏') },
    { type: 'tool/call', data: {} },
  ])
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' } }
  h.agentRef.current = agent
  const assembled = await h.assemble(baseAssembled(), { agent, scope: agent })
  assert.equal(assembled.sections.length, SECTIONS.length, 'sections stay full')
  assert.deepEqual(assembled.contexts, [])
  assert.ok(assembled.tools.length === TOOLS.length, 'full tool catalog exposed')
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /hands-on software engineer/)
})

test('spec preset (routerMode: standard): RL first turn, then full assembly returns (#44)', async () => {
  const h = makeHarness(applySpec, { routerMode: 'standard' })
  const session = makeSession()
  const build = userMessage('m7', '从零开发一个马里奥网页游戏')
  const { assembled } = await runFirstStep(h, { message: build, session })
  // RL-interface first turn
  assert.deepEqual(assembled.sections.map((s) => s.name), ['plan-mode', 'router-persona'])
  assert.deepEqual(assembled.tools.map((t) => t.name), ['pwsh', 'str_replace_editor'])
  assert.deepEqual(assembled.contexts, [])

  // promoted: the router stops touching the assembly (full sections restored)
  session.events.push({ type: 'tool/call', data: {} })
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' } }
  h.agentRef.current = agent
  const original = baseAssembled()
  const promoted = await h.assemble(original, { agent, scope: agent })
  assert.equal(promoted, original, 'promoted assembly must be returned untouched')
})

test('spec preset (routerMode: spec): classified persona over the full section list', async () => {
  const h = makeHarness(applySpec, { routerMode: 'spec' })
  const session = makeSession()
  const build = userMessage('m8', '从零开发一个马里奥网页游戏')
  const { assembled } = await runFirstStep(h, { message: build, session })
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /hands-on software engineer/)
  assert.equal(assembled.sections.length, SECTIONS.length)
  assert.deepEqual(assembled.tools.map((t) => t.name), ['pwsh', 'read', 'write', 'edit'])
})

// ── resume safety ──────────────────────────────────────────────────────────

test('resume: a guide already in the durable transcript is never injected twice', async () => {
  const h = makeHarness(applyStandard, {})
  const m = userMessage('m9', '今天天气怎么样')
  const session = makeSession([
    { type: 'user/message', data: m },
    { type: 'user/message', data: { id: 'router-guide-m9', role: 'user', source: { kind: 'plugin', plugin: 'router-bootstrap' }, content: [{ type: 'text', text: 'guide' }] } },
  ])
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' } }
  h.agentRef.current = agent
  const decision = await h.preStep({ agent, messages: [m], turn: 2, step: 1 })
  assert.deepEqual(decision.messages.map((x) => x.id), ['m9'], 'no duplicate guide on resume')
})

// ── legacy session/event capture only ──────────────────────────────────────

test('session/event listener never appends to the inbox (no extra API round-trip, #55)', async () => {
  const h = makeHarness(applyStandard, {})
  const session = makeSession()
  const inbox = { append() { throw new Error('inbox.append must not be called from session/event') } }
  const agent = { session, options: { provider: 'deepseek-official', model: 'deepseek-v4-flash' }, inbox }
  h.agentRef.current = agent
  h.emit('session/event', session, { type: 'user/message', data: userMessage('m10', '今天天气怎么样') })
  // capture fallback still records the first real user message
  const assembled = await h.assemble(baseAssembled(), { agent, scope: agent })
  assert.match(assembled.sections.find((s) => s.name === 'router-persona').text, /decide the task type/)
})

// ── dev tools register ─────────────────────────────────────────────────────

test('router visibility tools are registered', () => {
  const h = makeHarness(applyStandard, {})
  const names = h.registeredTools.map((t) => t.name)
  assert.ok(names.includes('dev_router_status'))
  assert.ok(names.includes('dev_router_mode'))
  assert.ok(names.includes('dev_mode_subagent'))
})
