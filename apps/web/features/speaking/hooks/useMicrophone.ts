import { useCallback, useEffect, useRef, useState } from "react";
import {
  registerMediaStream,
  unregisterMediaStream,
  registerAudioContext,
  unregisterAudioContext,
} from "@/hooks/use-global-audio-cleanup";

export interface UseMicrophoneResult {
  hasPermission: boolean | null;
  isInitializing: boolean;
  isRecording: boolean;
  error: string | null;
  volumeLevel: number;
  stream: MediaStream | null;
  requestPermission: (deviceId?: string) => Promise<boolean>;
  releaseMicrophone: () => void;
  startRecording: () => Promise<boolean>;
  stopRecording: () => Promise<Blob>;
}

export function useMicrophone(): UseMicrophoneResult {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [volumeLevel, setVolumeLevel] = useState(0);

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const animFrameRef = useRef<number | null>(null);
  const lastVolumeTimeRef = useRef<number>(0);

  const releaseMicrophone = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch {}
      mediaRecorderRef.current = null;
    }
    if (streamRef.current) {
      unregisterMediaStream(streamRef.current);
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {}
      });
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      unregisterAudioContext(audioContextRef.current);
      try {
        audioContextRef.current.close();
      } catch {}
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setVolumeLevel(0);
    setIsRecording(false);
  }, []);

  const monitorVolume = useCallback(() => {
    if (!analyserRef.current) return;
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const checkVolume = () => {
      if (!analyserRef.current) return;
      const now = performance.now();
      if (now - lastVolumeTimeRef.current >= 60) {
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(1.0, Math.max(0.0, avg / 100.0));
        setVolumeLevel(normalized);
        lastVolumeTimeRef.current = now;
      }
      animFrameRef.current = requestAnimationFrame(checkVolume);
    };

    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
    }
    animFrameRef.current = requestAnimationFrame(checkVolume);
  }, []);

  const requestPermission = useCallback(
    async (deviceId?: string): Promise<boolean> => {
      setIsInitializing(true);
      setError(null);
      try {
        if (!navigator?.mediaDevices?.getUserMedia) {
          throw new Error("Trình duyệt không hỗ trợ truy cập Microphone.");
        }

        // Reuse active stream if available
        if (streamRef.current && streamRef.current.active) {
          const liveTrack = streamRef.current.getAudioTracks().find((t) => t.readyState === "live");
          if (liveTrack) {
            setHasPermission(true);
            setIsInitializing(false);
            if (!analyserRef.current) monitorVolume();
            return true;
          }
        }

        releaseMicrophone();

        const constraints: MediaStreamConstraints = {
          audio: {
            deviceId: deviceId ? { exact: deviceId } : undefined,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
          },
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;
        registerMediaStream(stream);

        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioCtx();
        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.4;
        source.connect(analyser);

        audioContextRef.current = ctx;
        analyserRef.current = analyser;
        registerAudioContext(ctx);

        monitorVolume();
        setHasPermission(true);
        setIsInitializing(false);
        return true;
      } catch (err: any) {
        console.error("[useMicrophone] Permission error:", err);
        setHasPermission(false);
        setIsInitializing(false);
        const msg =
          err.name === "NotAllowedError" || err.name === "PermissionDeniedError"
            ? "Quyền truy cập Microphone bị từ chối. Hãy cho phép micro trên thanh địa chỉ trình duyệt."
            : err.message || "Không thể khởi tạo Microphone.";
        setError(msg);
        return false;
      }
    },
    [monitorVolume, releaseMicrophone]
  );

  const startRecording = useCallback(async (): Promise<boolean> => {
    try {
      if (!streamRef.current || !streamRef.current.active) {
        const ok = await requestPermission();
        if (!ok) return false;
      }

      if (audioContextRef.current && audioContextRef.current.state === "suspended") {
        try {
          await audioContextRef.current.resume();
        } catch {}
      }

      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        return true;
      }

      audioChunksRef.current = [];

      let mimeType = "audio/webm;codecs=opus";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/webm";
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/ogg;codecs=opus";
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "";
      }

      const recorderOptions: MediaRecorderOptions = {
        audioBitsPerSecond: 128000,
      };
      if (mimeType) {
        recorderOptions.mimeType = mimeType;
      }

      const recorder = new MediaRecorder(streamRef.current!, recorderOptions);

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      return true;
    } catch (e: any) {
      console.error("[useMicrophone] Failed to start recorder:", e);
      setError(e.message || "Không thể bắt đầu thu âm.");
      setIsRecording(false);
      return false;
    }
  }, [requestPermission]);

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setIsRecording(false);
        mediaRecorderRef.current = null;
        resolve(new Blob([], { type: "audio/webm" }));
        return;
      }

      recorder.onstop = () => {
        setIsRecording(false);
        const mimeType = recorder.mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        audioChunksRef.current = [];
        mediaRecorderRef.current = null;
        resolve(blob);
      };

      recorder.onerror = () => {
        setIsRecording(false);
        mediaRecorderRef.current = null;
        resolve(new Blob([], { type: "audio/webm" }));
      };

      try {
        recorder.stop();
      } catch {
        setIsRecording(false);
        mediaRecorderRef.current = null;
        resolve(new Blob([], { type: "audio/webm" }));
      }
    });
  }, []);

  useEffect(() => {
    return () => {
      releaseMicrophone();
    };
  }, [releaseMicrophone]);

  return {
    hasPermission,
    isInitializing,
    isRecording,
    error,
    volumeLevel,
    stream: streamRef.current,
    requestPermission,
    releaseMicrophone,
    startRecording,
    stopRecording,
  };
}
