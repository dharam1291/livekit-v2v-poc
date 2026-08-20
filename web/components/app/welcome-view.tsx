'use client';

import { Button } from '@/components/ui/button';
import { ConversationHistory } from '@/components/app/conversation-history';
import type { AvatarGender, SessionLanguage, SessionPersona } from '@/lib/session-persona';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  connectionLabel?: string;
  isConnecting?: boolean;
  failureReason?: string | null;
  persona: SessionPersona;
  onPersonaChange: (persona: SessionPersona) => void;
  historyRefreshKey?: number;
  storageWarning?: string | null;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  connectionLabel = 'Disconnected',
  isConnecting = false,
  failureReason = null,
  persona,
  onPersonaChange,
  historyRefreshKey = 0,
  storageWarning = null,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const setGender = (avatarGender: AvatarGender) =>
    onPersonaChange({ ...persona, avatarGender });
  const setLanguage = (sessionLanguage: SessionLanguage) =>
    onPersonaChange({ ...persona, sessionLanguage });

  return (
    <div ref={ref} className="relative min-h-svh w-full overflow-y-auto">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(56,120,180,0.18),_transparent_55%),radial-gradient(ellipse_at_bottom_right,_rgba(180,90,60,0.12),_transparent_50%)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.35] [background-image:linear-gradient(to_right,rgba(0,0,0,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.04)_1px,transparent_1px)] [background-size:28px_28px] dark:opacity-[0.2] dark:[background-image:linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)]"
      />

      <section className="relative mx-auto flex max-w-lg flex-col items-center px-6 py-16 text-center">
        <p className="text-muted-foreground mb-3 font-mono text-[10px] tracking-[0.25em] uppercase">
          Voice · Live · Local
        </p>
        <h1 className="text-foreground mb-3 text-4xl font-semibold tracking-tight sm:text-5xl">
          LiveKit Voice
        </h1>
        <p className="text-muted-foreground mb-8 max-w-md text-sm leading-6">
          Talk with a local agent, watch the transcript beside the call, and reopen earlier
          conversations from this device.
        </p>

        <p
          className="text-muted-foreground mb-4 font-mono text-xs tracking-wider uppercase"
          aria-live="polite"
        >
          Status: {connectionLabel}
        </p>

        {failureReason && (
          <p className="text-destructive mb-4 max-w-prose text-sm" role="alert">
            {failureReason}
          </p>
        )}

        {storageWarning && (
          <p className="text-amber-700 dark:text-amber-400 mb-4 max-w-prose text-sm" role="status">
            {storageWarning}
          </p>
        )}

        <div className="mb-6 grid w-full max-w-md gap-4 text-left">
          <fieldset>
            <legend className="mb-2 font-mono text-[10px] tracking-wider uppercase">
              Agent avatar
            </legend>
            <div className="flex gap-2">
              {(['female', 'male'] as AvatarGender[]).map((g) => (
                <Button
                  key={g}
                  type="button"
                  variant={persona.avatarGender === g ? 'default' : 'outline'}
                  size="sm"
                  className="flex-1 capitalize"
                  onClick={() => setGender(g)}
                  disabled={isConnecting}
                >
                  {g}
                </Button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 font-mono text-[10px] tracking-wider uppercase">
              Language
            </legend>
            <div className="flex gap-2">
              {(
                [
                  { code: 'en', label: 'English' },
                  { code: 'hi', label: 'Hindi' },
                  { code: 'es', label: 'Spanish' },
                ] as const
              ).map((lang) => (
                <Button
                  key={lang.code}
                  type="button"
                  variant={persona.sessionLanguage === lang.code ? 'default' : 'outline'}
                  size="sm"
                  className="flex-1"
                  onClick={() => setLanguage(lang.code)}
                  disabled={isConnecting}
                >
                  {lang.label}
                </Button>
              ))}
            </div>
          </fieldset>
        </div>

        <Button
          size="lg"
          onClick={onStartCall}
          disabled={isConnecting}
          className="w-full max-w-xs rounded-full font-mono text-xs font-bold tracking-wider uppercase"
        >
          {isConnecting ? 'Connecting…' : startButtonText}
        </Button>

        <p className="text-muted-foreground mt-6 max-w-prose text-xs leading-5">
          Allow the microphone when prompted. Agent logs stream in the{' '}
          <code className="font-mono">./start_app.sh</code> terminal.
        </p>

        <ConversationHistory refreshKey={historyRefreshKey} />
      </section>
    </div>
  );
};
