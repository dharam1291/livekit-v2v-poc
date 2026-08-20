export type TranscriptSpeaker = 'tester' | 'agent';

export interface TranscriptEntry {
  entryId: string;
  turnId: string;
  speaker: TranscriptSpeaker;
  text: string;
  createdAt: number;
  toolName?: string | null;
}

/** Persistence-ready turn shape (ISO timestamps) used by conversation history. */
export interface TranscriptTurn {
  id: string;
  role: 'user' | 'agent';
  text: string;
  createdAt: string;
}

export function toTranscriptSpeaker(isLocal: boolean | undefined): TranscriptSpeaker {
  return isLocal ? 'tester' : 'agent';
}

export function createTranscriptEntry(args: {
  text: string;
  speaker: TranscriptSpeaker;
  toolName?: string | null;
  turnId?: string;
}): TranscriptEntry {
  const turnId = args.turnId ?? crypto.randomUUID();
  return {
    entryId: crypto.randomUUID(),
    turnId,
    speaker: args.speaker,
    text: args.text.trim(),
    createdAt: Date.now(),
    toolName: args.toolName ?? null,
  };
}

export function transcriptEntryToTurn(entry: TranscriptEntry): TranscriptTurn | null {
  const text = entry.text.trim();
  if (!text) return null;
  return {
    id: entry.entryId,
    role: entry.speaker === 'tester' ? 'user' : 'agent',
    text,
    createdAt: new Date(entry.createdAt).toISOString(),
  };
}

export function speakerFromMessage(isLocal: boolean | undefined): TranscriptSpeaker {
  return toTranscriptSpeaker(isLocal);
}
