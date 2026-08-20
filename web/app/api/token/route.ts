import { NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';
import { RoomAgentDispatch, RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

type PersonaBody = {
  avatarGender?: unknown;
  sessionLanguage?: unknown;
  avatar_gender?: unknown;
  session_language?: unknown;
};

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

// don't cache the results
export const revalidate = 0;

function coerceGender(value: unknown): 'male' | 'female' {
  return value === 'male' ? 'male' : 'female';
}

function coerceLanguage(value: unknown): string {
  if (typeof value === 'string' && value.trim()) {
    return value.trim().toLowerCase().split('-')[0] || 'en';
  }
  return 'en';
}

function parsePersona(body: Record<string, unknown>): {
  avatarGender: 'male' | 'female';
  sessionLanguage: string;
} {
  const fromPersona =
    body.persona && typeof body.persona === 'object'
      ? (body.persona as PersonaBody)
      : null;

  let fromAgentMeta: PersonaBody | null = null;
  const agentMetaRaw = body.agent_metadata ?? body.agentMetadata;
  if (typeof agentMetaRaw === 'string' && agentMetaRaw.trim()) {
    try {
      const parsed = JSON.parse(agentMetaRaw) as PersonaBody;
      if (parsed && typeof parsed === 'object') fromAgentMeta = parsed;
    } catch {
      fromAgentMeta = null;
    }
  }

  const source = fromPersona ?? fromAgentMeta ?? {};
  return {
    avatarGender: coerceGender(source.avatarGender ?? source.avatar_gender),
    sessionLanguage: coerceLanguage(source.sessionLanguage ?? source.session_language),
  };
}

export async function POST(req: Request) {
  // make an exception for the vercel preview environment
  if (process.env.NODE_ENV !== 'development' && process.env.IS_VERCEL_PREVIEW !== 'true') {
    throw new Error(
      'THIS API ROUTE IS INSECURE. DO NOT USE THIS ROUTE IN PRODUCTION WITHOUT AN AUTHENTICATION LAYER.'
    );
  }

  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Parse room config from request body (TokenSource may send proto JSON).
    let body: Record<string, unknown> = {};
    try {
      body = (await req.json()) as Record<string, unknown>;
    } catch {
      body = {};
    }

    const persona = parsePersona(body);
    const personaMetadata = JSON.stringify({
      avatar_gender: persona.avatarGender,
      session_language: persona.sessionLanguage,
    });

    const roomConfig = body?.room_config
      ? RoomConfiguration.fromJson(body.room_config as never, { ignoreUnknownFields: true })
      : new RoomConfiguration();

    const agentName = process.env.AGENT_NAME || 'v2v-poc-agent';
    // Always dispatch with persona metadata so TTS voice matches UI selection.
    roomConfig.agents = [
      new RoomAgentDispatch({ agentName, metadata: personaMetadata }),
    ];

    // Generate participant token
    const participantName = 'user';
    const participantIdentity = `poc_user_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `poc-${crypto.randomUUID().slice(0, 8)}`;

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      roomConfig
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'Unknown token error' }, { status: 500 });
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig: RoomConfiguration | undefined
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}
