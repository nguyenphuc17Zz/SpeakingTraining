"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ProviderSettingsSection } from "@/components/settings/provider-settings-section";
import { GeneralSettingsSection } from "@/components/settings/general-settings-section";
import { VoiceSettingsHub } from "@/components/settings/voice-settings-hub";
import { KeybindingsSettingsSection } from "@/components/settings/keybindings-settings-section";
import {
  Settings as SettingsIcon,
  Cpu,
  Sliders,
  Volume2,
  Users,
  ArrowRight,
  Keyboard,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

type SettingsTab = "providers" | "voice" | "keybindings" | "general";

interface NavOption {
  id: SettingsTab;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
}

const NAV_OPTIONS: NavOption[] = [
  {
    id: "providers",
    icon: Cpu,
    label: "Mô hình AI & API Keys",
    description: "OpenAI, Gemini, Groq, Claude & Routing",
  },
  {
    id: "voice",
    icon: Volume2,
    label: "Giọng nói & Âm thanh",
    description: "VOICEVOX, Web Speech & Thử micro",
  },
  {
    id: "keybindings",
    icon: Keyboard,
    label: "Phím tắt hệ thống",
    description: "Tùy biến phím tắt thao tác nhanh",
  },
  {
    id: "general",
    icon: Sliders,
    label: "Cài đặt chung",
    description: "Ngôn ngữ hiển thị & Múi giờ",
  },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("providers");

  return (
    <div className="space-y-6 animate-in fade-in duration-200 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-border bg-card p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
            <SettingsIcon className="h-5 w-5" />
          </span>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground">
              Cài đặt hệ thống
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Cấu hình mô hình AI, bộ tổng hợp giọng nói, phím tắt và thông số người dùng.
            </p>
          </div>
        </div>

        <Link
          href="/speaking"
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted hover:bg-muted/80 border border-border text-foreground text-xs font-semibold transition-colors self-start sm:self-center"
        >
          <Users className="h-4 w-4 text-muted-foreground" />
          <span>Đối tác luyện nói</span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
        </Link>
      </div>

      {/* 2-Column Cockpit Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left Navigation Column (4 cols on desktop) */}
        <aside className="md:col-span-4 lg:col-span-3 space-y-2 sticky top-4">
          <div className="rounded-xl border border-border bg-card p-2 flex flex-col gap-1">
            {NAV_OPTIONS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={cn(
                    "w-full text-left p-2.5 rounded-lg text-xs font-medium transition-all flex items-start gap-3",
                    isActive
                      ? "bg-muted text-foreground font-semibold shadow-2xs"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  )}
                >
                  <span
                    className={cn(
                      "h-7 w-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 border",
                      isActive
                        ? "bg-primary/10 border-primary/20 text-primary"
                        : "bg-muted border-border text-muted-foreground"
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" />
                  </span>
                  <div className="min-w-0">
                    <span className="block truncate font-semibold text-sm leading-tight text-foreground">
                      {item.label}
                    </span>
                    <span className="block text-[11px] text-muted-foreground leading-tight mt-1 truncate">
                      {item.description}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Security & Local Engine Note */}
          <div className="rounded-xl border border-border/80 bg-muted/30 p-3 flex items-center gap-2.5 text-[11px] text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-emerald-500 shrink-0" />
            <span>Mã hóa bảo mật API Key bằng AES-256 cục bộ.</span>
          </div>
        </aside>

        {/* Right Content Column (8-9 cols on desktop) */}
        <main className="md:col-span-8 lg:col-span-9 min-w-0">
          {activeTab === "providers" && <ProviderSettingsSection />}
          {activeTab === "voice" && <VoiceSettingsHub />}
          {activeTab === "keybindings" && <KeybindingsSettingsSection />}
          {activeTab === "general" && <GeneralSettingsSection />}
        </main>
      </div>
    </div>
  );
}

