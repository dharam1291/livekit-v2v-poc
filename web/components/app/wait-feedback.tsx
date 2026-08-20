'use client';

import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/shadcn/utils';
import { startWaitSound, stopWaitSound } from '@/lib/wait-sound';

const SHOW_DELAY_MS = 450;

interface WaitFeedbackProps {
  active: boolean;
  className?: string;
  /** Prefer audio when available; visual always shows after delay. */
  enableSound?: boolean;
}

/**
 * Visual (+ optional audio) filler while the agent is thinking.
 * Skips flash for sub-~450ms thinks.
 */
export function WaitFeedback({ active, className, enableSound = true }: WaitFeedbackProps) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    if (!active) {
      setVisible(false);
      stopWaitSound();
      return;
    }

    timerRef.current = setTimeout(() => {
      setVisible(true);
      if (enableSound) {
        void startWaitSound();
      }
    }, SHOW_DELAY_MS);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      stopWaitSound();
    };
  }, [active, enableSound]);

  if (!visible) return null;

  return (
    <div
      className={cn(
        'pointer-events-none flex flex-col items-center gap-2 text-center',
        className
      )}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-1.5">
        <span className="bg-foreground/70 size-2 animate-bounce rounded-full [animation-delay:0ms]" />
        <span className="bg-foreground/70 size-2 animate-bounce rounded-full [animation-delay:120ms]" />
        <span className="bg-foreground/70 size-2 animate-bounce rounded-full [animation-delay:240ms]" />
      </div>
      <p className="text-muted-foreground font-mono text-[10px] tracking-wider uppercase">
        Preparing reply…
      </p>
    </div>
  );
}
