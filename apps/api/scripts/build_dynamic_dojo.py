import os

# 1. dynamic_boss_generator.py
DYNAMIC_BOSS_GEN = '''import json
import random
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.gamification.models import BossDefinition


SAMPLE_BOSS_PROMPTS = [
    {"topic": "Thương Lượng Tăng Lương Với Trưởng Phòng Nhật", "difficulty": "hard", "level": 5},
    {"topic": "Báo Cáo Sự Cố Rò Rỉ Dữ Liệu Khẩn Cấp Nửa Đêm Cho Giám Đốc", "difficulty": "extreme", "level": 10},
    {"topic": "Thuyết Trình Đề Xuất Dự Án Mới Trước Hội Đồng Cổ Đông", "difficulty": "hard", "level": 7},
    {"topic": "Giải Trình Với Hải Quan Sân Bay Narita Về Hành Lý Bị Giữ", "difficulty": "normal", "level": 3},
    {"topic": "Xin Gia Hạn Deadline Hợp Đồng Với Đối Tác Khó Tính", "difficulty": "hard", "level": 6},
    {"topic": "Xoa Dịu Khách Hàng VIP Đòi Hủy Đơn Hàng Do Giao Chậm", "difficulty": "extreme", "level": 12},
    {"topic": "Phỏng Vấn Vòng Cuối Giám Đốc Nhân Sự Tập Đoàn Đa Quốc Gia", "difficulty": "extreme", "level": 15},
    {"topic": "Thuyết Phục Đồng Nghiệp Tiền Bối Hỗ Trợ Đề Án Bị Phản Đối", "difficulty": "normal", "level": 4},
]


class DynamicBossGenerator:
    """Generates infinite high-stakes Japanese speaking boss battle trials using Gemini AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def generate_boss(
        self,
        topic: str | None = None,
        difficulty: str = "normal",
        required_level: int = 3,
        user_id: str | None = None,
    ) -> BossDefinition:
        """Dynamically designs and persists a new high-stakes Boss challenge."""
        if not topic or topic.strip() == "" or topic == "random":
            chosen = random.choice(SAMPLE_BOSS_PROMPTS)
            topic = chosen["topic"]
            difficulty = chosen["difficulty"]
            required_level = chosen["level"]

        prompt = f"""Bạn là Đạo diễn Thiết Kế Đấu Trường Luyện Nói Tiếng Nhật (Dojo Boss Arena Director).
Hãy thiết kế một Thử Thách Boss Đối Kháng Áp Lực Cao (High-Stakes Speaking Boss Trial) theo chủ đề:
Chủ đề: {topic}
Độ khó: {difficulty} (normal, hard, extreme)
Cấp độ yêu cầu: Level {required_level}

Yêu cầu xuất ra định dạng JSON thuần túy (không markdown, không ```json):
{{
  "name": "Tên Boss và chức danh bằng tiếng Nhật kèm Hán tự (ví dụ: 鬼の取締役・田中 (Trưởng ban Tanaka nghiêm khắc))",
  "subtitle": "Phụ đề tóm tắt bối cảnh bằng tiếng Việt (ngắn gọn, kịch tính)",
  "description": "Mô tả chi tiết tình huống đối thoại áp lực và thái độ của Boss",
  "persona_key": "system_default_persona",
  "difficulty": "{difficulty}",
  "required_level": {required_level},
  "pass_score_threshold": {75.0 if difficulty == "normal" else 82.0 if difficulty == "hard" else 88.0},
  "xp_reward": {500 if difficulty == "normal" else 900 if difficulty == "hard" else 1500},
  "title_reward": "Danh hiệu độc quyền khi chiến thắng kèm tiếng Nhật (ví dụ: 交渉の達人 (Bậc Thầy Đàm Phán))",
  "objectives": [
    "Mục tiêu 1 bằng tiếng Việt (ví dụ: Sử dụng chuẩn xác Kính ngữ Sonkeigo/Kenjougo)",
    "Mục tiêu 2 bằng tiếng Việt (ví dụ: Trình bày lý do mạch lạc dưới 15 giây)",
    "Mục tiêu 3 bằng tiếng Việt (ví dụ: Đưa ra giải pháp thuyết phục không lúng túng)"
  ],
  "scenario_template": "Bối cảnh mở đầu chi tiết",
  "initial_boss_line_ja": "Câu mở đầu đầy áp lực của Boss bằng tiếng Nhật (kèm kanji)",
  "initial_boss_line_vi": "Dịch nghĩa câu mở đầu của Boss sang tiếng Việt"
}}"""

        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction="Bạn là AI Game Master thiết kế màn chơi Boss Đấu Trường tiếng Nhật. Luôn trả về đúng chuẩn JSON.",
            temperature=0.7,
        )

        boss_data = None
        try:
            resp = await self.ai_router.generate(task=AITask.ROLEPLAY_GENERATE, request=req, user_id=user_id)
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            boss_data = json.loads(raw.strip())
        except Exception as e:
            logger.warning(f"[DynamicBossGenerator] Gemini generation fallback: {e}")
            boss_data = {
                "name": f"試練の相手・{topic[:15]}",
                "subtitle": f"Thử thách đối thoại: {topic}",
                "description": f"Vượt qua buổi đối thoại căng thẳng về chủ đề '{topic}' với người Nhật có chuyên môn cao.",
                "persona_key": "system_default_persona",
                "difficulty": difficulty,
                "required_level": required_level,
                "pass_score_threshold": 75.0 if difficulty == "normal" else 85.0,
                "xp_reward": 600 if difficulty == "normal" else 1000,
                "title_reward": f"Chinh Phục {topic[:10]}",
                "objectives": [
                    "Sử dụng Kính ngữ phù hợp hoàn cảnh",
                    "Phản xạ câu nói tự tin dưới 3 giây",
                    "Giữ nhịp điệu phát âm chuẩn Tokyo",
                ],
                "scenario_template": f"Bạn đang tham gia buổi đàm phán quan trọng về: {topic}.",
                "initial_boss_line_ja": "本日はお時間をいただき感謝いたします。早速ですが、今回の件についてご説明いただけますか。",
                "initial_boss_line_vi": "Cảm ơn bạn đã dành thời gian hôm nay. Không để mất thời gian, bạn có thể giải thích rõ về sự việc lần này không?",
            }

        unique_key = f"boss_{uuid.uuid4().hex[:8]}"
        boss = BossDefinition(
            key=unique_key,
            name=boss_data.get("name", f"Boss: {topic}"),
            subtitle=boss_data.get("subtitle", "Thử thách đối kháng cao độ"),
            description=boss_data.get("description", "Thử thách đối thoại áp lực"),
            persona_key="system_default_persona",
            difficulty=boss_data.get("difficulty", difficulty),
            required_level=int(boss_data.get("required_level", required_level)),
            pass_score_threshold=float(boss_data.get("pass_score_threshold", 75.0)),
            xp_reward=int(boss_data.get("xp_reward", 600)),
            title_reward=boss_data.get("title_reward", "Võ Sĩ Đạo Trường"),
            objectives_json=boss_data.get("objectives", []),
            scenario_template=boss_data.get("scenario_template", topic),
            prompt_modifier=f"InitialLineJa: {boss_data.get('initial_boss_line_ja', '')} | InitialLineVi: {boss_data.get('initial_boss_line_vi', '')}",
        )
        self.db.add(boss)
        await self.db.commit()
        await self.db.refresh(boss)

        logger.info(f"[DynamicBossGenerator] Successfully generated Boss '{boss.name}' ({boss.key})")
        return boss
'''

