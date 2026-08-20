'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import {
  DEFAULT_SESSION_PERSONA,
  personaToAgentMetadata,
  type SessionPersona,
} from '@/lib/session-persona';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const [persona, setPersona] = useState<SessionPersona>(DEFAULT_SESSION_PERSONA);
  const personaRef = useRef(persona);
  personaRef.current = persona;

  const tokenSource = useMemo(() => {
    const sandboxEndpoint = process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT?.trim();
    if (sandboxEndpoint) {
      return getSandboxTokenSource(appConfig);
    }

    return TokenSource.custom(async () => {
      const current = personaRef.current;
      const res = await fetch('/api/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona: current,
          agent_metadata: personaToAgentMetadata(current),
          room_config: appConfig.agentName
            ? { agents: [{ agent_name: appConfig.agentName }] }
            : undefined,
        }),
      });
      if (!res.ok) {
        const errBody = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(errBody?.error || `Token request failed (${res.status})`);
      }
      return await res.json();
    });
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName
      ? {
          agentName: appConfig.agentName,
          agentMetadata: personaToAgentMetadata(persona),
        }
      : { agentMetadata: personaToAgentMetadata(persona) }
  );

  const handlePersonaChange = useCallback((next: SessionPersona) => {
    setPersona(next);
  }, []);

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController
          appConfig={appConfig}
          persona={persona}
          onPersonaChange={handlePersonaChange}
        />
      </main>
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
