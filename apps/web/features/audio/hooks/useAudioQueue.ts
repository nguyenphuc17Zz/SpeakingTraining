"use client";

import { useCallback, useState } from "react";
import { AudioQueueItem } from "@/types/audio";
import { useAudioPlayer } from "./useAudioPlayer";

export function useAudioQueue() {
  const [queue, setQueue] = useState<AudioQueueItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [isPlayingQueue, setIsPlayingQueue] = useState(false);

  const player = useAudioPlayer({
    onPlaybackEnded: () => {
      // Auto-advance to next queue item
      setQueue((prevQueue) => {
        if (currentIndex + 1 < prevQueue.length) {
          const nextIdx = currentIndex + 1;
          setCurrentIndex(nextIdx);
          const nextItem = prevQueue[nextIdx];
          if (nextItem) {
            setTimeout(() => {
              if (nextItem.type === "tts" || nextItem.source.startsWith("data:") || !nextItem.source.startsWith("http")) {
                player.playBase64(nextItem.source);
              } else {
                player.playUrl(nextItem.source);
              }
            }, nextItem.repeat_count ? 500 : 200);
          }
        } else {
          setIsPlayingQueue(false);
          setCurrentIndex(-1);
        }
        return prevQueue;
      });
    },
  });

  const enqueue = useCallback((item: AudioQueueItem) => {
    setQueue((prev) => [...prev, item]);
  }, []);

  const clearQueue = useCallback(() => {
    player.stop();
    setQueue([]);
    setCurrentIndex(-1);
    setIsPlayingQueue(false);
  }, [player]);

  const startQueue = useCallback(
    (items?: AudioQueueItem[]) => {
      const targetQueue = items || queue;
      if (targetQueue.length === 0) return;

      if (items) {
        setQueue(items);
      }

      setCurrentIndex(0);
      setIsPlayingQueue(true);

      const firstItem = targetQueue[0];
      if (firstItem.type === "tts" || firstItem.source.startsWith("data:") || !firstItem.source.startsWith("http")) {
        player.playBase64(firstItem.source);
      } else {
        player.playUrl(firstItem.source);
      }
    },
    [player, queue]
  );

  const skipNext = useCallback(() => {
    if (currentIndex + 1 < queue.length) {
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      const nextItem = queue[nextIdx];
      if (nextItem.type === "tts" || nextItem.source.startsWith("data:") || !nextItem.source.startsWith("http")) {
        player.playBase64(nextItem.source);
      } else {
        player.playUrl(nextItem.source);
      }
    } else {
      clearQueue();
    }
  }, [clearQueue, currentIndex, player, queue]);

  return {
    queue,
    currentIndex,
    currentItem: currentIndex >= 0 ? queue[currentIndex] : null,
    isPlayingQueue,
    enqueue,
    startQueue,
    clearQueue,
    skipNext,
    pause: player.pause,
    resume: player.resume,
    playerState: player.state,
  };
}
