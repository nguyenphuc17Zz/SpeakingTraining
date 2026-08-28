import { useCallback, useEffect, useRef, useState } from "react";
import { RecordingState } from "@/types/audio";
import {
  registerMediaStream,
  unregisterMediaStream,
  registerAudioContext,
  unregisterAudioContext,
} from "@/hooks/use-global-audio-cleanup";

export interface UseAudioRecorderOptions {
  onRecordingStarted?: () => void;
  onRecordingStopped?: (blob: Blob) => void;
  onError?: (err: Error) => void;
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const [state, setState] = useState<RecordingState>("idle");
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const lastVolumeUpdateRef = useRef<number>(0);

  const isStreamValid = (stream: MediaStream | null): boolean => {
    if (!stream || !stream.active) return false;
    const tracks = stream.getAudioTracks();
    if (tracks.length === 0) return false;
    return tracks.some((t) => t.readyState === "live");
  };

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
    setState("idle");
  }, []);

  const monitorVolume = useCallback(() => {
    if (!analyserRef.current) return;
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const checkVolume = () => {
      if (!analyserRef.current) return;
      const now = performance.now();
      // throttle volume updates to 100ms (was 60fps -> 6x renders)
      if (now - lastVolumeUpdateRef.current >= 100) {
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(1.0, Math.max(0.0, avg / 128.0));
        setVolumeLevel(normalized);
        lastVolumeUpdateRef.current = now;
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
      setState("requesting_permission");
      setError(null);
      try {
        if (!navigator?.mediaDevices?.getUserMedia) {
          throw new Error("Trình duyệt không hỗ trợ ghi âm trực tiếp.");
        }

        releaseMicrophone();

        const constraints: MediaStreamConstraints = {
          audio: {
            deviceId: deviceId ? { exact: deviceId } : undefined,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000,
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
        analyser.smoothingTimeConstant = 0.5;
        source.connect(analyser);

        audioContextRef.current = ctx;
        analyserRef.current = analyser;
        registerAudioContext(ctx);

        monitorVolume();
        setHasPermission(true);
        setState("ready");
        return true;
      } catch (err: any) {
        console.error("[useAudioRecorder] Permission error:", err);
        setHasPermission(false);
        setState("permission_denied");
        const msg =
          err.name === "NotAllowedError" || err.name === "PermissionDeniedError"
            ? "Quyền truy cập Microphone bị từ chối. Hãy cấp quyền trong trình duyệt."
            : err.message || "Không thể khởi tạo Microphone.";
        setError(msg);
        options.onError?.(new Error(msg));
        return false;
      }
    },
    [monitorVolume, options, releaseMicrophone]
  );

  const startRecording = useCallback(async () => {
    if (!isStreamValid(streamRef.current)) {
      const ok = await requestPermission(selectedDeviceId || undefined);
      if (!ok) return;
    }

    if (audioContextRef.current && audioContextRef.current.state === "suspended") {
      try {
        await audioContextRef.current.resume();
      } catch (e:any) {
        setError(e?.message || "AudioContext resume failed (autoplay policy)");
        throw e;
      }
    }

    if (!animFrameRef.current && analyserRef.current) {
      monitorVolume();
    }

    try {
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

      const recorder = mimeType
        ? new MediaRecorder(streamRef.current!, { mimeType })
        : new MediaRecorder(streamRef.current!);

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setState("recording");
      options.onRecordingStarted?.();
    } catch (e: any) {
      console.error("[useAudioRecorder] Failed to start recorder:", e);
      setState("error");
      setError(e.message || "Không thể bắt đầu ghi âm.");
      options.onError?.(e);
    }
  }, [isStreamValid, monitorVolume, options, requestPermission, selectedDeviceId]);

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setState("ready");
        mediaRecorderRef.current = null;
        resolve(new Blob([], { type: "audio/webm" }));
        return;
      }

      setState("stopping");

      recorder.onstop = () => {
        setState("ready");
        const mimeType = recorder.mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        options.onRecordingStopped?.(blob);
        mediaRecorderRef.current = null;
        resolve(blob);
      };

      recorder.onerror = (e) => {
        setState("error");
        mediaRecorderRef.current = null;
        reject(e);
      };

      recorder.stop();
    });
  }, [options]);

  useEffect(() => {
    return () => {
      releaseMicrophone();
    };
  }, [releaseMicrophone]);

  return {
    state,
    isRecording: state === "recording",
    hasPermission,
    error,
    volumeLevel,
    selectedDeviceId,
    setSelectedDeviceId,
    requestPermission,
    startRecording,
    stopRecording,
    releaseMicrophone,
  };
}

