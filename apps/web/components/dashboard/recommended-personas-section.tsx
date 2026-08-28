"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Dices,
  RefreshCw,
  MessageCircle,
  Volume2,
  X,
  UserCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Persona } from "@/types/persona";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

type TopicCategory = "all" | "daily" | "business" | "casual";

interface PersonaScenario {
  iceBreakerJa: string;
  iceBreakerVi: string;
  scenarioTag: string;
  speakingStyleTag: "タメ口" | "丁寧語" | "敬語";
  category: TopicCategory;
}

interface PersonaVisualTheme {
  avatarGradient: string;
  avatarIcon: string;
  badgeStyle: string;
  topAccent: string;
  roleVi: string;
  buttonClass: string;
  jlptVariant: "n1" | "n2" | "n3" | "n4" | "n5" | "default";
}

const PERSONA_THEMES: Record<string, PersonaVisualTheme> = {
  persona_senpai: {
    avatarGradient: "from-pink-500 via-rose-500 to-pink-600",
    avatarIcon: "🌸",
    badgeStyle: "bg-pink-500/15 text-pink-400 border-pink-500/30",
    topAccent: "from-pink-500/60 via-rose-400/30 to-transparent",
    roleVi: "Tiền bối thân thiện",
    buttonClass: "border-pink-500/30 bg-pink-500/10 text-pink-400 hover:bg-pink-500 hover:text-white",
    jlptVariant: "n3",
  },
  persona_teacher: {
    avatarGradient: "from-cyan-500 via-blue-600 to-indigo-600",
    avatarIcon: "📚",
    badgeStyle: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
    topAccent: "from-cyan-500/60 via-blue-400/30 to-transparent",
    roleVi: "Giảng viên tiếng Nhật",
    buttonClass: "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500 hover:text-white",
    jlptVariant: "n4",
  },
  persona_friend: {
    avatarGradient: "from-amber-500 via-orange-500 to-red-500",
    avatarIcon: "🎧",
    badgeStyle: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    topAccent: "from-amber-500/60 via-orange-400/30 to-transparent",
    roleVi: "Bạn thân Tokyo",
    buttonClass: "border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500 hover:text-white",
    jlptVariant: "n2",
  },
  persona_interviewer: {
    avatarGradient: "from-amber-600 via-yellow-600 to-kintsugi-500",
    avatarIcon: "💼",
    badgeStyle: "bg-kintsugi-400/15 text-kintsugi-500 border-kintsugi-400/30",
    topAccent: "from-kintsugi-400/60 via-amber-500/30 to-transparent",
    roleVi: "Trưởng phòng phỏng vấn",
    buttonClass: "border-kintsugi-400/40 bg-kintsugi-400/10 text-kintsugi-500 hover:bg-kintsugi-400 hover:text-black",
    jlptVariant: "n1",
  },
};

const DEFAULT_SCENARIOS: Record<string, PersonaScenario> = {
  persona_senpai: {
    iceBreakerJa: "「お疲れさま！最近日本語の練習どう？一緒に楽しく話そうよ！」",
    iceBreakerVi: "Vất vả rồi! Dạo này luyện tiếng Nhật thế nào rồi? Cùng trò chuyện thật vui nhé!",
    scenarioTag: "Giao tiếp bạn bè",
    speakingStyleTag: "丁寧語",
    category: "casual",
  },
  persona_teacher: {
    iceBreakerJa: "「こんにちは。今日の文法や発音で気になる点はありますか？」",
    iceBreakerVi: "Xin chào bạn. Hôm nay có điểm ngữ pháp hay phát âm nào bạn muốn luyện không?",
    scenarioTag: "Sửa lỗi ngữ pháp",
    speakingStyleTag: "丁寧語",
    category: "daily",
  },
  persona_friend: {
    iceBreakerJa: "「やっほー！週末どっか遊びに行く？最近のアニメの話もしようぜ！」",
    iceBreakerVi: "Yo! Cuối tuần có đi đâu chơi không? Cùng đàm đạo về mấy bộ anime hot gần đây đi!",
    scenarioTag: "Khẩu ngữ Tokyo",
    speakingStyleTag: "タメ口",
    category: "casual",
  },
  persona_interviewer: {
    iceBreakerJa: "「本日はお時間をいただきありがとうございます。自己紹介をお願いできますか。」",
    iceBreakerVi: "Cảm ơn bạn đã dành thời gian hôm nay. Bạn có thể giới thiệu ngắn gọn bản thân được không.",
    scenarioTag: "Phỏng vấn công việc",
    speakingStyleTag: "敬語",
    category: "business",
  },
};

