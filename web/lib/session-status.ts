export type SessionUiStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'failed';

export function sessionStatusLabel(
  status: SessionUiStatus,
  failureReason?: string | null
): string {
  switch (status) {
    case 'connecting':
      return 'Connecting';
    case 'connected':
      return 'Connected';
    case 'failed':
      return failureReason ? `Failed: ${failureReason}` : 'Failed';
    case 'disconnected':
    default:
      return 'Disconnected';
  }
}

export function deriveSessionStatus(args: {
  isConnected: boolean;
  isConnecting: boolean;
  failed?: boolean;
}): SessionUiStatus {
  if (args.failed) return 'failed';
  if (args.isConnecting) return 'connecting';
  if (args.isConnected) return 'connected';
  return 'disconnected';
}
