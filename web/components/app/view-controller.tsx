'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { ConnectionState, RoomEvent } from 'livekit-client';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { useAgentJoinTimeout } from '@/hooks/useAgentJoinTimeout';
import {
  deriveSessionStatus,
  sessionStatusLabel,
  type SessionUiStatus,
} from '@/lib/session-status';
import type { SessionPersona } from '@/lib/session-persona';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear' as const,
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
  persona: SessionPersona;
  onPersonaChange: (persona: SessionPersona) => void;
}

export function ViewController({ appConfig, persona, onPersonaChange }: ViewControllerProps) {
  const { isConnected, start, connectionState, room, end } = useSessionContext();
  const agent = useAgent();
  const { timedOut, failureReason: joinFailure } = useAgentJoinTimeout(30_000);
  const [manualFailure, setManualFailure] = useState<string | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [callStartedAt, setCallStartedAt] = useState<string | null>(null);

  const isConnecting = connectionState === ConnectionState.Connecting;
  const failed = Boolean(manualFailure || joinFailure || timedOut || agent.state === 'failed');

  const status: SessionUiStatus = deriveSessionStatus({
    isConnected: isConnected && !failed,
    isConnecting: isConnecting && !failed,
    failed,
  });

  const failureReason =
    manualFailure ||
    joinFailure ||
    (agent.state === 'failed' ? 'Agent session failed' : null);
  const connectionLabel = sessionStatusLabel(status, failureReason);

  useEffect(() => {
    if (!room) return;
    let sawReconnect = false;

    const onConnectionState = (state: ConnectionState) => {
      if (
        state === ConnectionState.Reconnecting ||
        state === ConnectionState.SignalReconnecting
      ) {
        sawReconnect = true;
        return;
      }
      if (state === ConnectionState.Connected) {
        sawReconnect = false;
        return;
      }
      if (state === ConnectionState.Disconnected && sawReconnect) {
        setManualFailure('Network connection lost — reconnect manually');
        sawReconnect = false;
        end();
      }
    };

    room.on(RoomEvent.ConnectionStateChanged, onConnectionState);
    return () => {
      room.off(RoomEvent.ConnectionStateChanged, onConnectionState);
    };
  }, [end, room]);

  useEffect(() => {
    if (isConnecting) setManualFailure(null);
  }, [isConnecting]);

  useEffect(() => {
    if (isConnected && !failed && !callStartedAt) {
      setCallStartedAt(new Date().toISOString());
    }
    if (!isConnected) {
      setCallStartedAt(null);
    }
  }, [isConnected, failed, callStartedAt]);

  const handleStart = async () => {
    setManualFailure(null);
    setStorageWarning(null);
    try {
      await Promise.resolve(start());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect';
      setManualFailure(message);
    }
  };

  const handleConversationSaved = (warning: string | null) => {
    setStorageWarning(warning);
    setHistoryRefreshKey((k) => k + 1);
  };

  const showWelcome = !isConnected || failed;

  return (
    <AnimatePresence mode="wait">
      {showWelcome && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
          connectionLabel={connectionLabel}
          isConnecting={isConnecting && !failed}
          failureReason={failureReason}
          persona={persona}
          onPersonaChange={onPersonaChange}
          historyRefreshKey={historyRefreshKey}
          storageWarning={storageWarning}
        />
      )}
      {isConnected && !failed && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          preConnectMessage="Connected — allow mic if prompted, then speak. Transcripts appear on the right."
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          avatarGender={persona.avatarGender}
          sessionLanguage={persona.sessionLanguage}
          conversationStartedAt={callStartedAt ?? undefined}
          onConversationSaved={handleConversationSaved}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
