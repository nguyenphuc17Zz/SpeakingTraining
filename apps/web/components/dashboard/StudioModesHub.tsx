"use client";

import React from "react";
import Link from "next/link";
import {
  Zap,
  Crown,
  Volume2,
  Compass,
  ArrowRight,
  Sparkles,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

const STUDIO_MODES = [
  {
    id: "reflex",
    title: "1. Phản Xạ 3 Giây",
    jaTitle: "瞬発スピーキング",
    tag: "Tốc Độ & Tư Duy Không Dịch",
    desc: "Chuyển ý nghĩ thành câu nói tiếng Nhật dưới 3 giây. Rèn phản xạ không qua bước dịch tiếng Việt.",
    icon: <Zap className="h-5 w-5 text-amber-500" />,
    url: "/reflex",
    color: "amber",
    submodes: ["Mẫu câu cơ bản", "Hội thoại nhanh", "Thử thách áp lực"],
    accentBg: "from-amber-500/10 via-amber-500/5 to-transparent",
  },
  {
    id: "keigo",
    title: "2. Kính Ngữ Công Sở",
    jaTitle: "ビジネス敬語スタジオ",
    tag: "Tôn Kính & Khiêm Nhường",
    desc: "Thực hành Sonkeigo, Kenjougo, quy tắc Uchi/Soto và văn hóa doanh nghiệp Nhật chuẩn mực.",
    icon: <Crown className="h-5 w-5 text-purple-500" />,
    url: "/keigo",
    color: "purple",
    submodes: ["Tôn kính ngữ", "Khiêm nhường ngữ", "Lịch sự trang trọng"],
    accentBg: "from-purple-500/10 via-purple-500/5 to-transparent",
  },
  {
    id: "pitch",
    title: "3. Cao Độ Chuẩn Tokyo",
    jaTitle: "東京アクセント・拍感覚",
    tag: "Cao Độ & Phách Mora",
    desc: "Luyện 4 mô hình cao độ Tokyo, phân biệt cặp từ tối thiểu (雨/飴), trường âm và vô thanh hóa.",
    icon: <Volume2 className="h-5 w-5 text-sky-500" />,
    url: "/pitch",
    color: "sky",
    submodes: ["Cặp từ tối thiểu", "Phách trường âm", "Vô thanh hóa"],
    accentBg: "from-sky-500/10 via-sky-500/5 to-transparent",
  },
  {
    id: "situations",
    title: "4. Tình Huống Vô Tận",
    jaTitle: "場面英会話・無限生成",
    tag: "AI Roleplay Vô Tận",
    desc: "Hàng trăm bối cảnh đối thoại sinh động do Gemini AI tạo mới không giới hạn kèm phản hồi NPC tức thì.",
    icon: <Compass className="h-5 w-5 text-emerald-500" />,
    url: "/situations",
    color: "emerald",
    submodes: ["Công sở & Phỏng vấn", "Đời sống Nhật", "Tùy biến AI"],
    accentBg: "from-emerald-500/10 via-emerald-500/5 to-transparent",
  },
  {
    id: "ramp",
    title: "6. アウトプット・リハビリ",
    jaTitle: "日本語発話訓練",
    tag: "Speaking Ramp — Output Rehab",
    desc: "Từ phản xạ từ đơn → câu hoàn chỉnh → 60 giây độc lập. Rèn phát ngôn tự nhiên theo 11 cấp độ có giáo án.",
    icon: <Sparkles className="h-5 w-5 text-teal-600 dark:text-teal-400" />,
    url: "/ramp",
    color: "teal",
    submodes: ["Echo & Thay thế", "Mở rộng câu", "Phát ngôn tự do"],
    accentBg: "from-teal-500/10 via-teal-500/5 to-transparent",
  },
];

export function StudioModesHub() {
  return (
    <div className="space-y-3">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-6 w-6 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            <Layers className="h-3.5 w-3.5" />
          </span>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <span>Phòng Luyện Thực Chiến</span>
            <span className="text-xs font-normal text-muted-foreground font-jp">実践スタジオ</span>
          </h2>
        </div>

        <span className="text-xs text-muted-foreground">5 chuyên đề</span>
      </div>

      {/* 5 Cards Grid — Minimalist Studio */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
        {STUDIO_MODES.map((mode) => (
          <Link
            key={mode.id}
            href={mode.url}
            prefetch={true}
            onClick={() => soundFX.playKatana()}
            className="group p-4 rounded-2xl border border-border/70 bg-card/60 hover:bg-card hover:border-primary/40 hover:shadow-xs transition-all flex flex-col justify-between relative overflow-hidden"
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="h-9 w-9 rounded-xl bg-muted/50 border border-border/60 flex items-center justify-center text-foreground group-hover:scale-105 transition-transform">
                  {mode.icon}
                </div>
                <span className="text-[10px] font-medium text-muted-foreground bg-muted/40 px-2 py-0.5 rounded-md border border-border/50">
                  {mode.tag.split("—")[0].trim()}
                </span>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {mode.title.replace(/^\d+\.\s*/, "")}
                </h3>
                <p className="text-[10px] text-muted-foreground font-jp">
                  {mode.jaTitle}
                </p>
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {mode.desc}
              </p>
            </div>

            <div className="pt-3 mt-3 border-t border-border/50 flex items-center justify-between text-xs font-medium text-muted-foreground group-hover:text-primary transition-colors">
              <span>Bắt đầu luyện</span>
              <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
