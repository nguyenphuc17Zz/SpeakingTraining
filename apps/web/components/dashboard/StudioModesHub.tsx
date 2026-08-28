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
];

export function StudioModesHub() {
  return (
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-7 w-7 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
            <Layers className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>4 Phòng Luyện Studio Thực Chiến</span>
              <span className="text-xs font-semibold text-muted-foreground font-jp">実践スタジオ</span>
            </h2>
          </div>
        </div>

        <Badge variant="kintsugi" size="sm" className="font-bold text-[10px]">
          100% DYNAMIC AI
        </Badge>
      </div>

      {/* 4 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {STUDIO_MODES.map((mode) => (
          <div
            key={mode.id}
            className="p-5 rounded-3xl border border-border/80 bg-card washi-texture shadow-xs hover:border-primary/40 hover:shadow-md transition-all flex flex-col justify-between group relative overflow-hidden"
          >
            <div className={cn("absolute top-0 right-0 h-32 w-32 bg-gradient-to-bl rounded-full blur-2xl pointer-events-none opacity-60", mode.accentBg)} />

            <div className="space-y-3 relative z-10">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-2xl bg-muted/60 border border-border/80 shadow-2xs group-hover:scale-105 transition-transform">
                  {mode.icon}
                </div>
                <Badge variant="outline" size="sm" className="text-[10px] font-semibold text-muted-foreground">
                  {mode.tag.split("&")[0]}
                </Badge>
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                  {mode.title}
                </h3>
                <p className="text-[10px] text-muted-foreground font-jp font-medium">
                  {mode.jaTitle}
                </p>
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                {mode.desc}
              </p>

              {/* Sub-modes tags */}
              <div className="flex flex-wrap gap-1 pt-1">
                {mode.submodes.map((sub, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-muted/40 text-muted-foreground border border-border/60"
                  >
                    {sub}
                  </span>
                ))}
              </div>
            </div>

            {/* Launch Button */}
            <div className="pt-4 mt-2 border-t border-border/60 relative z-10">
              <Link href={mode.url} className="w-full block">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => soundFX.playKatana()}
                  className="w-full text-xs font-bold justify-between rounded-xl h-8.5 hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all shadow-2xs"
                >
                  <span>Vào phòng luyện</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
