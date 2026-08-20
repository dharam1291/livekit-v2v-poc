import type { AvatarGender, SessionLanguage } from '@/lib/session-persona';
import type { TranscriptTurn } from '@/lib/transcript';

export const CONVERSATION_STORAGE_KEY = 'livekit-v2v-poc:conversations';
export const CONVERSATION_STORE_VERSION = 1;
export const MAX_CONVERSATIONS = 50;

export interface ConversationRecord {
  id: string;
  startedAt: string;
  endedAt: string;
  label: string;
  avatarGender: AvatarGender;
  sessionLanguage: SessionLanguage;
  turns: TranscriptTurn[];
}

interface ConversationStoreDocument {
  version: number;
  conversations: ConversationRecord[];
}

export type ConversationStoreResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string; value: T };

function emptyDoc(): ConversationStoreDocument {
  return { version: CONVERSATION_STORE_VERSION, conversations: [] };
}

function safeParse(raw: string | null): ConversationStoreResult<ConversationStoreDocument> {
  if (!raw) return { ok: true, value: emptyDoc() };
  try {
    const parsed = JSON.parse(raw) as ConversationStoreDocument;
    if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.conversations)) {
      return { ok: false, error: 'Conversation history was corrupted and was reset.', value: emptyDoc() };
    }
    return {
      ok: true,
      value: {
        version: CONVERSATION_STORE_VERSION,
        conversations: parsed.conversations,
      },
    };
  } catch {
    return { ok: false, error: 'Conversation history was corrupted and was reset.', value: emptyDoc() };
  }
}

function readDoc(): ConversationStoreResult<ConversationStoreDocument> {
  if (typeof window === 'undefined') return { ok: true, value: emptyDoc() };
  try {
    return safeParse(window.localStorage.getItem(CONVERSATION_STORAGE_KEY));
  } catch {
    return { ok: false, error: 'Could not read conversation history.', value: emptyDoc() };
  }
}

function writeDoc(doc: ConversationStoreDocument): ConversationStoreResult<true> {
  if (typeof window === 'undefined') return { ok: true, value: true };
  try {
    window.localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(doc));
    return { ok: true, value: true };
  } catch {
    return {
      ok: false,
      error: 'Could not save conversation history (storage full or blocked).',
      value: true,
    };
  }
}

export function listConversations(): ConversationStoreResult<ConversationRecord[]> {
  const result = readDoc();
  const sorted = [...result.value.conversations].sort(
    (a, b) => Date.parse(b.endedAt) - Date.parse(a.endedAt)
  );
  if (result.ok) return { ok: true, value: sorted };
  return { ok: false, error: result.error, value: sorted };
}

export function getConversation(id: string): ConversationStoreResult<ConversationRecord | null> {
  const result = readDoc();
  const found = result.value.conversations.find((c) => c.id === id) ?? null;
  if (!found && result.ok) {
    return { ok: false, error: 'That conversation could not be found.', value: null };
  }
  if (result.ok) return { ok: true, value: found };
  return { ok: false, error: result.error, value: found };
}

export function upsertConversation(
  record: ConversationRecord
): ConversationStoreResult<ConversationRecord> {
  if (!record.turns.length) {
    return { ok: true, value: record };
  }
  const result = readDoc();
  const others = result.value.conversations.filter((c) => c.id !== record.id);
  const next = [record, ...others]
    .sort((a, b) => Date.parse(b.endedAt) - Date.parse(a.endedAt))
    .slice(0, MAX_CONVERSATIONS);
  const write = writeDoc({ version: CONVERSATION_STORE_VERSION, conversations: next });
  if (!write.ok) {
    return { ok: false, error: write.error, value: record };
  }
  if (!result.ok) {
    return { ok: false, error: result.error, value: record };
  }
  return { ok: true, value: record };
}

export function buildConversationLabel(turns: TranscriptTurn[]): string {
  const firstUser = turns.find((t) => t.role === 'user')?.text;
  const firstAgent = turns.find((t) => t.role === 'agent')?.text;
  const raw = (firstUser || firstAgent || 'Conversation').trim();
  return raw.length > 72 ? `${raw.slice(0, 69)}…` : raw;
}
