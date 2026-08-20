'use client';

import type { TranscriptEntry } from '@/lib/transcript';

interface TranscriptPanelProps {
  entries: TranscriptEntry[];
  className?: string;
}

/**
 * Compact live transcript list for tester/agent turns (testing UI).
 */
export function TranscriptPanel({ entries, className }: TranscriptPanelProps) {
  if (entries.length === 0) {
    return (
      <div className={className}>
        <p className="text-muted-foreground text-xs">Transcripts will appear here during the call.</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <ul className="space-y-2">
        {entries.map((entry) => (
          <li key={entry.entryId} className="text-left text-sm">
            <span className="font-mono text-xs tracking-wide uppercase opacity-70">
              {entry.speaker}
              {entry.toolName ? ` · ${entry.toolName}` : ''}
            </span>
            <p className="text-foreground leading-5">{entry.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
