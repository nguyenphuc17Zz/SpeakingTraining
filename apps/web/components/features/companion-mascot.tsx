"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, MessageCircle, X, Volume2, Heart, RefreshCw, ChevronRight } from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

type MascotType = "kitsune" | "shiba";

interface MascotDialogue {
  japanese: string;
  vietnamese: string;
  mood: "happy" | "encourage" | "proud" | "sleepy";
}

const KITSUNE_DIALOGUES: MascotDialogue[] = [
  {
    japanese: "今日も一緒に楽しく話しましょう！",
    vietnamese: "Hôm nay cùng nhau nói tiếng Nhật thật vui nhé!",
    mood: "happy",
  },
  {
    japanese: "発音の練習、応援していますよ。",
    vietnamese: "Mình luôn ở đây cổ vũ bạn luyện phát âm chuẩn Tokyo!",
    mood: "encourage",
  },
  {
    japanese: "毎日の積み重ねが、大きな自信になります。",
    vietnamese: "Mỗi ngày tích lũy một chút sẽ tạo nên sự tự tin to lớn.",
    mood: "proud",
  },
  {
    japanese: "シャドーイングでイントネーションを磨きましょう！",
    vietnamese: "Cùng Shadowing để mài giũa ngữ điệu mượt mà như người bản xứ nhé!",
    mood: "happy",
  },
];

const SHIBA_DIALOGUES: MascotDialogue[] = [
  {
    japanese: "ワン！連続記録をキープしよう！",
    vietnamese: "Gâu! Cùng giữ chuỗi ngày chăm chỉ hừng hực lửa nào!",
    mood: "happy",
  },
  {
    japanese: "諦めない君が一番かっこいい！",
    vietnamese: "Không từ bỏ chính là lúc bạn ngầu nhất đó!",
    mood: "encourage",
  },
  {
    japanese: "今日のクエストはもうクリアした？",
    vietnamese: "Nhiệm vụ hôm nay bạn đã hoàn thành chưa nào?",
    mood: "happy",
  },
  {
    japanese: "話せば話すほど上手になるよ！",
    vietnamese: "Càng nói nhiều thì tiếng Nhật càng siêu đỉnh!",
    mood: "proud",
  },
];

export function CompanionMascot({
  streakDays = 1,
  className,
}: {
  streakDays?: number;
  className?: string;
}) {
  const [mascot, setMascot] = useState<MascotType>("kitsune");
  const [dialogueIndex, setDialogueIndex] = useState(0);
  const [isBubbleOpen, setIsBubbleOpen] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isCheering, setIsCheering] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedMascot = localStorage.getItem("hanasu-mascot") as MascotType | null;
    if (savedMascot) setMascot(savedMascot);
  }, []);

  const dialogues = mascot === "kitsune" ? KITSUNE_DIALOGUES : SHIBA_DIALOGUES;
  const currentDialogue = dialogues[dialogueIndex % dialogues.length];

  const handleNextDialogue = () => {
    soundFX.playSuikinkutsu();
    setIsCheering(true);
    setDialogueIndex((prev) => (prev + 1) % dialogues.length);
    setTimeout(() => setIsCheering(false), 500);
  };

  const handleSwitchMascot = (type: MascotType) => {
    soundFX.playFurin();
    setMascot(type);
    setDialogueIndex(0);
    if (typeof window !== "undefined") {
      localStorage.setItem("hanasu-mascot", type);
    }
  };

  const handleSpeakDialogue = () => {
    if (typeof window === "undefined") return;
    soundFX.playSuikinkutsu();
    const utterance = new SpeechSynthesisUtterance(currentDialogue.japanese);
    utterance.lang = "ja-JP";
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  };

  if (isMinimized) {
    return (
      <button
        onClick={() => {
          soundFX.playFurin();
          setIsMinimized(false);
          setIsBubbleOpen(true);
        }}
        className="fixed bottom-5 right-5 z-40 h-12 w-12 rounded-full border-2 border-primary/40 bg-card/95 backdrop-blur-md shadow-sumi-lg flex items-center justify-center text-xl hover:scale-110 transition-all duration-200"
        title="Mở linh thú đồng hành"
      >
        {mascot === "kitsune" ? "🦊" : "🐕"}
        <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-primary border-2 border-card animate-pulse" />
      </button>
    );
  }

  return (
    <div className={cn("fixed bottom-5 right-5 z-40 flex flex-col items-end gap-2 pointer-events-none select-none", className)}>
      {/* Speech Bubble */}
      {isBubbleOpen && (
        <div className="pointer-events-auto max-w-[260px] sm:max-w-[290px] rounded-2xl border border-border bg-card/95 washi-texture backdrop-blur-xl shadow-sumi-lg p-3.5 space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-foreground flex items-center gap-1">
                {mascot === "kitsune" ? "Cáo Thần Inari" : "Shiba Dũng Cảm"}
                <span className="text-[10px] font-jp text-primary font-bold">
                  {mascot === "kitsune" ? "稲荷" : "柴犬"}
                </span>
              </span>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleSpeakDialogue}
                className="h-6 w-6 rounded-md bg-muted hover:bg-muted/80 flex items-center justify-center text-muted-foreground hover:text-foreground"
                title="Nghe phát âm"
              >
                <Volume2 className="h-3 w-3" />
              </button>
              <button
                onClick={() => setIsBubbleOpen(false)}
                className="h-6 w-6 rounded-md bg-muted hover:bg-muted/80 flex items-center justify-center text-muted-foreground hover:text-foreground"
                title="Ẩn lời thoại"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          </div>

          <div className="space-y-1 cursor-pointer" onClick={handleNextDialogue}>
            <p className="text-xs font-jp font-bold text-foreground leading-snug">
              {currentDialogue.japanese}
            </p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              {currentDialogue.vietnamese}
            </p>
          </div>

          {/* Quick Actions in Bubble */}
          <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[10px] text-muted-foreground">
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleSwitchMascot(mascot === "kitsune" ? "shiba" : "kitsune")}
                className="hover:text-primary font-semibold flex items-center gap-0.5"
              >
                <RefreshCw className="h-2.5 w-2.5" />
                Đổi {mascot === "kitsune" ? "Shiba 🐕" : "Kitsune 🦊"}
              </button>
            </div>
            <button
              onClick={handleNextDialogue}
              className="text-primary hover:opacity-80 font-bold flex items-center gap-0.5"
            >
              Tiếp theo <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}

      {/* Mascot Avatar Figure */}
      <div className="pointer-events-auto flex items-center gap-1">
        <button
          onClick={() => {
            if (!isBubbleOpen) setIsBubbleOpen(true);
            else handleNextDialogue();
          }}
          className={cn(
            "h-14 w-14 rounded-2xl border-2 border-primary/40 bg-gradient-to-br from-card to-muted/80 shadow-sumi-lg flex items-center justify-center text-2xl hover:scale-105 active:scale-95 transition-all duration-200 relative group",
            isCheering && "animate-bounce"
          )}
          title="Bấm để tương tác với linh thú"
        >
          <span>{mascot === "kitsune" ? "🦊" : "🐕"}</span>
          <span className="absolute -bottom-1 -right-1 text-[10px] px-1 rounded-full bg-amber-500 text-white font-black shadow-sm">
            Lv.{Math.min(streakDays, 99)}
          </span>
        </button>

        <button
          onClick={() => setIsMinimized(true)}
          className="h-6 w-6 rounded-full bg-muted/80 hover:bg-muted border border-border flex items-center justify-center text-muted-foreground hover:text-foreground text-[10px]"
          title="Thu nhỏ linh thú"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
