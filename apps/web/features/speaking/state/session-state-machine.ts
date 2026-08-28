import { RecordingState } from "../types";

export interface StateMachineContext {
  state: RecordingState;
  errorMessage?: string | null;
}

export function canTransition(from: RecordingState, to: RecordingState): boolean {
  const allowedTransitions: Record<RecordingState, RecordingState[]> = {
    idle: ["requesting_permission", "error"],
    requesting_permission: ["ready", "permission_denied", "error", "idle"],
    permission_denied: ["requesting_permission", "idle"],
    ready: ["listening", "paused", "ended", "error", "idle"],
    listening: ["processing_stt", "paused", "ended", "error", "idle"],
    processing_stt: ["ai_thinking", "listening", "error", "ended"],
    ai_thinking: ["ai_speaking", "listening", "error", "ended"],
    ai_speaking: ["listening", "paused", "ended", "error"],
    paused: ["listening", "ended", "idle"],
    ended: ["idle", "requesting_permission"],
    error: ["idle", "requesting_permission", "listening"],
  };

  return allowedTransitions[from]?.includes(to) ?? false;
}

export function getStatusColor(state: RecordingState): {
  badgeBg: string;
  badgeText: string;
  dotColor: string;
  label: string;
} {
  switch (state) {
    case "listening":
      return {
        badgeBg: "bg-emerald-500/10 border-emerald-500/30",
        badgeText: "text-emerald-400",
        dotColor: "bg-emerald-400 animate-pulse",
        label: "Listening (聞いています)",
      };
    case "processing_stt":
      return {
        badgeBg: "bg-amber-500/10 border-amber-500/30",
        badgeText: "text-amber-400",
        dotColor: "bg-amber-400 animate-pulse",
        label: "Transcribing Speech (文字起こし中)",
      };
    case "ai_thinking":
      return {
        badgeBg: "bg-indigo-500/10 border-indigo-500/30",
        badgeText: "text-indigo-400",
        dotColor: "bg-indigo-400 animate-pulse",
        label: "AI Thinking (考え中)",
      };
    case "ai_speaking":
      return {
        badgeBg: "bg-primary/10 border-primary/30",
        badgeText: "text-primary",
        dotColor: "bg-primary animate-ping",
        label: "AI Speaking (話しています)",
      };
    case "paused":
      return {
        badgeBg: "bg-slate-500/10 border-slate-500/30",
        badgeText: "text-muted-foreground",
        dotColor: "bg-slate-400",
        label: "Paused (一時停止)",
      };
    case "ready":
      return {
        badgeBg: "bg-teal-500/10 border-teal-500/30",
        badgeText: "text-teal-400",
        dotColor: "bg-teal-400",
        label: "Microphone Ready (準備完了)",
      };
    case "requesting_permission":
      return {
        badgeBg: "bg-blue-500/10 border-blue-500/30",
        badgeText: "text-blue-400",
        dotColor: "bg-blue-400 animate-spin",
        label: "Requesting Mic (マイク確認中)",
      };
    case "permission_denied":
      return {
        badgeBg: "bg-destructive/10 border-destructive/30",
        badgeText: "text-destructive",
        dotColor: "bg-destructive",
        label: "Mic Denied (マイク未許可)",
      };
    case "error":
      return {
        badgeBg: "bg-destructive/20 border-destructive/40",
        badgeText: "text-destructive",
        dotColor: "bg-destructive",
        label: "Session Error",
      };
    case "ended":
      return {
        badgeBg: "bg-muted border-border",
        badgeText: "text-foreground",
        dotColor: "bg-slate-500",
        label: "Session Completed (終了)",
      };
    default:
      return {
        badgeBg: "bg-card border-border",
        badgeText: "text-muted-foreground",
        dotColor: "bg-slate-600",
        label: "Idle (待機中)",
      };
  }
}
