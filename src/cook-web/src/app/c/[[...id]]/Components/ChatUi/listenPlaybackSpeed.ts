/** Playback speed control for listen mode. */

export type ListenPlaybackSpeed = 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 2.0;

export const LISTEN_PLAYBACK_SPEED_OPTIONS: ListenPlaybackSpeed[] = [
  0.5, 0.75, 1.0, 1.25, 1.5, 2.0,
];

const STORAGE_KEY = 'listen-playback-speed';

export function readListenPlaybackSpeedFromStorage(): ListenPlaybackSpeed {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = parseFloat(stored) as ListenPlaybackSpeed;
      if (LISTEN_PLAYBACK_SPEED_OPTIONS.includes(parsed)) {
        return parsed;
      }
    }
  } catch {
    // ignore
  }
  return 1.0;
}

export function writeListenPlaybackSpeedToStorage(speed: ListenPlaybackSpeed): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(speed));
  } catch {
    // ignore
  }
}

export function formatListenPlaybackSpeed(speed: ListenPlaybackSpeed): string {
  return `${speed}x`;
}

export function applyListenPlaybackSpeedToAudioElement(
  audioEl: HTMLAudioElement | null,
  speed: ListenPlaybackSpeed,
): void {
  if (audioEl) {
    audioEl.playbackRate = speed;
  }
}
