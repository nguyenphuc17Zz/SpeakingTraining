"use client";

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
