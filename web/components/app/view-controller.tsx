'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
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
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start, connectionState, room, end } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const agent = useAgent();
  const { timedOut, failureReason: joinFailure } = useAgentJoinTimeout(30_000);
  const [manualFailure, setManualFailure] = useState<string | null>(null);

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

  const handleStart = async () => {
    setManualFailure(null);
    try {
      await Promise.resolve(start());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect';
      setManualFailure(message);
    }
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
        />
      )}
      {isConnected && !failed && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          preConnectMessage="Connected — allow mic if prompted, then speak. Transcripts appear above."
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
