"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Target,
  Clock,
  Wand2,
  Briefcase,
  Store,
  MessageCircle,
  Plane,
  Award,
  Edit3,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface CurriculumOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (data: {
    level: string;
    target_goal: string;
    daily_minutes: number;
    custom_wish?: string;
  }) => Promise<void>;
  currentLevel?: string;
  currentGoal?: string;
  currentMinutes?: number;
}

export const LEVELS = [
  { id: "beginner", label: "N5 • Sơ Cấp 1", desc: "Mới bắt đầu, phát âm & câu đơn" },
  { id: "elementary", label: "N4 • Sơ Cấp 2", desc: "Ngữ pháp căn bản & sinh hoạt" },
  { id: "intermediate", label: "N3 • Trung Cấp", desc: "Giao tiếp tự nhiên & đời sống" },
  { id: "advanced", label: "N2 • Trung Cao Cấp", desc: "Kính ngữ & môi trường công sở" },
  { id: "fluent", label: "N1 • Cao Cấp", desc: "Thuyết trình, đàm phán lưu loát" },
];

export const GOALS = [
  {
    id: "workplace",
    title: "Công Sở & Doanh Nghiệp (ビジネス)",
    desc: "Kính ngữ, báo cáo Hou-Ren-So, tiếp đối tác và viết email",
    icon: <Briefcase className="h-4 w-4 text-purple-500" />,
  },
  {
    id: "baito",
    title: "Phỏng Vấn & Làm Thêm (バイト面接)",
    desc: "Giao tiếp Konbini, nhà hàng, ứng xử lịch làm và xin phép",
    icon: <Store className="h-4 w-4 text-emerald-500" />,
  },
  {
    id: "daily",
    title: "Đời Sống & Kết Bạn (日常会話)",
    desc: "Phản xạ nhanh, mua sắm, nhà ga, kết bạn và tiệc tùng",
    icon: <MessageCircle className="h-4 w-4 text-amber-500" />,
  },
  {
    id: "travel",
    title: "Du Lịch & Định Cư (観光・生活)",
    desc: "Hỏi đường, khách sạn, y tế khẩn cấp và thủ tục hành chính",
    icon: <Plane className="h-4 w-4 text-sky-500" />,
  },
  {
    id: "exam",
    title: "Luyện Thi Kaiwa & JLPT (試験対策)",
    desc: "Tổng hợp mẫu câu trọng điểm, ngữ pháp và phát âm chuẩn",
    icon: <Award className="h-4 w-4 text-rose-500" />,
  },
];

export const MINUTES = [
  { mins: 15, label: "15 phút • Nhẹ nhàng" },
  { mins: 30, label: "30 phút • Tiêu chuẩn" },
  { mins: 45, label: "45 phút • Chuyên sâu" },
  { mins: 60, label: "60 phút • Đột phá" },
];

export function CurriculumOnboardingModal({
  isOpen,
  onClose,
  onGenerate,
  currentLevel = "intermediate",
  currentGoal = "workplace",
  currentMinutes = 30,
}: CurriculumOnboardingModalProps) {
  const [level, setLevel] = useState(currentLevel);
  const [goal, setGoal] = useState(currentGoal);
  const [dailyMinutes, setDailyMinutes] = useState(currentMinutes);
  const [customWish, setCustomWish] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    soundFX.playKatana();
    try {
      await onGenerate({
        level,
        target_goal: goal,
        daily_minutes: dailyMinutes,
        custom_wish: customWish.trim() || undefined,
      });
      onClose();
    } catch (e) {
      console.error("Failed to generate curriculum:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Thiết Lập Lộ Trình Học Nói Tiếng Nhật Cá Nhân Hóa"
      description="AI sẽ phân tích trình độ và mục tiêu để thiết kế lộ trình 4 chặng độc quyền cho bạn"
      className="max-w-3xl"
    >
      <div className="space-y-6 pt-2">
        {/* Step 1: Current Level */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
              1
            </span>
            <span>Trình độ tiếng Nhật hiện tại của bạn:</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {LEVELS.map((lvl) => (
              <button
                key={lvl.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setLevel(lvl.id);
                }}
                className={cn(
                  "p-2.5 rounded-xl border text-left transition-all space-y-0.5",
                  level === lvl.id
                    ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/30"
                    : "bg-muted/40 border-border/80 hover:border-primary/40"
                )}
              >
                <div className="text-xs font-bold text-foreground">{lvl.label}</div>
                <div className="text-[10px] text-muted-foreground">{lvl.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Target Goal */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
              2
            </span>
            <span>Mục tiêu rèn luyện trọng tâm:</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {GOALS.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setGoal(g.id);
                }}
                className={cn(
                  "p-3 rounded-xl border text-left transition-all flex items-start gap-2.5",
                  goal === g.id
                    ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/30"
                    : "bg-muted/40 border-border/80 hover:border-primary/40"
                )}
              >
                <div className="p-1.5 rounded-lg bg-card border border-border/80 shrink-0 mt-0.5">
                  {g.icon}
                </div>
                <div className="space-y-0.5 min-w-0 flex-1">
                  <div className="text-xs font-bold text-foreground">{g.title}</div>
                  <div className="text-[11px] text-muted-foreground leading-snug">{g.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Daily Minutes & Custom Wish */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-foreground">
              <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
                3
              </span>
              <span>Thời gian rèn luyện mỗi ngày:</span>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              {MINUTES.map((m) => (
                <button
                  key={m.mins}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDailyMinutes(m.mins);
                  }}
                  className={cn(
                    "p-2 rounded-xl border text-center text-xs font-bold transition-all",
                    dailyMinutes === m.mins
                      ? "bg-primary text-primary-foreground border-primary shadow-xs"
                      : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                  )}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-foreground">
              <Edit3 className="h-4 w-4 text-primary" />
              <span>Nguyện vọng riêng biệt (Tùy chọn):</span>
            </div>

            <textarea
              value={customWish}
              onChange={(e) => setCustomWish(e.target.value)}
              placeholder="VD: Muốn tập trung sửa lỗi từ đệm ano/etto và đàm phán hợp đồng IT..."
              rows={2}
              className="w-full bg-background border border-border rounded-xl p-2.5 text-xs focus:outline-none focus:border-primary resize-none placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-3 border-t border-border flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isSubmitting}
            className="text-xs font-semibold"
          >
            Hủy bỏ
          </Button>

          <Button
            variant="akane"
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="text-xs font-bold gap-2 px-6 h-10 rounded-xl shadow-md"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>AI Đang Thiết Kế Lộ Trình...</span>
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4" />
                <span>✨ Tạo Lộ Trình Độc Quyền</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
