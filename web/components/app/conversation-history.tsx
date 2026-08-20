'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ConversationRecord } from '@/lib/conversation-store';
import { getConversation, listConversations } from '@/lib/conversation-store';
import { Button } from '@/components/ui/button';
import { TranscriptPanel } from '@/components/app/transcript-panel';
import type { TranscriptEntry } from '@/lib/transcript';

interface ConversationHistoryProps {
  refreshKey?: number;
  onStorageWarning?: (message: string | null) => void;
}

export function ConversationHistory({ refreshKey = 0, onStorageWarning }: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<ConversationRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    const listed = listConversations();
    setConversations(listed.value);
    onStorageWarning?.(listed.ok ? null : listed.error);
  }, [refreshKey, onStorageWarning]);

  const selected = useMemo(() => {
    if (!selectedId) return null;
    return conversations.find((c) => c.id === selectedId) ?? null;
  }, [conversations, selectedId]);

  const detailEntries: TranscriptEntry[] = useMemo(() => {
    if (!selected) return [];
    return selected.turns.map((turn) => ({
      entryId: turn.id,
      turnId: turn.id,
      speaker: turn.role === 'user' ? 'tester' : 'agent',
      text: turn.text,
      createdAt: Date.parse(turn.createdAt) || Date.now(),
    }));
  }, [selected]);

  const openConversation = (id: string) => {
    const result = getConversation(id);
    if (!result.ok) {
      setDetailError(result.error);
      setSelectedId(null);
      return;
    }
    if (!result.value) {
      setDetailError('That conversation could not be loaded.');
      setSelectedId(null);
      return;
    }
    setDetailError(null);
    setSelectedId(id);
  };

  return (
    <section className="mt-10 w-full max-w-lg text-left" aria-label="Previous conversations">
      <h2 className="mb-2 font-mono text-xs tracking-wider uppercase">Previous conversations</h2>

      {conversations.length === 0 ? (
        <p className="text-muted-foreground text-sm leading-6">
          No previous conversations yet. Start a call to build your history here.
        </p>
      ) : (
        <ul className="border-border divide-y rounded-lg border">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className="hover:bg-muted/50 flex w-full flex-col gap-0.5 px-3 py-3 text-left transition-colors"
                onClick={() => openConversation(c.id)}
              >
                <span className="text-foreground line-clamp-2 text-sm font-medium">{c.label}</span>
                <span className="text-muted-foreground font-mono text-[10px] tracking-wide uppercase">
                  {new Date(c.endedAt).toLocaleString()} · {c.avatarGender} · {c.sessionLanguage}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {detailError && (
        <p className="text-destructive mt-3 text-sm" role="alert">
          {detailError}
        </p>
      )}

      {selected && (
        <div className="border-border mt-4 overflow-hidden rounded-lg border">
          <div className="flex items-center justify-between gap-2 border-b px-3 py-2">
            <p className="text-sm font-medium">{selected.label}</p>
            <Button type="button" variant="ghost" size="sm" onClick={() => setSelectedId(null)}>
              Close
            </Button>
          </div>
          <TranscriptPanel
            entries={detailEntries}
            className="max-h-72 border-0"
            emptyLabel="This conversation has no transcript turns."
          />
        </div>
      )}
    </section>
  );
}
