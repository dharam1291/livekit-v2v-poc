'use client';

import { cn } from '@/lib/shadcn/utils';
import type { AvatarGender } from '@/lib/session-persona';

export type AgentAvatarVisualState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface AgentAvatarProps {
  gender: AvatarGender;
  visualState: AgentAvatarVisualState;
  className?: string;
}

function mapAgentState(state: string | undefined): AgentAvatarVisualState {
  if (state === 'speaking') return 'speaking';
  if (state === 'thinking') return 'thinking';
  if (state === 'listening') return 'listening';
  return 'idle';
}

export function agentStateToAvatarVisual(state: string | undefined): AgentAvatarVisualState {
  return mapAgentState(state);
}

export function AgentAvatar({ gender, visualState, className }: AgentAvatarProps) {
  const isSpeaking = visualState === 'speaking';
  const isThinking = visualState === 'thinking';
  const tone = gender === 'male' ? 'from-sky-700 to-slate-800' : 'from-rose-600 to-amber-700';

  return (
    <div
      className={cn('relative flex flex-col items-center justify-center gap-3', className)}
      data-avatar-gender={gender}
      data-avatar-state={visualState}
      aria-label={`${gender} agent avatar, ${visualState}`}
    >
      <div
        className={cn(
          'relative flex size-36 items-center justify-center rounded-full bg-gradient-to-br shadow-lg transition-transform duration-300 md:size-44',
          tone,
          isSpeaking && 'scale-105',
          isThinking && 'animate-pulse'
        )}
      >
        <svg
          viewBox="0 0 120 120"
          className="size-[70%] text-white/95"
          aria-hidden
        >
          <circle cx="60" cy="42" r="22" fill="currentColor" opacity="0.95" />
          <path
            d="M28 98c4-22 20-34 32-34s28 12 32 34"
            fill="currentColor"
            opacity="0.9"
          />
          {gender === 'female' ? (
            <path
              d="M38 28c8-14 36-14 44 0-6 4-14 6-22 6s-16-2-22-6z"
              fill="currentColor"
              opacity="0.55"
            />
          ) : (
            <path
              d="M36 34c6-10 42-10 48 0-10 2-18 3-24 3s-14-1-24-3z"
              fill="currentColor"
              opacity="0.45"
            />
          )}
        </svg>

        {isSpeaking && (
          <div className="absolute inset-0 rounded-full ring-4 ring-white/40 animate-ping" />
        )}
      </div>

      <div className="flex h-6 items-end justify-center gap-1" aria-hidden>
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className={cn(
              'w-1 rounded-full bg-foreground/70 transition-all',
              isSpeaking ? 'animate-bounce' : 'h-1 opacity-30',
              isSpeaking && i % 2 === 0 && 'h-5',
              isSpeaking && i % 2 === 1 && 'h-3',
              isThinking && 'h-2 animate-pulse opacity-60'
            )}
            style={isSpeaking ? { animationDelay: `${i * 80}ms` } : undefined}
          />
        ))}
      </div>
    </div>
  );
}