# 2. Add evaluate_arena_turn to boss_service.py
BOSS_SERVICE_UPDATE = '''    async def evaluate_arena_turn(
        self,
        user_id: str,
        boss_id: str,
        round_index: int,
        user_speech: str,
        latency_ms: float = 2000.0,
    ) -> dict[str, Any]:
        """Evaluates a live turn in the Dojo Boss Arena, deals damage to Boss HP, and gets AI response."""
        boss_stmt = select(BossDefinition).where(BossDefinition.id == boss_id)
        boss_res = await self.db.execute(boss_stmt)
        boss = boss_res.scalar_one_or_none()
        if not boss:
            raise NotFoundException(f"Boss '{boss_id}' not found.")

        # AI prompt to evaluate learner speech and produce NPC rebuttal
        prompt = f"""Bạn là Giám khảo Trận Đấu Dojo kiêm Boss đối thoại tiếng Nhật '{boss.name}'.
Bối cảnh: {boss.description}
Mục tiêu thử thách: {', '.join(boss.objectives_json or [])}
Độ khó: {boss.difficulty}

Lượt đấu hiện tại: Hiệp {round_index}/3
Câu nói của học viên: "{user_speech}"
Tốc độ phản xạ: {int(latency_ms)}ms

Yêu cầu xuất ra đúng định dạng JSON (không markdown, không ```json):
{{
  "turn_score": (Điểm hiệp này từ 0 đến 100 dựa trên Kính ngữ, sự thuyết phục, từ vựng và tốc độ),
  "keigo_accuracy": (Điểm Kính ngữ 0-100),
  "fluency_score": (Điểm Trôi chảy 0-100),
  "feedback_vi": "Nhận xét nhanh 1 câu bằng tiếng Việt về câu trả lời vừa rồi",
  "boss_rebuttal_ja": "Câu đáp trả hoặc câu hỏi tiếp theo của Boss bằng tiếng Nhật (kèm kanji)",
  "boss_rebuttal_vi": "Bản dịch tiếng Việt của câu đáp trả"
}}"""

        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction="Bạn là Boss Game Master chấm điểm và đối đáp áp lực. Luôn trả về đúng định dạng JSON.",
            temperature=0.6,
        )

        try:
            resp = await self.ai_router.generate(task=AITask.ROLEPLAY_GENERATE, request=req, user_id=user_id)
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            res_data = json.loads(raw.strip())
        except Exception as e:
            logger.warning(f"[BossService] Arena turn AI fallback: {e}")
            score = max(50.0, min(95.0, round(90.0 - (latency_ms / 3000.0 * 20.0), 1)))
            res_data = {
                "turn_score": score,
                "keigo_accuracy": 80.0,
                "fluency_score": score,
                "feedback_vi": "Phản xạ câu tốt, hãy chú ý chọn từ trang trọng hơn.",
                "boss_rebuttal_ja": "なるほど、おっしゃることは分かりました。では次の点についてはいかがでしょうか。",
                "boss_rebuttal_vi": "Tôi hiểu ý bạn rồi. Vậy về điểm tiếp theo bạn nghĩ sao?",
            }

        turn_score = float(res_data.get("turn_score", 75.0))
        damage = max(15, min(45, int(turn_score * 0.40)))

        return {
            "round_index": round_index,
            "turn_score": turn_score,
            "damage_dealt": damage,
            "keigo_accuracy": res_data.get("keigo_accuracy", 80.0),
            "fluency_score": res_data.get("fluency_score", 75.0),
            "feedback_vi": res_data.get("feedback_vi", "Phản xạ tốt!"),
            "boss_rebuttal_ja": res_data.get("boss_rebuttal_ja", ""),
            "boss_rebuttal_vi": res_data.get("boss_rebuttal_vi", ""),
        }
'''

