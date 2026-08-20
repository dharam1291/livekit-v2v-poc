'use client';

import { useMemo } from 'react';
import type { ReceivedMessage } from '@livekit/components-react';
import { cn } from '@/lib/shadcn/utils';
import { createTranscriptEntry, type TranscriptEntry } from '@/lib/transcript';

interface TranscriptPanelProps {
  messages?: ReceivedMessage[];
  entries?: TranscriptEntry[];
  className?: string;
  emptyLabel?: string;
}

function messagesToEntries(messages: ReceivedMessage[]): TranscriptEntry[] {
  return messages
    .map((message) => {
      const text = (message.message ?? '').trim();
      if (!text) return null;
      let speaker: 'tester' | 'agent';
      if (message.type === 'userTranscript') {
        speaker = 'tester';
      } else if (message.type === 'agentTranscript') {
        speaker = 'agent';
      } else {
        speaker = message.from?.isLocal ? 'tester' : 'agent';
      }
      return createTranscriptEntry({
        text,
        speaker,
        turnId: message.id,
      });
    })
    .filter((e): e is TranscriptEntry => e !== null);
}

/**
 * Dedicated live / history transcript list for tester/agent turns.
 */
export function TranscriptPanel({
  messages,
  entries: entriesProp,
  className,
  emptyLabel = 'Transcripts will appear here during the call.',
}: TranscriptPanelProps) {
  const entries = useMemo(() => {
    if (entriesProp) return entriesProp;
    if (messages) return messagesToEntries(messages);
    return [];
  }, [entriesProp, messages]);

  return (
    <aside
      className={cn(
        'border-border bg-background/80 flex h-full min-h-0 flex-col border-l backdrop-blur-sm',
        className
      )}
      aria-label="Conversation transcript"
    >
      <header className="border-border shrink-0 border-b px-4 py-3">
        <h2 className="font-mono text-xs tracking-wider uppercase">Transcript</h2>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {entries.length === 0 ? (
          <p className="text-muted-foreground text-xs leading-5">{emptyLabel}</p>
        ) : (
          <ul className="space-y-3">
            {entries.map((entry) => (
              <li key={entry.entryId} className="text-left text-sm">
                <span className="text-muted-foreground font-mono text-[10px] tracking-wide uppercase">
                  {entry.speaker === 'tester' ? 'You' : 'Agent'}
                  {entry.toolName ? ` · ${entry.toolName}` : ''}
                </span>
                <p className="text-foreground mt-0.5 leading-5">{entry.text}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

export { messagesToEntries };
