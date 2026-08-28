"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { stopWebSpeech } from "@/features/speaking/services/web-speech";

// Global registry to track any created AudioContext, MediaStream, or SpeechRecognition
const activeMediaStreams = new Set<MediaStream>();
const activeAudioContexts = new Set<AudioContext>();
const activeSpeechRecognitions = new Set<any>();

/**
 * Register a MediaStream for global cleanup tracking
 */
export function registerMediaStream(stream: MediaStream | null) {
  if (!stream) return;
  activeMediaStreams.add(stream);
}

/**
 * Unregister a MediaStream
 */
export function unregisterMediaStream(stream: MediaStream | null) {
  if (!stream) return;
  activeMediaStreams.delete(stream);
}

/**
 * Register an AudioContext for global cleanup tracking
 */
export function registerAudioContext(ctx: AudioContext | null) {
  if (!ctx) return;
  activeAudioContexts.add(ctx);
}

/**
 * Unregister an AudioContext
 */
export function unregisterAudioContext(ctx: AudioContext | null) {
  if (!ctx) return;
  activeAudioContexts.delete(ctx);
}

/**
 * Register a SpeechRecognition instance for global cleanup tracking
 */
export function registerSpeechRecognition(rec: any) {
  if (!rec) return;
  activeSpeechRecognitions.add(rec);
}

/**
 * Unregister a SpeechRecognition instance
 */
export function unregisterSpeechRecognition(rec: any) {
  if (!rec) return;
  activeSpeechRecognitions.delete(rec);
}

/**
 * Unconditionally stop and release all hardware microphone tracks,
 * close all AudioContexts, abort SpeechRecognition, and cancel all speech synthesis across the entire browser tab.
 */
export function releaseAllAudioHardware() {
  if (typeof window === "undefined") return;

  // 1. Cancel any active TTS speech synthesis
  try {
    stopWebSpeech();
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  } catch {}

  // 2. Abort all active SpeechRecognitions
  activeSpeechRecognitions.forEach((rec) => {
    try {
      rec.onstart = null;
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      rec.abort();
    } catch {}
  });
  activeSpeechRecognitions.clear();

  // 3. Stop all tracked MediaStreams
  activeMediaStreams.forEach((stream) => {
    try {
      stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {}
      });
    } catch {}
  });
  activeMediaStreams.clear();

  // 4. Close all tracked AudioContexts
  activeAudioContexts.forEach((ctx) => {
    try {
      if (ctx.state !== "closed") {
        ctx.close().catch(() => {});
      }
    } catch {}
  });
  activeAudioContexts.clear();
}

/**
 * Hook to automatically clean up all audio hardware whenever the user navigates between routes.
 */
export function useGlobalAudioCleanup() {
  const pathname = usePathname();
  const prevPathnameRef = useRef(pathname);

  useEffect(() => {
    if (prevPathnameRef.current !== pathname) {
      prevPathnameRef.current = pathname;
      releaseAllAudioHardware();
    }
  }, [pathname]);

  useEffect(() => {
    const handleBeforeUnload = () => {
      releaseAllAudioHardware();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      releaseAllAudioHardware();
    };
  }, []);
}