# 3. DynamicBossGeneratorModal.tsx
DYNAMIC_BOSS_MODAL = """\"use client\";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Dices,
  Swords,
  X,
  Zap,
  Target,
  Flame,
  Crown,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface DynamicBossGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBossCreated: (boss: any) => void;
}

const PRESET_TOPICS = [
  "Thương Lượng Tăng Lương Với Trưởng Phòng Nhật",
  "Báo Cáo Sự Cố Khẩn Cấp Nửa Đêm Cho Giám Đốc",
  "Thuyết Trình Đề Xuất Dự Án Trước Hội Đồng Cổ Đông",
  "Giải Trình Với Hải Quan Sân Bay Narita",
  "Xin Gia Hạn Hợp Đồng Với Đối Tác Khó Tính",
  "Xoa Dịu Khách Hàng VIP Đòi Hủy Đơn Hàng",
];

export function DynamicBossGeneratorModal({
  isOpen,
  onClose,
  onBossCreated,
}: DynamicBossGeneratorModalProps) {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState<"normal" | "hard" | "extreme">("normal");
  const [requiredLevel, setRequiredLevel] = useState<number>(3);
  const [isGenerating, setIsGenerating] = useState(false);

  if (!isOpen) return null;

  const handleGenerate = async (targetTopic?: string) => {
    const finalTopic = targetTopic || topic;
    try {
      setIsGenerating(true);
      soundFX.playKatana();
      const res = await fetch("http://localhost:8000/api/v1/game/bosses/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: finalTopic || "random",
          difficulty,
          required_level: requiredLevel,
        }),
      });
      if (res.ok) {
        const createdBoss = await res.json();
        soundFX.playTaiko();
        onBossCreated(createdBoss);
        onClose();
      } else {
        alert("Không thể tạo Boss thử thách. Vui lòng thử lại!");
      }
    } catch (e) {
      console.error("Boss generation error:", e);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in" role="dialog">
      <div className="bg-card border border-primary/30 rounded-3xl max-w-lg w-full p-6 md:p-8 space-y-6 shadow-2xl washi-texture relative overflow-hidden ring-1 ring-primary/20">
        <div className="absolute top-0 right-0 h-40 w-40 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-3.5 relative z-10">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/20 shadow-2xs">
              <Swords className="h-5 w-5" />
            </span>
            <div>
              <h3 className="text-base font-black text-foreground flex items-center gap-2">
                <span>Tạo Thử Thách Boss AI Vô Tận</span>
                <span className="text-xs font-jp text-muted-foreground font-normal">(強敵生成)</span>
              </h3>
              <p className="text-[11px] text-muted-foreground">Tạo màn đối đầu áp lực cao bằng Gemini AI</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-muted text-muted-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="space-y-4 relative z-10">
          {/* Topic Input */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-foreground">Chủ đề hoặc tình huống đối đầu mong muốn:</label>
            <input
              type="text"
              placeholder="VD: Thương lượng giảm giá hợp đồng, Đàm phán bồi thường..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-muted/40 border border-border text-xs text-foreground focus:outline-none focus:border-primary"
            />
          </div>

          {/* Quick Presets */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-muted-foreground">Gợi ý tình huống kịch tính:</span>
            <div className="flex flex-wrap gap-1.5">
              {PRESET_TOPICS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setTopic(preset)}
                  className={cn(
                    "px-2.5 py-1 rounded-lg text-[10px] font-semibold border transition-all text-left",
                    topic === preset
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-muted/40 text-muted-foreground border-border/80 hover:text-foreground"
                  )}
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty & Level */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-foreground">Độ khó Boss:</label>
              <div className="flex rounded-xl border border-border overflow-hidden p-0.5 bg-muted/30">
                {(["normal", "hard", "extreme"] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDifficulty(d)}
                    className={cn(
                      "flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-all capitalize",
                      difficulty === d
                        ? "bg-primary text-primary-foreground shadow-2xs"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {d === "normal" ? "Thường" : d === "hard" ? "Khó" : "Cực Hạn"}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-foreground">Cấp RPG yêu cầu:</label>
              <select
                value={requiredLevel}
                onChange={(e) => setRequiredLevel(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border text-xs text-foreground focus:outline-none focus:border-primary"
              >
                <option value={1}>Level 1+ (Sơ cấp)</option>
                <option value={3}>Level 3+ (Trung cấp)</option>
                <option value={8}>Level 8+ (Cao cấp)</option>
                <option value={15}>Level 15+ (Bậc thầy)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-2.5 pt-2 border-t border-border/80 relative z-10">
          <Button
            variant="outline"
            size="md"
            onClick={() => handleGenerate("random")}
            disabled={isGenerating}
            className="w-full sm:w-auto text-xs font-bold gap-1.5 rounded-xl border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
          >
            <Dices className="h-4 w-4" />
            <span>🎲 Tạo Ngẫu Nhiên</span>
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => handleGenerate()}
            disabled={isGenerating}
            className="w-full sm:flex-1 text-xs font-bold gap-1.5 rounded-xl shadow-md"
          >
            <Sparkles className="h-4 w-4" />
            <span>{isGenerating ? "Gemini đang thiết kế Boss..." : "Tạo Boss Mới Ngay"}</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
"""

