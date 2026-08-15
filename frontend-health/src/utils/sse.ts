/**
 * SSE（Server-Sent Events）解析工具
 *
 * 从 api/index.ts 的 consultStream 中抽取，消除流式循环与尾部处理的重复解析逻辑，
 * 并使其可独立单测。协议：事件块以空行分隔，块内为 "event: X" / "data: Y" 行，
 * 允许多行 data 拼接。
 */

export interface SSEParsedEvent {
  /** 事件类型：thinking / delta / done / error / message（默认） */
  event: string
  /** 原始 data 文本（JSON 字符串或纯文本） */
  data: string
}

/** 解析单个事件块；无 data 内容时返回 null */
export function parseSSEBlock(block: string): SSEParsedEvent | null {
  let event = 'message'
  let dataStr = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataStr += line.slice(5).trim()
    }
  }
  if (!dataStr) return null
  return { event, data: dataStr }
}

/**
 * 从累积缓冲中提取所有完整事件（以空行 \n\n 为界）。
 *
 * @param buffer 累积的原始文本
 * @returns { events, rest }：完整事件列表 + 尚未完整的剩余文本（需拼入下一次读取）
 */
export function extractSSEEvents(buffer: string): { events: SSEParsedEvent[]; rest: string } {
  const events: SSEParsedEvent[] = []
  let rest = buffer
  let idx: number
  while ((idx = rest.indexOf('\n\n')) >= 0) {
    const block = rest.slice(0, idx)
    rest = rest.slice(idx + 2)
    const parsed = parseSSEBlock(block)
    if (parsed) events.push(parsed)
  }
  return { events, rest }
}

/** 将 SSE 事件 data 解析为 JSON（失败时回退为原始文本对象） */
export function parseSSEPayload(data: string): Record<string, unknown> {
  try {
    const parsed: unknown = JSON.parse(data)
    return typeof parsed === 'object' && parsed !== null
      ? (parsed as Record<string, unknown>)
      : { content: data }
  } catch {
    return { content: data }
  }
}
