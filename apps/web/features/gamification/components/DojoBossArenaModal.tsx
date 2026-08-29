"use client";

import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

import React, { useState, useEffect, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Swords,
  Mic,
  MicOff,
  Volume2,
  Trophy,
  Skull,
  Sparkles,
  Zap,
  Clock,
  X,
  RotateCcw,
  CheckCircle2,
  Flame,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface DojoBossArenaModalProps {
  boss: any | null;
  isOpen: boolean;
  onClose: () => void;
  onVictory: (boss: any, xpAwarded: number) => void;
}

export function DojoBossArenaModal({
  boss,
  isOpen,
  onClose,
  onVictory,
}: DojoBossArenaModalProps) {
  const [bossHp, setBossHp] = useState(100);
  const [playerHp, setPlayerHp] = useState(100);
  const [round, setRound] = useState(1);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [currentPromptJa, setCurrentPromptJa] = useState("");
  const [currentPromptVi, setCurrentPromptVi] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [turnHistory, setTurnHistory] = useState<any[]>([]);
  const [battleState, setBattleState] = useState<"ready" | "fighting" | "victory" | "defeat">("ready");
  const [timeLeft, setTimeLeft] = useState(15);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  const recognitionRef = useRef<any>(null);
  const timerRef = useRef<any>(null);
  const startTimeRef = useRef<number>(0);

  // Initialize battle when opened
  useEffect(() => {
    if (isOpen && boss) {
      setBossHp(100);
      setPlayerHp(100);
      setRound(1);
      setTurnHistory([]);
      setBattleState("ready");
      setTranscript("");

      // Parse initial line if available
      let initJa = "本日はお時間をいただきありがとうございます。早速ですが、今回の件についてご説明いただけますか。";
      let initVi = "Cảm ơn bạn đã dành thời gian hôm nay. Bạn có thể giải thích rõ về tình huống lần này không?";
      if (boss.prompt_modifier && boss.prompt_modifier.includes("InitialLineJa:")) {
        const parts = boss.prompt_modifier.split("|");
        initJa = parts[0]?.replace("InitialLineJa:", "").trim() || initJa;
        initVi = parts[1]?.replace("InitialLineVi:", "").trim() || initVi;
      }
      setCurrentPromptJa(initJa);
      setCurrentPromptVi(initVi);
    }
  }, [isOpen, boss]);

  // Turn timer
  useEffect(() => {
    if (isTimerRunning && timeLeft > 0) {
      timerRef.current = setTimeout(() => setTimeLeft((t) => t - 1), 1000);
    } else if (timeLeft === 0 && isTimerRunning) {
      setIsTimerRunning(false);
      // Auto submit or timeout penalty
      handleTimeout();
    }
    return () => clearTimeout(timerRef.current);
  }, [isTimerRunning, timeLeft]);

  if (!isOpen || !boss) return null;

  const startBattle = () => {
    soundFX.playTaiko();
    setBattleState("fighting");
    setTimeLeft(15);
    setIsTimerRunning(true);
    startTimeRef.current = Date.now();
    speakJapaneseText(currentPromptJa);
  };

  const handleTimeout = () => {
    soundFX.playSuikinkutsu();
    setPlayerHp((hp) => Math.max(0, hp - 30));
    setTurnHistory((prev) => [
      ...prev,
      {
        round,
        turn_score: 30,
        damage_dealt: 0,
        feedback_vi: "Hết thời gian phản xạ (Quá 15 giây). Bạn bị trừ 30 HP!",
      },
    ]);
    if (playerHp <= 30) {
      setBattleState("defeat");
    } else {
      nextRound();
    }
  };

  const startSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Trình duyệt không hỗ trợ nhận diện giọng nói Web-Speech.");
      return;
    }

    soundFX.playFurin();
    const recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event: any) => {
      const text = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join("");
      setTranscript(text);
    };

    recognition.onend = () => {
      setIsRecording(false);
      soundFX.playSuikinkutsu();
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleEvaluateSpeech = async () => {
    if (!transcript.trim()) {
      alert("Vui lòng phát âm câu trả lời trước khi tấn công!");
      return;
    }

    try {
      setEvaluating(true);
      setIsTimerRunning(false);
      const latencyMs = Date.now() - startTimeRef.current;

      const res = await fetch(`http://localhost:8000/api/v1/game/bosses/${boss.id}/evaluate-turn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          round_index: round,
          user_speech: transcript,
          latency_ms: latencyMs,
        }),
      });

      if (res.ok) {
        const evalData = await res.json();
        soundFX.playKatana();

        const newBossHp = Math.max(0, bossHp - evalData.damage_dealt);
        setBossHp(newBossHp);

        setTurnHistory((prev) => [...prev, evalData]);

        if (newBossHp === 0 || round >= 3) {
          if (newBossHp <= 20 || evalData.turn_score >= boss.pass_score_threshold) {
            soundFX.playFurin();
            setBattleState("victory");
            onVictory(boss, boss.xp_reward);
          } else {
            setBattleState("defeat");
          }
        } else {
          // Next round setup
          if (evalData.boss_rebuttal_ja) {
            setCurrentPromptJa(evalData.boss_rebuttal_ja);
            setCurrentPromptVi(evalData.boss_rebuttal_vi || "");
            speakJapaneseText(evalData.boss_rebuttal_ja);
          }
          setRound((r) => r + 1);
          setTranscript("");
          setTimeLeft(15);
          setIsTimerRunning(true);
          startTimeRef.current = Date.now();
        }
      }
    } catch (e) {
      console.error("Turn eval error:", e);
    } finally {
      setEvaluating(false);
    }
  };

  const nextRound = () => {
    if (round >= 3) {
      setBattleState("defeat");
    } else {
      setRound((r) => r + 1);
      setTranscript("");
      setTimeLeft(15);
      setIsTimerRunning(true);
      startTimeRef.current = Date.now();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in" role="dialog">
      <div className="bg-card border border-primary/40 rounded-3xl max-w-2xl w-full p-6 md:p-8 space-y-6 shadow-2xl washi-texture relative overflow-hidden">
        {/* Arena Header: Boss Info & Close */}
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2">
            <Badge variant="sakura" size="sm" className="font-bold">
              DOJO ARENA HIỆP {round}/3
            </Badge>
            <Badge variant="outline" size="sm" className="font-mono text-[10px]">
              {boss.difficulty.toUpperCase()}
            </Badge>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-muted text-muted-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Dual HP Bars: Boss HP & Player HP */}
        <div className="grid grid-cols-2 gap-4">
          {/* Boss HP */}
          <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold text-rose-500">
              <span className="flex items-center gap-1">
                <Skull className="h-4 w-4" />
                <span>{boss.name}</span>
              </span>
              <span className="font-mono">{bossHp} HP</span>
            </div>
            <div className="w-full h-3 rounded-full bg-muted/60 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-rose-600 to-rose-400 rounded-full transition-all duration-500"
                style={{ width: `${bossHp}%` }}
              />
            </div>
          </div>

          {/* Player HP */}
          <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <span className="flex items-center gap-1">
                <Zap className="h-4 w-4" />
                <span>Bạn (Challenger)</span>
              </span>
              <span className="font-mono">{playerHp} HP</span>
            </div>
            <div className="w-full h-3 rounded-full bg-muted/60 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-500"
                style={{ width: `${playerHp}%` }}
              />
            </div>
          </div>
        </div>

        {/* Battle Stages */}
        {battleState === "ready" && (
          <div className="p-8 text-center space-y-4 rounded-2xl bg-muted/30 border border-border/80">
            <div className="w-16 h-16 rounded-3xl bg-amber-500/10 border border-amber-500/30 text-amber-500 mx-auto flex items-center justify-center shadow-lg">
              <Swords className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-black text-foreground font-jp">{boss.name}</h3>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">{boss.description}</p>
            </div>

            <div className="flex flex-wrap justify-center gap-1.5 pt-2">
              {boss.objectives?.map((obj: string, i: number) => (
                <span key={i} className="text-[10px] px-2.5 py-1 rounded-lg bg-card border border-border text-muted-foreground">
                  🎯 {obj}
                </span>
              ))}
            </div>

            <Button
              variant="primary"
              size="lg"
              onClick={startBattle}
              className="font-bold text-sm rounded-xl px-8 shadow-lg gap-2"
            >
              <Swords className="h-4 w-4" />
              <span>Tiến Vào Đấu Trường (Khai Trận)</span>
            </Button>
          </div>
        )}

        {battleState === "fighting" && (
          <div className="space-y-4">
            {/* Boss Dialogue Prompt */}
            <div className="p-4 rounded-2xl bg-muted/50 border border-border/80 space-y-2 relative">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-rose-500 font-mono uppercase">
                  LỜI THÁCH ĐẤU CỦA BOSS (HIỆP {round})
                </span>
                <div className="flex items-center gap-1 text-xs font-mono font-bold text-amber-500">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{timeLeft}s</span>
                </div>
              </div>

              <div className="text-sm font-bold text-foreground font-jp leading-relaxed">
                <UniversalFurigana text={currentPromptJa} fontSize="lg" />
              </div>
              {currentPromptVi && (
                <div className="text-xs text-muted-foreground">
                  {currentPromptVi}
                </div>
              )}

              <button
                type="button"
                onClick={() => speakJapaneseText(currentPromptJa)}
                className="absolute top-3 right-12 p-1.5 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground"
                title="Nghe lại câu nói của Boss"
              >
                <Volume2 className="h-4 w-4" />
              </button>
            </div>

            {/* Player Speech Input Area */}
            <div className="p-4 rounded-2xl bg-card border border-border space-y-3 shadow-2xs">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-foreground">Câu trả lời phản công của bạn:</span>
                <span className="text-[10px] text-muted-foreground">Phát âm rõ ràng tiếng Nhật</span>
              </div>

              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Bấm nút Mic bên dưới và nói tiếng Nhật để phản đòn Boss..."
                className="w-full h-20 p-3 rounded-xl bg-muted/30 border border-border/80 text-xs font-jp text-foreground focus:outline-none focus:border-primary resize-none"
              />

              <div className="flex items-center justify-between gap-2">
                <Button
                  variant={isRecording ? "danger" : "outline"}
                  size="sm"
                  onClick={isRecording ? stopSpeechRecognition : startSpeechRecognition}
                  className="text-xs font-bold rounded-xl gap-1.5"
                >
                  {isRecording ? <MicOff className="h-4 w-4 animate-pulse" /> : <Mic className="h-4 w-4 text-primary" />}
                  <span>{isRecording ? "Dừng thu âm" : "Bắt đầu nói (Mic)"}</span>
                </Button>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleEvaluateSpeech}
                  disabled={evaluating || !transcript.trim()}
                  className="text-xs font-bold rounded-xl gap-1.5 shadow-md"
                >
                  <Flame className="h-4 w-4" />
                  <span>{evaluating ? "Đang tấn công..." : "Tung Đòn Phản Công ⚔️"}</span>
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Victory Screen */}
        {battleState === "victory" && (
          <div className="p-8 text-center space-y-4 rounded-3xl bg-emerald-500/10 border border-emerald-500/30">
            <div className="w-16 h-16 rounded-3xl bg-emerald-500 text-white mx-auto flex items-center justify-center shadow-lg animate-bounce">
              <Trophy className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xl font-black text-foreground">CHIẾN THẮNG TUYỆT ĐỐI! (VICTORY)</h3>
              <p className="text-xs text-muted-foreground">Bạn đã khuất phục thành công {boss.name}</p>
            </div>

            <div className="p-4 rounded-2xl bg-card border border-border/80 max-w-sm mx-auto space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">EXP Nhận được:</span>
                <span className="font-bold text-primary font-mono">+{boss.xp_reward} XP</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Danh hiệu mở khóa:</span>
                <span className="font-bold text-amber-500">{boss.title_reward || "Võ Sĩ Đạo Trường"}</span>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={onClose}
              className="font-bold text-xs rounded-xl px-6"
            >
              Hoàn Tất Thử Thách
            </Button>
          </div>
        )}

        {/* Defeat Screen */}
        {battleState === "defeat" && (
          <div className="p-8 text-center space-y-4 rounded-3xl bg-rose-500/10 border border-rose-500/30">
            <div className="w-16 h-16 rounded-3xl bg-rose-500 text-white mx-auto flex items-center justify-center shadow-lg">
              <Skull className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xl font-black text-foreground">THỬ THÁCH CHƯA THÀNH CÔNG</h3>
              <p className="text-xs text-muted-foreground">Áp lực đàm phán quá lớn! Hãy rèn luyện thêm tại các phòng Studio và thử lại.</p>
            </div>

            <Button
              variant="outline"
              size="md"
              onClick={() => {
                setBattleState("ready");
              }}
              className="font-bold text-xs rounded-xl px-6 gap-1.5"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Thử Lại Trận Đấu</span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
