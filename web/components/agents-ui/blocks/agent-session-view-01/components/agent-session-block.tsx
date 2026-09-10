'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { RoomEvent, type RemoteParticipant, type Participant } from 'livekit-client';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import {
  AgentAvatar,
  agentStateToAvatarVisual,
} from '@/components/app/agent-avatar';
import { TranscriptPanel, messagesToEntries } from '@/components/app/transcript-panel';
import { SessionTracePanel } from '@/components/app/session-trace-panel';
import { WaitFeedback } from '@/components/app/wait-feedback';
import { cn } from '@/lib/shadcn/utils';
import {
  normalizeAvatarGender,
  normalizeReplyMode,
  normalizeSessionLanguage,
  replyModeLabel,
  type AvatarGender,
  type ReplyMode,
  type SessionLanguage,
} from '@/lib/session-persona';
import {
  buildConversationLabel,
  upsertConversation,
  type ConversationRecord,
} from '@/lib/conversation-store';
import { transcriptEntryToTurn } from '@/lib/transcript';
import {
  SESSION_TRACE_TOPIC,
  parseTracePayload,
  type SessionTraceEvent,
} from '@/lib/session-traces';

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  className?: string;
  avatarGender?: AvatarGender;
  sessionLanguage?: SessionLanguage;
  replyMode?: ReplyMode;
  conversationStartedAt?: string;
  onConversationSaved?: (warning: string | null) => void;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput: _supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,
  avatarGender = 'female',
  sessionLanguage = 'en',
  replyMode = 'standard',
  conversationStartedAt,
  onConversationSaved,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();
  const savedRef = useRef(false);
  const startedAtRef = useRef(conversationStartedAt || new Date().toISOString());
  const entriesRef = useRef(messagesToEntries(messages));

  const [traceEvents, setTraceEvents] = useState<SessionTraceEvent[]>([]);
  const [tracesUnavailable, setTracesUnavailable] = useState(false);
  const [appliedMode, setAppliedMode] = useState<ReplyMode>(replyMode);
  const [requestedMode, setRequestedMode] = useState<ReplyMode>(replyMode);
  const [fallbackReason, setFallbackReason] = useState<string | null>(null);
  const [appliedGender, setAppliedGender] = useState<AvatarGender>(avatarGender);
  const [appliedLanguage, setAppliedLanguage] = useState<SessionLanguage>(sessionLanguage);
  const [defaultsUsed, setDefaultsUsed] = useState(false);

  const applyParticipantAttributes = useCallback((attrs: Record<string, string>) => {
    if (attrs.reply_mode != null && attrs.reply_mode !== '') {
      setAppliedMode(normalizeReplyMode(attrs.reply_mode));
    }
    if (attrs.requested_reply_mode != null && attrs.requested_reply_mode !== '') {
      setRequestedMode(normalizeReplyMode(attrs.requested_reply_mode));
    }
    if (attrs.fallback_reason != null) {
      setFallbackReason(attrs.fallback_reason.trim() || null);
    }
    if (attrs.avatar_gender != null && attrs.avatar_gender !== '') {
      setAppliedGender(normalizeAvatarGender(attrs.avatar_gender));
    }
    if (attrs.session_language != null && attrs.session_language !== '') {
      setAppliedLanguage(normalizeSessionLanguage(attrs.session_language));
    }
    if (attrs.defaults_used != null && attrs.defaults_used !== '') {
      setDefaultsUsed(attrs.defaults_used === 'true' || attrs.defaults_used === '1');
    }
  }, []);

  useEffect(() => {
    const room = session.room;
    if (!room) return;

    const readParticipant = (participant: Participant | RemoteParticipant) => {
      if (participant.attributes && Object.keys(participant.attributes).length > 0) {
        applyParticipantAttributes(participant.attributes as Record<string, string>);
      }
    };

    for (const participant of room.remoteParticipants.values()) {
      readParticipant(participant);
    }

    const onAttributesChanged = (
      changed: Record<string, string>,
      participant: Participant
    ) => {
      if (participant.isLocal) return;
      applyParticipantAttributes({
        ...(participant.attributes as Record<string, string>),
        ...changed,
      });
    };

    const onDataReceived = (
      payload: Uint8Array,
      _participant?: Participant,
      _kind?: unknown,
      topic?: string
    ) => {
      if (topic !== SESSION_TRACE_TOPIC) return;
      const event = parseTracePayload(payload);
      if (!event) {
        setTracesUnavailable(true);
        return;
      }
      if (event.event === 'trace_sink_error') {
        setTracesUnavailable(true);
      }
      setTraceEvents((prev) => [...prev, event]);
    };

    const onParticipantConnected = (participant: RemoteParticipant) => {
      readParticipant(participant);
    };

    room.on(RoomEvent.ParticipantAttributesChanged, onAttributesChanged);
    room.on(RoomEvent.DataReceived, onDataReceived);
    room.on(RoomEvent.ParticipantConnected, onParticipantConnected);

    return () => {
      room.off(RoomEvent.ParticipantAttributesChanged, onAttributesChanged);
      room.off(RoomEvent.DataReceived, onDataReceived);
      room.off(RoomEvent.ParticipantConnected, onParticipantConnected);
    };
  }, [applyParticipantAttributes, session.room]);

  const agentStateLabel =
    agentState === 'listening'
      ? 'Listening — speak now'
      : agentState === 'thinking'
        ? 'Thinking…'
        : agentState === 'speaking'
          ? 'Agent speaking'
          : agentState === 'connecting' ||
              agentState === 'initializing' ||
              agentState === 'pre-connect-buffering'
            ? 'Agent joining…'
            : agentState === 'idle'
              ? 'Connected — waiting'
              : agentState === 'failed'
                ? 'Agent failed'
                : 'In call';

  const modeStatusLabel = replyModeLabel(appliedMode);
  const personaStatusLabel = `${appliedGender}/${appliedLanguage}`;
  const statusMeta = [
    modeStatusLabel,
    personaStatusLabel,
    defaultsUsed ? 'defaults used' : null,
  ]
    .filter(Boolean)
    .join(' · ');

  const showFallbackWarning =
    requestedMode !== appliedMode || Boolean(fallbackReason);

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: false,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  const entries = useMemo(() => messagesToEntries(messages), [messages]);
  entriesRef.current = entries;

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [entries.length]);

  const persistConversation = () => {
    if (savedRef.current) return;
    const turns = entriesRef.current
      .map(transcriptEntryToTurn)
      .filter((t): t is NonNullable<typeof t> => t !== null);
    if (!turns.length) return;
    savedRef.current = true;
    const record: ConversationRecord = {
      id: crypto.randomUUID(),
      startedAt: startedAtRef.current,
      endedAt: new Date().toISOString(),
      label: buildConversationLabel(turns),
      avatarGender,
      sessionLanguage,
      turns,
    };
    const result = upsertConversation(record);
    onConversationSaved?.(result.ok ? null : result.error);
  };

  const handleDisconnect = () => {
    persistConversation();
    session.end();
  };

  useEffect(() => {
    return () => {
      persistConversation();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- persist once on unmount via refs
  }, []);

  const thinking = agentState === 'thinking';

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      <div className="flex h-full min-h-0 flex-col md:flex-row">
        {/* Main call stage */}
        <div className="relative flex min-h-0 min-w-0 flex-1 flex-col">
          <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />
          <div
            className="absolute inset-x-0 top-3 z-20 flex flex-col items-center gap-1 px-3 text-center"
            aria-live="polite"
          >
            <p className="text-muted-foreground font-mono text-xs tracking-wider uppercase">
              {agentStateLabel}
            </p>
            <p className="text-muted-foreground font-mono text-[10px] tracking-wide">
              {statusMeta}
            </p>
            {showFallbackWarning && (
              <p className="max-w-md text-[11px] font-medium text-amber-600 dark:text-amber-400">
                Fallback: requested {replyModeLabel(requestedMode)}, running{' '}
                {replyModeLabel(appliedMode)}
                {fallbackReason ? ` — ${fallbackReason}` : ''}
              </p>
            )}
          </div>

          <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 pb-36 pt-16">
            <AgentAvatar
              gender={appliedGender}
              visualState={agentStateToAvatarVisual(agentState)}
            />
            <WaitFeedback active={thinking} />
          </div>

          <motion.div
            {...BOTTOM_VIEW_MOTION_PROPS}
            className="absolute inset-x-3 bottom-0 z-50 md:inset-x-8"
          >
            {isPreConnectBufferEnabled && (
              <AnimatePresence>
                {messages.length === 0 && (
                  <motion.p
                    key="pre-connect-message"
                    aria-hidden={messages.length > 0}
                    {...SHIMMER_MOTION_PROPS}
                    className="shimmer shimmer-duration-2000 pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold"
                  >
                    {preConnectMessage}
                  </motion.p>
                )}
              </AnimatePresence>
            )}
            <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-10">
              <AgentControlBar
                variant="livekit"
                controls={controls}
                isChatOpen={false}
                isConnected={session.isConnected}
                onDisconnect={handleDisconnect}
              />
            </div>
          </motion.div>
        </div>

        {/* Transcript + session traces (right on desktop, below on narrow) */}
        <div className="border-border flex h-[45%] min-h-[260px] w-full shrink-0 flex-col border-t md:h-full md:w-[min(380px,36vw)] md:border-t-0 md:border-l">
          <div ref={scrollAreaRef} className="min-h-0 flex-1 overflow-hidden">
            <TranscriptPanel
              entries={entries}
              className="h-full border-0"
              emptyLabel="Connected — transcripts will appear here as you talk."
            />
          </div>
          <SessionTracePanel
            events={traceEvents}
            unavailable={tracesUnavailable}
            className="min-h-0 flex-1 border-l-0"
          />
        </div>
      </div>
    </section>
  );
}
