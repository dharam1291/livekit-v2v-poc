export type AvatarGender = 'male' | 'female';

export type SessionLanguage = 'en' | 'hi' | 'es';

export type ReplyMode = 'standard' | 'voice_to_voice';

export interface SessionPersona {
  avatarGender: AvatarGender;
  sessionLanguage: SessionLanguage;
  replyMode: ReplyMode;
}

export const DEFAULT_SESSION_PERSONA: SessionPersona = {
  avatarGender: 'female',
  sessionLanguage: 'en',
  replyMode: normalizeReplyMode(
    typeof process !== 'undefined'
      ? process.env.NEXT_PUBLIC_DEFAULT_REPLY_MODE
      : undefined
  ),
};

export function normalizeAvatarGender(value: unknown): AvatarGender {
  return value === 'male' ? 'male' : 'female';
}

export function normalizeSessionLanguage(value: unknown): SessionLanguage {
  if (value === 'hi' || value === 'es') return value;
  return 'en';
}

export function normalizeReplyMode(value: unknown): ReplyMode {
  const raw = String(value ?? 'standard')
    .trim()
    .toLowerCase()
    .replace(/-/g, '_');
  if (raw === 'voice_to_voice' || raw === 'v2v' || raw === 'realtime') {
    return 'voice_to_voice';
  }
  return 'standard';
}

export function parseSessionPersona(raw: unknown): SessionPersona {
  const obj = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  return {
    avatarGender: normalizeAvatarGender(obj.avatarGender ?? obj.avatar_gender),
    sessionLanguage: normalizeSessionLanguage(obj.sessionLanguage ?? obj.session_language),
    replyMode: normalizeReplyMode(obj.replyMode ?? obj.reply_mode),
  };
}

/** JSON string for LiveKit agent dispatch metadata. */
export function personaToAgentMetadata(persona: SessionPersona): string {
  return JSON.stringify({
    avatar_gender: persona.avatarGender,
    session_language: persona.sessionLanguage,
    reply_mode: persona.replyMode,
  });
}

export function replyModeLabel(mode: ReplyMode): string {
  return mode === 'voice_to_voice' ? 'Voice-to-voice' : 'Standard';
}