# 4. DojoBossArenaModal.tsx (Live 3-Round Interactive Battle)
ARENA_MODAL = """\"use client\";

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
    soundFX.playWoodBlock();
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

    soundFX.playMicOn();
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
      soundFX.playMicOff();
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
                "{currentPromptJa}"
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
                  variant={isRecording ? "destructive" : "outline"}
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
"""

# 5. Update bosses/page.tsx
BOSSES_PAGE = """\"use client\";

import React, { useState } from "react";
import { useBosses, BossCard } from "@/features/gamification";
import { DynamicBossGeneratorModal } from "@/features/gamification/components/DynamicBossGeneratorModal";
import { DojoBossArenaModal } from "@/features/gamification/components/DojoBossArenaModal";
import { Swords, Trophy, ShieldAlert, Sparkles, Flame, CheckCircle2, Zap, Dices, Plus } from "lucide-react";
import { BossDTO } from "@/features/gamification";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function BossesPage() {
  const { bosses, loading, error, fetchBosses } = useBosses();
  const [selectedDifficulty, setSelectedDifficulty] = useState<"all" | "normal" | "hard" | "extreme">("all");
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false);
  const [activeArenaBoss, setActiveArenaBoss] = useState<BossDTO | null>(null);

  const clearedCount = bosses.filter((b) => b.cleared).length;

  const filteredBosses = bosses.filter((b) => {
    if (selectedDifficulty === "all") return true;
    return b.difficulty === selectedDifficulty;
  });

  const handleStartArena = (boss: BossDTO) => {
    soundFX.playKatana();
    setActiveArenaBoss(boss);
  };

  const handleVictory = (boss: any, xp: number) => {
    console.log("Boss Victory:", boss.name, "+XP:", xp);
    if (fetchBosses) fetchBosses();
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Header Hero Banner */}
      <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden ring-1 ring-primary/20">
        <div className="absolute top-0 right-0 h-56 w-56 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="kintsugi" size="sm" className="font-bold">
                DOJO BOSS ARENA ⚔️
              </Badge>
              <Badge variant="matcha" size="sm" className="font-bold">
                100% DYNAMIC AI
              </Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-2">
              <span>Đấu Trường Boss & Thử Thách Cực Hạn</span>
              <span className="text-base font-jp font-normal text-muted-foreground">(強敵試練)</span>
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-xl leading-relaxed">
              Các kịch bản đối thoại đối kháng áp lực cao do Gemini AI sinh mới: Phỏng vấn công sở, giải trình khủng hoảng và tranh biện kịch tính.
            </p>
          </div>

          {/* Action Buttons: Generator & Stats */}
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                soundFX.playKatana();
                setIsGeneratorOpen(true);
              }}
              className="text-xs font-bold gap-1.5 rounded-xl shadow-md"
            >
              <Plus className="h-4 w-4" />
              <span>Tạo Boss AI Mới</span>
            </Button>
          </div>
        </div>

        {/* Clear Stats Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 border-t border-border/60 relative z-10">
          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">ĐÃ KHUẤT PHỤC</span>
            <div className="text-lg font-black text-foreground font-mono">
              {clearedCount} / {bosses.length} <span className="text-xs font-normal text-muted-foreground">Boss</span>
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">QUY TẮC ĐẤU TRƯỜNG</span>
            <div className="text-xs font-bold text-foreground">
              3 Hiệp Rút Máu Boss HP
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs col-span-2 sm:col-span-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">PHẦN THƯỞNG</span>
            <div className="text-xs font-bold text-amber-500 font-mono">
              +500 ~ 1500 EXP & Danh Hiệu
            </div>
          </div>
        </div>
      </div>

      {/* 2. Difficulty Filter Tabs */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          {(["all", "normal", "hard", "extreme"] as const).map((diff) => (
            <button
              key={diff}
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSelectedDifficulty(diff);
              }}
              className={cn(
                "px-3.5 py-1.5 rounded-xl text-xs font-bold border transition-all capitalize",
                selectedDifficulty === diff
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-card border-border text-muted-foreground hover:text-foreground"
              )}
            >
              {diff === "all" ? "Tất cả" : diff === "normal" ? "Thường (Normal)" : diff === "hard" ? "Khó (Hard)" : "Cực Hạn (Extreme)"}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Boss Grid */}
      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground animate-pulse">
          Đang chuẩn bị đấu trường Boss từ hệ thống...
        </div>
      ) : filteredBosses.length === 0 ? (
        <div className="p-16 text-center text-xs text-muted-foreground border rounded-3xl">
          Chưa có Boss nào thuộc phân loại này. Hãy bấm "Tạo Boss AI Mới"!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredBosses.map((boss) => (
            <div
              key={boss.id}
              className="p-6 rounded-3xl border border-border/80 bg-card washi-texture shadow-xs hover:border-primary/40 hover:shadow-md transition-all flex flex-col justify-between space-y-4 relative overflow-hidden group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge
                    variant={boss.difficulty === "extreme" ? "sakura" : boss.difficulty === "hard" ? "kintsugi" : "matcha"}
                    size="sm"
                    className="font-bold text-[10px] uppercase"
                  >
                    {boss.difficulty}
                  </Badge>
                  <span className="text-[10px] font-mono text-muted-foreground">Req Lv. {boss.required_level}</span>
                </div>

                <div className="space-y-1">
                  <h3 className="text-base font-black text-foreground font-jp group-hover:text-primary transition-colors">
                    {boss.name}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                    {boss.subtitle || boss.description}
                  </p>
                </div>

                {/* Objectives */}
                <div className="space-y-1 pt-1">
                  {boss.objectives?.slice(0, 2).map((obj: string, idx: number) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <span className="text-primary">•</span>
                      <span className="line-clamp-1">{obj}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3 border-t border-border/60">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartArena(boss)}
                  className="w-full text-xs font-bold rounded-xl justify-between hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all shadow-2xs"
                >
                  <span>Vào Đấu Trường Arena</span>
                  <Swords className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dynamic Boss Generator Modal */}
      <DynamicBossGeneratorModal
        isOpen={isGeneratorOpen}
        onClose={() => setIsGeneratorOpen(false)}
        onBossCreated={(newBoss) => {
          if (fetchBosses) fetchBosses();
          setActiveArenaBoss(newBoss);
        }}
      />

      {/* Dojo Boss Arena Interactive Modal */}
      <DojoBossArenaModal
        boss={activeArenaBoss}
        isOpen={!!activeArenaBoss}
        onClose={() => setActiveArenaBoss(null)}
        onVictory={handleVictory}
      />
    </div>
  );
}
"""

