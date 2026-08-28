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
} from "lucide-react";

type SettingsTab = "providers" | "voice" | "keybindings" | "general";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("providers");

  const TabBtn = ({ id, icon: Icon, label }: { id: SettingsTab; icon: any; label: string }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl border transition-colors shrink-0 ${
        activeTab === id
          ? "bg-primary text-primary-foreground border-primary shadow-sm"
          : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="relative overflow-hidden rounded-[24px] border border-border bg-card washi-texture shadow-washi p-6">
        <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
              <SettingsIcon className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                Cài đặt hệ thống <span className="font-jp text-sm font-normal text-muted-foreground">設定</span>
              </h1>
              <p className="text-sm text-muted-foreground">
                Quản lý các AI Provider, kết nối VOICEVOX/Whisper, tùy biến phím tắt và cấu hình chung.
              </p>
            </div>
          </div>

          <Link
            href="/speaking"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary/10 hover:bg-primary/20 border border-primary/20 text-primary text-xs font-bold transition-colors self-start sm:self-center"
          >
            <Users className="h-4 w-4" />
            <span>Quản lý đối tác tại Luyện nói</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
        <TabBtn id="providers" icon={Cpu} label="AI Providers" />
        <TabBtn id="voice" icon={Volume2} label="Giọng nói & Âm thanh" />
        <TabBtn id="keybindings" icon={Keyboard} label="Phím tắt (Keybindings)" />
        <TabBtn id="general" icon={Sliders} label="Chung" />
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "providers" && <ProviderSettingsSection />}
        {activeTab === "voice" && <VoiceSettingsHub />}
        {activeTab === "keybindings" && <KeybindingsSettingsSection />}
        {activeTab === "general" && <GeneralSettingsSection />}
      </div>
    </div>
  );
}

