"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Search, Loader2, Users, Sparkles, Filter, X, Volume2, Star } from "lucide-react";
import { VoiceProfile } from "@/types/audio";
import { audioApi } from "../services/audio-api";
import { VoicePreview } from "./VoicePreview";
import { getVoiceCharacterMeta } from "../services/voice-meta";

type FilterTab = "all" | "female" | "male" | "anime" | "calm" | "saved";

interface VoiceSelectorProps {
  selectedVoiceId: string;
  defaultVoiceId?: string;
  selectedProvider?: string;
  sampleText?: string;
  speed?: number;
  pitch?: number;
  savedProfiles?: VoiceProfile[];
  onSelect: (voice: VoiceProfile) => void;
  onSetDefault?: (voice: VoiceProfile) => void;
  className?: string;
}

export function VoiceSelector({
  selectedVoiceId,
  defaultVoiceId,
  selectedProvider = "voicevox",
  sampleText,
  speed = 1.0,
  pitch = 0.0,
  savedProfiles = [],
  onSelect,
  onSetDefault,
  className = "",
}: VoiceSelectorProps) {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    audioApi
      .getVoices(selectedProvider)
      .then((res) => {
        if (isMounted) {
          setVoices(res);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.warn("[VoiceSelector] Failed to load voices:", err);
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedProvider]);

  // Filtered voice list
  const filteredVoices = useMemo(() => {
    let list = voices;

    if (activeFilter === "saved") {
      list = savedProfiles;
    } else if (activeFilter === "female") {
      list = voices.filter((v) => {
        const meta = getVoiceCharacterMeta(v);
        return meta.gender === "female";
      });
    } else if (activeFilter === "male") {
      list = voices.filter((v) => {
        const meta = getVoiceCharacterMeta(v);
        return meta.gender === "male";
      });
    } else if (activeFilter === "anime") {
      list = voices.filter((v) => {
        const meta = getVoiceCharacterMeta(v);
        return meta.gender === "mascot" || meta.vibe === "energetic" || meta.vibe === "cute";
      });
    } else if (activeFilter === "calm") {
      list = voices.filter((v) => {
        const meta = getVoiceCharacterMeta(v);
        return meta.vibe === "calm" || meta.vibe === "gentle" || meta.vibe === "deep";
      });
    }

    if (!searchQuery.trim()) return list;

    const q = searchQuery.toLowerCase().trim();
    return list.filter((v) => {
      const name = (v.name || "").toLowerCase();
      const desc = (v.description || "").toLowerCase();
      const style = (v.style || "").toLowerCase();
      const meta = getVoiceCharacterMeta(v);
      return (
        name.includes(q) ||
        desc.includes(q) ||
        style.includes(q) ||
        meta.vibeLabel.toLowerCase().includes(q) ||
        meta.genderLabel.toLowerCase().includes(q)
      );
    });
  }, [voices, savedProfiles, activeFilter, searchQuery]);

  const FilterChip = ({ id, label, count }: { id: FilterTab; label: string; count?: number }) => (
    <button
      onClick={() => setActiveFilter(id)}
      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 flex items-center gap-1.5 border ${
        activeFilter === id
          ? "bg-primary text-primary-foreground border-primary shadow-sm"
          : "bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground"
      }`}
    >
      {label}
      {count !== undefined && (
        <span
          className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
            activeFilter === id ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-muted-foreground"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Bar & Stats */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Tìm theo tên (Zundamon, Metan, Tsumugi...), phong cách hoặc từ khóa..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 bg-background border border-border rounded-xl text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground p-0.5 rounded"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="text-xs text-muted-foreground shrink-0 flex items-center gap-1.5 px-1">
          <span>Tìm thấy</span>
          <span className="font-bold text-foreground font-mono">{filteredVoices.length}</span>
          <span>giọng đọc</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
        <FilterChip id="all" label="Tất cả" count={voices.length} />
        <FilterChip
          id="female"
          label="👩 Giọng Nữ"
          count={voices.filter((v) => getVoiceCharacterMeta(v).gender === "female").length}
        />
        <FilterChip
          id="male"
          label="👨 Giọng Nam"
          count={voices.filter((v) => getVoiceCharacterMeta(v).gender === "male").length}
        />
        <FilterChip id="anime" label="✨ Nhí nhảnh / Anime" />
        <FilterChip id="calm" label="🍵 Điềm tĩnh / Chuẩn mực" />
        {savedProfiles.length > 0 && (
          <FilterChip id="saved" label="⭐ Đã lưu" count={savedProfiles.length} />
        )}
      </div>

      {/* Voice Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-2">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="text-xs">Đang tải danh mục giọng đọc...</span>
        </div>
      ) : filteredVoices.length === 0 ? (
        <div className="text-center py-12 px-4 rounded-2xl border border-dashed border-border bg-card/40 space-y-2">
          <Volume2 className="h-8 w-8 text-muted-foreground mx-auto opacity-50" />
          <p className="text-sm font-semibold text-foreground">Không tìm thấy giọng đọc phù hợp</p>
          <p className="text-xs text-muted-foreground">
            Hãy thử tìm bằng từ khóa khác hoặc chuyển sang tab bộ lọc khác.
          </p>
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery("");
                setActiveFilter("all");
              }}
              className="text-xs text-primary font-medium hover:underline pt-1 inline-block"
            >
              Xóa bộ lọc tìm kiếm
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[460px] overflow-y-auto pr-1 scrollbar-thin">
          {filteredVoices.map((v) => (
            <VoicePreview
              key={`${v.provider}:${v.voice_id}:${v.name}`}
              voice={v}
              sampleText={sampleText}
              speed={speed}
              pitch={pitch}
              isSelected={v.voice_id === selectedVoiceId}
              isDefault={defaultVoiceId ? v.voice_id === defaultVoiceId : v.is_default}
              onSelect={() => onSelect(v)}
              onSetDefault={onSetDefault ? () => onSetDefault(v) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}