const GENERIC_SCENARIOS: PersonaScenario[] = [
  {
    iceBreakerJa: "「いらっしゃいませ！本日はどのようなご用件でしょうか？」",
    iceBreakerVi: "Kính chào quý khách! Hôm nay tôi có thể hỗ trợ gì cho bạn ạ?",
    scenarioTag: "Dịch vụ & Mua sắm",
    speakingStyleTag: "丁寧語",
    category: "daily",
  },
  {
    iceBreakerJa: "「プロジェクトの進捗について、少しお時間よろしいでしょうか。」",
    iceBreakerVi: "Về tiến độ dự án, tôi có thể xin một chút thời gian của bạn được không ạ.",
    scenarioTag: "Họp công sở",
    speakingStyleTag: "敬語",
    category: "business",
  },
  {
    iceBreakerJa: "「ねえねえ、今日のランチどこ行く？美味しいラーメン屋見つけたんだ！」",
    iceBreakerVi: "Nè nè, trưa nay ăn ở đâu ta? Mình mới tìm thấy quán ramen ngon lắm nè!",
    scenarioTag: "Ăn uống thường nhật",
    speakingStyleTag: "タメ口",
    category: "daily",
  },
];

export function RecommendedPersonasSection({
  personas = [],
  loading = false,
}: {
  personas: Persona[];
  loading?: boolean;
}) {
  const [selectedCategory, setSelectedCategory] = useState<TopicCategory>("all");
  const [shuffleSeed, setShuffleSeed] = useState(0);
  const [randomModalPersona, setRandomModalPersona] = useState<Persona | null>(null);
  const [isShuffling, setIsShuffling] = useState(false);

  const getPersonaScenario = (p: Persona, index: number): PersonaScenario => {
    if (DEFAULT_SCENARIOS[p.id]) return DEFAULT_SCENARIOS[p.id];
    const lower = (p.role + " " + p.description + " " + p.speaking_style).toLowerCase();
    if (lower.includes("business") || lower.includes("interviewer") || lower.includes("keigo") || lower.includes("kính ngữ")) {
      return {
        iceBreakerJa: "「本日はよろしくお願いいたします。何かご不明な点はございますか。」",
        iceBreakerVi: "Hôm nay rất mong được hợp tác cùng bạn. Bạn có thắc mắc gì không ạ.",
        scenarioTag: "Thương mại & Công sở",
        speakingStyleTag: "敬語",
        category: "business",
      };
    }
    if (lower.includes("friend") || lower.includes("casual") || lower.includes("tameguchi") || lower.includes("thân mật")) {
      return {
        iceBreakerJa: "「最近調子どう？気軽に日本語で何でも話しかけてね！」",
        iceBreakerVi: "Dạo này khỏe không? Cứ thoải mái nói chuyện tiếng Nhật với mình nha!",
        scenarioTag: "Bạn bè thân mật",
        speakingStyleTag: "タメ口",
        category: "casual",
      };
    }
    return GENERIC_SCENARIOS[index % GENERIC_SCENARIOS.length];
  };

  const getPersonaTheme = (p: Persona, index: number): PersonaVisualTheme => {
    if (PERSONA_THEMES[p.id]) return PERSONA_THEMES[p.id];
    const gradients = [
      "from-pink-500 via-rose-500 to-pink-600",
      "from-cyan-500 via-blue-600 to-indigo-600",
      "from-amber-500 via-orange-500 to-red-500",
      "from-emerald-500 via-teal-600 to-green-600",
    ];
    const icons = ["🌸", "📚", "🎧", "🍵"];
    const gIdx = index % gradients.length;
    return {
      avatarGradient: gradients[gIdx],
      avatarIcon: icons[gIdx],
      badgeStyle: "bg-primary/15 text-primary border-primary/30",
      topAccent: "from-primary/60 via-emerald-500/30 to-transparent",
      roleVi: p.role,
      buttonClass: "border-primary/30 bg-primary/10 text-primary hover:bg-primary hover:text-white",
      jlptVariant: "default",
    };
  };

  const displayedPersonas = useMemo(() => {
    if (!personas.length) return [];

    let list = [...personas];

    if (selectedCategory !== "all") {
      list = list.filter((p, idx) => {
        const sc = getPersonaScenario(p, idx);
        return sc.category === selectedCategory;
      });
    }

    if (!list.length) list = [...personas];

    if (shuffleSeed > 0) {
      list = [...list].sort(() => Math.sin(shuffleSeed + 0.5) - 0.5);
    }

    return list.slice(0, 4);
  }, [personas, selectedCategory, shuffleSeed]);

  const handleShuffle = () => {
    soundFX.playSuikinkutsu();
    setIsShuffling(true);
    setShuffleSeed((prev) => prev + 1);
    setTimeout(() => setIsShuffling(false), 300);
  };

  const handleRandomMatch = () => {
    if (!personas.length) return;
    soundFX.playFurin();
    setTimeout(() => soundFX.playTaiko(), 150);

    const randomIndex = Math.floor(Math.random() * personas.length);
    setRandomModalPersona(personas[randomIndex]);
  };

  const playSpeech = (text: string) => {
    if (typeof window === "undefined") return;
    soundFX.playSuikinkutsu();
    const utterance = new SpeechSynthesisUtterance(text.replace(/[「」]/g, ""));
    utterance.lang = "ja-JP";
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="space-y-4">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="h-8 w-8 rounded-xl bg-gradient-to-br from-primary/20 to-emerald-500/25 border border-primary/25 flex items-center justify-center text-primary shadow-sm">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm sm:text-base font-black text-foreground font-display tracking-tight">
                Đối Tác Hội Thoại Gợi Ý
              </h2>
              <span className="text-xs font-semibold text-muted-foreground font-jp">おすすめ会話相手</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Chọn đối tác phù hợp để luyện phản xạ tiếng Nhật tự nhiên mỗi ngày
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          <Button
            variant="primary"
            size="sm"
            onClick={handleRandomMatch}
            disabled={loading || !personas.length}
            className="text-xs font-bold gap-1.5 shadow-md"
            title="Ghép ngẫu nhiên một người bạn hội thoại bất ngờ"
          >
            <Dices className="h-3.5 w-3.5" />
            <span>Ghép ngẫu nhiên</span>
            <span className="text-[10px] font-jp opacity-90">出会い</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleShuffle}
            disabled={loading || isShuffling}
            className="text-xs font-bold gap-1.5 border-border"
            title="Đổi nhóm đối tác khác"
          >
            <RefreshCw className={cn("h-3 w-3", isShuffling && "animate-spin text-primary")} />
            <span>Đổi nhóm</span>
          </Button>

          <Link
            href="/speaking"
            className="text-xs font-bold text-primary hover:text-primary/80 flex items-center gap-1 transition-colors ml-1"
          >
            Tất cả <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Topic Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none pb-0.5">
        {[
          { id: "all", label: "🌟 Tất cả gợi ý", ja: "全般" },
          { id: "daily", label: "🍜 Đời sống & Du lịch", ja: "日常" },
          { id: "business", label: "💼 Công sở & Phỏng vấn", ja: "仕事" },
          { id: "casual", label: "⚡ Bạn bè & Anime", ja: "友達" },
        ].map((tab) => {
          const isSelected = selectedCategory === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                soundFX.playSuikinkutsu();
                setSelectedCategory(tab.id as TopicCategory);
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-1.5 border",
                isSelected
                  ? "bg-primary/15 text-primary border-primary/40 shadow-sm"
                  : "bg-card/70 border-border/80 text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <span>{tab.label}</span>
              <span className="text-[10px] font-jp opacity-70">({tab.ja})</span>
            </button>
          );
        })}
      </div>

      {/* Grid of 4 Persona Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-5">
        {loading ? (
          <div className="col-span-4 p-12 text-center text-sm text-muted-foreground">
            Đang tải danh sách đối tác…
          </div>
        ) : displayedPersonas.length === 0 ? (
          <div className="col-span-4 p-8 text-center text-sm text-muted-foreground">
            Không tìm thấy đối tác trong chủ đề này.
          </div>
        ) : (
          displayedPersonas.map((persona, idx) => {
            const scenario = getPersonaScenario(persona, idx);
            const visual = getPersonaTheme(persona, idx);

            return (
              <div
                key={persona.id}
                className="relative rounded-[22px] border border-border/80 bg-card/95 washi-texture p-5 flex flex-col justify-between transition-all duration-200 hover:border-border hover:shadow-sumi hover:-translate-y-1 group overflow-hidden min-h-[310px]"
              >
                {/* Top Ambient Highlight Gradient */}
                <div className={cn("absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r opacity-90", visual.topAccent)} />

                {/* Top Section: Avatar & Badges */}
                <div className="space-y-3.5 relative z-10">
                  <div className="flex items-start justify-between gap-2">
                    {/* Unique Avatar with Emoji + Online Glow */}
                    <div className="relative">
                      <span
                        className={cn(
                          "h-12 w-12 rounded-2xl bg-gradient-to-br flex items-center justify-center text-2xl shadow-md group-hover:scale-105 transition-transform duration-200 border border-white/15",
                          visual.avatarGradient
                        )}
                      >
                        {visual.avatarIcon}
                      </span>
                      {/* Live Online Pulsing Indicator */}
                      <span
                        className="absolute -bottom-0.5 -right-0.5 flex h-3.5 w-3.5"
                        title="Đang trực tuyến sẵn sàng luyện nói"
                      >
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500 border-2 border-card" />
                      </span>
                    </div>

                    {/* Speaking Style & JLPT Badges */}
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      <span
                        className={cn(
                          "text-[10px] font-jp font-bold px-2 py-0.5 rounded-full border tracking-wide",
                          visual.badgeStyle
                        )}
                      >
                        {scenario.speakingStyleTag}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-muted/90 border border-border text-[10px] font-sans font-black text-foreground">
                        {persona.difficulty || "N3"}
                      </span>
                    </div>
                  </div>

                  {/* Name & Role Description */}
                  <div className="space-y-0.5">
                    <h3 className="text-sm sm:text-[15px] font-black text-foreground font-sans tracking-tight group-hover:text-primary transition-colors line-clamp-1">
                      {persona.name}
                    </h3>
                    <p className="text-xs text-muted-foreground font-medium line-clamp-1">
                      {visual.roleVi}
                    </p>
                  </div>

                  {/* Ice-Breaker Speech Bubble */}
                  <div className="relative rounded-2xl bg-muted/60 border border-border/80 p-3 space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-jp font-bold text-foreground leading-relaxed line-clamp-2">
                        {scenario.iceBreakerJa}
                      </p>
                      <button
                        type="button"
                        onClick={() => playSpeech(scenario.iceBreakerJa)}
                        className="h-6 w-6 rounded-lg bg-card/80 hover:bg-muted border border-border/60 flex items-center justify-center text-muted-foreground hover:text-primary shrink-0 transition-colors shadow-sm"
                        title="Nghe phát âm câu chào"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                      {scenario.iceBreakerVi}
                    </p>
                  </div>
                </div>

                {/* Footer Action Button */}
                <div className="pt-3.5 relative z-10">
                  <Link href={`/speaking`} className="w-full block">
                    <button
                      type="button"
                      onClick={() => soundFX.playTaiko()}
                      className={cn(
                        "w-full h-9 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all duration-200 shadow-sm active:scale-98",
                        visual.buttonClass
                      )}
                    >
                      <MessageCircle className="h-3.5 w-3.5" />
                      <span>Trò chuyện ngay</span>
                    </button>
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Random Match Encounter Modal (Gặp gỡ bất ngờ) */}
      {randomModalPersona && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-[28px] border-2 border-kintsugi-400/40 bg-card/95 washi-texture shadow-sumi-lg p-6 overflow-hidden">
            {/* Ambient enso backdrop */}
            <div className="absolute -top-12 -right-12 h-40 w-40 rounded-full bg-enso-gradient opacity-40 pointer-events-none" />

            <button
              onClick={() => setRandomModalPersona(null)}
              className="absolute top-4 right-4 h-8 w-8 rounded-full bg-muted/80 hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-2.5 mb-4">
              <span className="text-2xl">🎲</span>
              <div>
                <h3 className="text-base font-black text-foreground font-sans">
                  Gặp Gỡ Bất Ngờ Tại Tokyo
                </h3>
                <p className="text-xs text-muted-foreground font-jp">偶然の出会い・会話マッチ</p>
              </div>
            </div>

            <div className="rounded-2xl border border-primary/30 bg-muted/40 p-4 space-y-3">
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "h-12 w-12 rounded-2xl bg-gradient-to-br flex items-center justify-center text-2xl shadow-md border border-white/15",
                    getPersonaTheme(randomModalPersona, 0).avatarGradient
                  )}
                >
                  {getPersonaTheme(randomModalPersona, 0).avatarIcon}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-black text-foreground font-sans">{randomModalPersona.name}</h4>
                    <span className="px-2 py-0.5 rounded-full bg-muted border border-border text-[10px] font-sans font-black text-foreground">
                      {randomModalPersona.difficulty || "N3"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-medium">{getPersonaTheme(randomModalPersona, 0).roleVi}</p>
                </div>
              </div>

              <div className="rounded-xl bg-card p-3 border border-border/80 space-y-1.5">
                <span className="text-[10px] font-bold text-muted-foreground uppercase">Tình huống mở đầu:</span>
                <p className="text-xs font-jp font-bold text-foreground leading-snug">
                  {getPersonaScenario(randomModalPersona, 0).iceBreakerJa}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {getPersonaScenario(randomModalPersona, 0).iceBreakerVi}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 mt-5">
              <Button
                variant="outline"
                size="md"
                onClick={handleRandomMatch}
                className="flex-1 text-xs font-bold gap-1"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Ghép người khác
              </Button>

              <Link href="/speaking" className="flex-[1.3]">
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => soundFX.playTaiko()}
                  className="w-full text-xs font-bold gap-1.5 shadow-md"
                >
                  <MessageCircle className="h-4 w-4" />
                  Bắt đầu nói ngay
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
