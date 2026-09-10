/**
 * Soft waiting cue from /wait-cue.wav (looped).
 * Falls back silently when Audio / autoplay is blocked.
 */

const WAIT_CUE_SRC = '/wait-cue.wav';

let audioEl: HTMLAudioElement | null = null;
let playing = false;

function getAudio(): HTMLAudioElement | null {
  if (typeof window === 'undefined') return null;
  if (!audioEl) {
    audioEl = new Audio(WAIT_CUE_SRC);
    audioEl.loop = true;
    audioEl.volume = 0.35;
    audioEl.preload = 'auto';
  }
  return audioEl;
}

export async function startWaitSound(): Promise<boolean> {
  if (playing) return true;
  const audio = getAudio();
  if (!audio) return false;
  try {
    audio.currentTime = 0;
    await audio.play();
    playing = true;
    return true;
  } catch {
    stopWaitSound();
    return false;
  }
}

export function stopWaitSound(): void {
  try {
    if (audioEl) {
      audioEl.pause();
      audioEl.currentTime = 0;
    }
  } catch {
    // ignore
  }
  playing = false;
}

export function isWaitSoundPlaying(): boolean {
  return playing;
}
