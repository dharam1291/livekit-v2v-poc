'use client';

import { useEffect, useRef, useState } from 'react';
import { useAgent, useSessionContext } from '@livekit/components-react';

const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Fail the session if the agent never becomes ready within ~30s after connect.
 */
export function useAgentJoinTimeout(timeoutMs = DEFAULT_TIMEOUT_MS) {
  const { isConnected, end } = useSessionContext();
  const agent = useAgent();
  const [timedOut, setTimedOut] = useState(false);
  const [failureReason, setFailureReason] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!isConnected) {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = null;
      setTimedOut(false);
      setFailureReason(null);
      return;
    }

    const agentReady =
      agent.state === 'listening' ||
      agent.state === 'thinking' ||
      agent.state === 'speaking';

    if (agentReady) {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = null;
      return;
    }

    if (timerRef.current) return;

    timerRef.current = setTimeout(() => {
      setTimedOut(true);
      setFailureReason('Agent did not join within 30 seconds');
      end();
    }, timeoutMs);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = null;
    };
  }, [agent.state, end, isConnected, timeoutMs]);

  return { timedOut, failureReason };
}
