import { describe, it, expect } from 'vitest'
import { parseSSEBlock, extractSSEEvents, parseSSEPayload } from '@/utils/sse'

describe('parseSSEBlock', () => {
  it('解析 event + data', () => {
    expect(parseSSEBlock('event: delta\ndata: 你好')).toEqual({ event: 'delta', data: '你好' })
  })

  it('未声明 event 时默认为 message', () => {
    expect(parseSSEBlock('data: {"a":1}')).toEqual({ event: 'message', data: '{"a":1}' })
  })

  it('无 data 内容时返回 null', () => {
    expect(parseSSEBlock('event: ping')).toBeNull()
  })

  it('多行 data 拼接', () => {
    expect(parseSSEBlock('data: {"a":1}\ndata: {"b":2}')).toEqual({
      event: 'message',
      data: '{"a":1}{"b":2}'
    })
  })
})

describe('extractSSEEvents', () => {
  it('提取多个完整事件并返回剩余缓冲', () => {
    const buffer = 'event: delta\ndata: 好\n\nevent: done\ndata: {"ok":true}\n\nevent: delta\ndata: 未完成'
    const { events, rest } = extractSSEEvents(buffer)
    expect(events).toHaveLength(2)
    expect(events[0]).toEqual({ event: 'delta', data: '好' })
    expect(events[1]).toEqual({ event: 'done', data: '{"ok":true}' })
    expect(rest).toBe('event: delta\ndata: 未完成')
  })

  it('无完整事件时 events 为空、rest 原样保留', () => {
    const { events, rest } = extractSSEEvents('event: delta\ndata: 半')
    expect(events).toEqual([])
    expect(rest).toBe('event: delta\ndata: 半')
  })

  it('空缓冲返回空', () => {
    const { events, rest } = extractSSEEvents('')
    expect(events).toEqual([])
    expect(rest).toBe('')
  })

  it('空行（无 data）不产生事件', () => {
    const { events } = extractSSEEvents('event: ping\n\nevent: delta\ndata: x\n\n')
    expect(events).toHaveLength(1)
    expect(events[0].event).toBe('delta')
  })
})

describe('parseSSEPayload', () => {
  it('JSON 字符串解析为对象', () => {
    expect(parseSSEPayload('{"content":"hi","mode":"full"}')).toEqual({ content: 'hi', mode: 'full' })
  })

  it('非 JSON 文本回退为 content 对象', () => {
    expect(parseSSEPayload('纯文本内容')).toEqual({ content: '纯文本内容' })
  })
})
