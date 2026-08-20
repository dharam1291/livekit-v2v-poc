export type AvatarGender = 'male' | 'female';

export type SessionLanguage = 'en' | 'hi' | 'es';

export interface SessionPersona {
  avatarGender: AvatarGender;
  sessionLanguage: SessionLanguage;
}

export const DEFAULT_SESSION_PERSONA: SessionPersona = {
  avatarGender: 'female',
  sessionLanguage: 'en',
};

export function normalizeAvatarGender(value: unknown): AvatarGender {
  return value === 'male' ? 'male' : 'female';
}

export function normalizeSessionLanguage(value: unknown): SessionLanguage {
  if (value === 'hi' || value === 'es') return value;
  return 'en';
}

export function parseSessionPersona(raw: unknown): SessionPersona {
  const obj = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  return {
    avatarGender: normalizeAvatarGender(obj.avatarGender ?? obj.avatar_gender),
    sessionLanguage: normalizeSessionLanguage(obj.sessionLanguage ?? obj.session_language),
  };
}

/** JSON string for LiveKit agent dispatch metadata. */
export function personaToAgentMetadata(persona: SessionPersona): string {
  return JSON.stringify({
    avatar_gender: persona.avatarGender,
    session_language: persona.sessionLanguage,
  });
}
