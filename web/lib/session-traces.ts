export const SESSION_TRACE_TOPIC = 'session.trace';

export interface SessionTraceEvent {
  session_id?: string;
  ts?: string;
  event: string;
  turn_index?: number | null;
  attrs?: Record<string, unknown>;
  t_mono?: number;
}

export function parseTracePayload(data: Uint8Array | string): SessionTraceEvent | null {
  try {
    const text =
      typeof data === 'string' ? data : new TextDecoder().decode(data);
    const parsed = JSON.parse(text) as SessionTraceEvent;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.event !== 'string') {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function formatTraceLine(ev: SessionTraceEvent): string {
  const turn =
    ev.turn_index === null || ev.turn_index === undefined ? '' : ` t${ev.turn_index}`;
  const mode = ev.attrs?.actual_reply_mode ?? ev.attrs?.reply_mode;
  const modeBit = mode ? ` [${String(mode)}]` : '';
  const gender = ev.attrs?.avatar_gender ? ` ${String(ev.attrs.avatar_gender)}` : '';
  const lang = ev.attrs?.session_language ? `/${String(ev.attrs.session_language)}` : '';
  const fallback = ev.attrs?.fallback_reason
    ? ` fallback=${String(ev.attrs.fallback_reason)}`
    : '';
  return `${ev.ts ?? ''}${turn} ${ev.event}${modeBit}${gender}${lang}${fallback}`.trim();
}
