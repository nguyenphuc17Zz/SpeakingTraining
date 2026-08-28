"use client";

import { useEffect, useState } from "react";

export function useAudioLevelMeter(volume: number) {
  const [clipping, setClipping] = useState(false);
  const [levelCategory, setLevelCategory] = useState<"silent" | "quiet" | "good" | "loud" | "clipping">("silent");

  useEffect(() => {
    if (volume >= 0.95) {
      setClipping(true);
      setLevelCategory("clipping");
    } else {
      setClipping(false);
      if (volume < 0.02) {
        setLevelCategory("silent");
      } else if (volume < 0.15) {
        setLevelCategory("quiet");
      } else if (volume < 0.70) {
        setLevelCategory("good");
      } else {
        setLevelCategory("loud");
      }
    }
  }, [volume]);

  return {
    volume,
    isClipping: clipping,
    levelCategory,
  };
}
