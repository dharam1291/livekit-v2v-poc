/**
 * Soft waiting tone via Web Audio (no static asset required).
 * Falls back silently when AudioContext / autoplay is blocked.
 */

let audioCtx: AudioContext | null = null;
let oscillator: OscillatorNode | null = null;
let gainNode: GainNode | null = null;
let playing = false;

function getCtx(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return null;
    if (!audioCtx) audioCtx = new Ctx();
    return audioCtx;
  } catch {
    return null;
  }
}

export async function startWaitSound(): Promise<boolean> {
  if (playing) return true;
  const ctx = getCtx();
  if (!ctx) return false;
  try {
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
    oscillator = ctx.createOscillator();
    gainNode = ctx.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = 392;
    gainNode.gain.value = 0.03;
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    oscillator.start();
    // Gentle pulse
    const now = ctx.currentTime;
    gainNode.gain.setValueAtTime(0.02, now);
    gainNode.gain.exponentialRampToValueAtTime(0.04, now + 0.4);
    gainNode.gain.exponentialRampToValueAtTime(0.02, now + 0.8);
    playing = true;
    return true;
  } catch {
    stopWaitSound();
    return false;
  }
}

export function stopWaitSound(): void {
  try {
    oscillator?.stop();
  } catch {
    // already stopped
  }
  try {
    oscillator?.disconnect();
    gainNode?.disconnect();
  } catch {
    // ignore
  }
  oscillator = null;
  gainNode = null;
  playing = false;
}

export function isWaitSoundPlaying(): boolean {
  return playing;
}
