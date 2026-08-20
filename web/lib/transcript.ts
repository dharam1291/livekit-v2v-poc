export type TranscriptSpeaker = 'tester' | 'agent';

export interface TranscriptEntry {
  entryId: string;
  turnId: string;
  speaker: TranscriptSpeaker;
  text: string;
  createdAt: number;
  toolName?: string | null;
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