FILES_DOJO = {
    r"E:\SpeakingTraining\apps\api\app\domains\gamification\application\dynamic_boss_generator.py": DYNAMIC_BOSS_GEN,
    r"E:\SpeakingTraining\apps\web\features\gamification\components\DynamicBossGeneratorModal.tsx": DYNAMIC_BOSS_MODAL,
    r"E:\SpeakingTraining\apps\web\features\gamification\components\DojoBossArenaModal.tsx": ARENA_MODAL,
    r"E:\SpeakingTraining\apps\web\app\bosses\page.tsx": BOSSES_PAGE,
}

for filepath, content in FILES_DOJO.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

# Append evaluate_arena_turn to boss_service.py if not present
boss_service_path = r"E:\SpeakingTraining\apps\api\app\domains\gamification\application\boss_service.py"
with open(boss_service_path, "r", encoding="utf-8") as f:
    text = f.read()

if "evaluate_arena_turn" not in text:
    # Need to also ensure AIRouter is imported/available in boss_service
    if "from app.domains.ai.router import AIRouter" not in text:
        text = "from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask\\nfrom app.domains.ai.router import AIRouter\\nimport json\\n" + text
    
    # Initialize ai_router in __init__
    text = text.replace("def __init__(self, db: AsyncSession):\\n        self.db = db", "def __init__(self, db: AsyncSession):\\n        self.db = db\\n        self.ai_router = AIRouter(db)")
    
    text = text + "\\n" + BOSS_SERVICE_UPDATE
    with open(boss_service_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully added evaluate_arena_turn to boss_service.py")

# Add endpoints to game.py if not present
game_api_path = r"E:\SpeakingTraining\apps\api\app\api\v1\game.py"
with open(game_api_path, "r", encoding="utf-8") as f:
    game_text = f.read()

GAME_ENDPOINTS = '''
from pydantic import BaseModel

class GenerateBossRequest(BaseModel):
    topic: str | None = None
    difficulty: str = "normal"
    required_level: int = 3

class EvaluateTurnRequest(BaseModel):
    round_index: int = 1
    user_speech: str
    latency_ms: float = 2000.0

@router.post("/bosses/generate", response_model=BossDTO)
async def generate_dynamic_boss(
    payload: GenerateBossRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generates a dynamic high-stakes speaking boss challenge using Gemini AI."""
    from app.domains.gamification.application.dynamic_boss_generator import DynamicBossGenerator
    generator = DynamicBossGenerator(db)
    boss = await generator.generate_boss(
        topic=payload.topic,
        difficulty=payload.difficulty,
        required_level=payload.required_level,
        user_id=user_id,
    )
    return BossDTO(
        id=boss.id,
        key=boss.key,
        name=boss.name,
        subtitle=boss.subtitle,
        description=boss.description,
        difficulty=boss.difficulty,
        required_level=boss.required_level,
        is_unlocked=True,
        pass_score_threshold=boss.pass_score_threshold,
        xp_reward=boss.xp_reward,
        title_reward=boss.title_reward,
        objectives=boss.objectives_json or [],
        personal_best_score=None,
        cleared=False,
        total_attempts=0,
    )

@router.post("/bosses/{boss_id}/evaluate-turn")
async def evaluate_arena_turn(
    boss_id: str,
    payload: EvaluateTurnRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates a live turn in the Dojo Boss Arena."""
    service = BossService(db)
    return await service.evaluate_arena_turn(
        user_id=user_id,
        boss_id=boss_id,
        round_index=payload.round_index,
        user_speech=payload.user_speech,
        latency_ms=payload.latency_ms,
    )
'''

if "bosses/generate" not in game_text:
    with open(game_api_path, "a", encoding="utf-8") as f:
        f.write(GAME_ENDPOINTS + "\\n")
    print("Successfully added /bosses/generate and evaluate-turn to game.py")

print("All Dojo Dynamic files created successfully!")
