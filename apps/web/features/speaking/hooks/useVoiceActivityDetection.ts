"use client";

import { useVAD, UseVADOptions } from "@/features/audio/hooks/useVAD";

export type { UseVADOptions };

export function useVoiceActivityDetection(options: UseVADOptions) {
  return useVAD(options);
}
