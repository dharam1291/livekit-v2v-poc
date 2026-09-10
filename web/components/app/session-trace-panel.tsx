'use client';

import { formatTraceLine, type SessionTraceEvent } from '@/lib/session-traces';
import { cn } from '@/lib/shadcn/utils';

const JAEGER_UI =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_JAEGER_UI_URL?.trim()) ||
  'http://localhost:16686';

interface SessionTracePanelProps {
  events: SessionTraceEvent[];
  unavailable?: boolean;
  className?: string;
}

export function SessionTracePanel({
  events,
  unavailable = false,
  className,
}: SessionTracePanelProps) {
  return (
    <aside
      className={cn(
        'border-border bg-background/80 flex min-h-0 flex-col border-t md:border-t-0 md:border-l',
        className
      )}
      aria-label="Session traces"
    >
      <header className="border-border flex items-center justify-between gap-2 border-b px-3 py-2">
        <h2 className="font-mono text-[10px] tracking-wider uppercase">Session traces</h2>
        <div className="flex items-center gap-2">
          <a
            href={JAEGER_UI}
            target="_blank"
            rel="noreferrer"
            className="text-foreground/80 hover:text-foreground font-mono text-[10px] underline-offset-2 hover:underline"
          >
            Jaeger
          </a>
          <span className="text-muted-foreground font-mono text-[10px]">{events.length}</span>
        </div>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
        {unavailable ? (
          <p className="text-muted-foreground text-xs" role="status">
            Live timeline unavailable — call continues. Check Jaeger if OTLP is up.
          </p>
        ) : events.length === 0 ? (
          <p className="text-muted-foreground text-xs">
            Waiting for timeline events… Full history also in{' '}
            <a
              href={JAEGER_UI}
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-2"
            >
              Jaeger
            </a>
            .
          </p>
        ) : (
          <ul className="space-y-1.5 font-mono text-[10px] leading-4">
            {events.map((ev, idx) => (
              <li key={`${ev.ts ?? 't'}-${ev.event}-${idx}`} className="text-muted-foreground">
                {formatTraceLine(ev)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
