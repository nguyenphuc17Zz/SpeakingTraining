"use client";

import { useCallback, useEffect, useState } from "react";
import { AudioDeviceInfo } from "@/types/audio";

export function useAudioDevices() {
  const [audioInputDevices, setAudioInputDevices] = useState<AudioDeviceInfo[]>([]);
  const [audioOutputDevices, setAudioOutputDevices] = useState<AudioDeviceInfo[]>([]);
  const [supportsOutputSelection, setSupportsOutputSelection] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);

  const enumerateDevices = useCallback(async () => {
    if (!navigator?.mediaDevices?.enumerateDevices) return;

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs: AudioDeviceInfo[] = [];
      const outputs: AudioDeviceInfo[] = [];

      let hasLabels = false;

      devices.forEach((d) => {
        if (d.kind === "audioinput") {
          inputs.push({
            deviceId: d.deviceId,
            label: d.label || `Microphone ${inputs.length + 1}`,
            kind: d.kind,
          });
          if (d.label) hasLabels = true;
        } else if (d.kind === "audiooutput") {
          outputs.push({
            deviceId: d.deviceId,
            label: d.label || `Speaker ${outputs.length + 1}`,
            kind: d.kind,
          });
        }
      });

      setHasPermission(hasLabels);
      setAudioInputDevices(inputs);
      setAudioOutputDevices(outputs);

      // Check sinkId support for output switching
      const audio = document.createElement("audio");
      setSupportsOutputSelection(typeof (audio as any).setSinkId === "function");
    } catch (e) {
      console.warn("[useAudioDevices] Enumeration failed:", e);
    }
  }, []);

  useEffect(() => {
    enumerateDevices();

    if (navigator?.mediaDevices?.addEventListener) {
      navigator.mediaDevices.addEventListener("devicechange", enumerateDevices);
      return () => {
        navigator.mediaDevices.removeEventListener("devicechange", enumerateDevices);
      };
    }
  }, [enumerateDevices]);

  return {
    audioInputDevices,
    audioOutputDevices,
    supportsOutputSelection,
    hasPermission,
    refreshDevices: enumerateDevices,
  };
}
