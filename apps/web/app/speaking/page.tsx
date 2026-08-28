"use client";

import React, { useState, useEffect } from "react";
import { usePersonas } from "@/hooks/use-personas";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { CoachQuickActions, CoachPanel } from "@/features/coach";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { SpeakingLiveCoachOverlay } from "@/features/coach/components/SpeakingLiveCoachOverlay";
import { SpeakingPostSessionCoachCard } from "@/features/coach/components/SpeakingPostSessionCoachCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import {
  Mic,
  Sparkles,
  Lock,
  Zap,
  Plus,
  Wand2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  RotateCcw,
  Users,
} from "lucide-react";
import { Persona, PersonaCreateInput } from "@/types/persona";
import {
  useVoiceSession,
  SessionLobby,
  ActiveSessionRoom,
  SessionSummaryModal,
  MicrophonePermissionModal,
} from "@/features/speaking";

const DIFFICULTIES = ["All", "N5", "N4", "N3", "N2", "N1"];

const INITIAL_FORM: PersonaCreateInput = {
  name: "",
  role: "",
  description: "",
  personality: "",
  speaking_style: "",
  difficulty: "N3",
  system_prompt: "",
};

export default function SpeakingPage() {
  const {
    personas,
    loading,
    actionLoading,
    generating,
    createPersona,
    deletePersona,
    generateRandomPersona,
    restoreDefaults,
  } = usePersonas();

  const [selectedDifficulty, setSelectedDifficulty] = useState("All");
  const [activePersona, setActivePersona] = useState<Persona | null>(null);
  const [isLobbyOpen, setIsLobbyOpen] = useState(false);
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  // Persona Creation & Deletion States
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [formData, setFormData] = useState<PersonaCreateInput>(INITIAL_FORM);
  const [aiThemeHint, setAiThemeHint] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Persona | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const {
    session,
    turns,
    state,
    volumeLevel,
    isUserSpeaking,
    isInitializing,
    formattedElapsed,
    formattedSpeaking,
    isVoiceMuted,
    toggleVoiceMute,
    autoEndOfSpeech,
    toggleAutoEndOfSpeech,
    interimTranscript,
    latestUserTranscript,
    latestSttMetrics,
    startSession,
    sendTextTurn,
    isManualRecording,
    manualSeconds,
    startManualRecording,
    stopAndSendManualRecording,
    pauseSession,
    resumeSession,
    endSession,
    resetSession,
    replayVoice,
    hasPermission,
    requestPermission,
    summary,
  } = useVoiceSession();

  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  useEffect(() => {
    if (summary !== null && state === "ended") {
      setIsSummaryOpen(true);
    }
  }, [summary, state]);

  const handleCloseSummary = () => {
    setIsSummaryOpen(false);
    setActivePersona(null);
    resetSession();
  };

  const filteredPersonas = personas.filter((p) => {
    if (selectedDifficulty === "All") return true;
    return p.difficulty.toUpperCase() === selectedDifficulty;
  });

  const handleOpenLobby = (persona: Persona) => {
    setActivePersona(persona);
    setIsLobbyOpen(true);
  };

  const handleStartFromLobby = async (mode: any, config: any) => {
    if (!activePersona) return;
    setIsLobbyOpen(false);
    await startSession(activePersona, mode, config);
  };

  const resetCreateForm = () => {
    setFormData(INITIAL_FORM);
    setAiThemeHint("");
  };

  const handleOpenCreateModal = () => {
    resetCreateForm();
    setIsCreateModalOpen(true);
  };

  const handleCreatePersona = async () => {
    if (!formData.name.trim() || !formData.role.trim()) {
      setFeedback({ type: "error", msg: "Vui lòng nhập tên và vai trò của đối tác." });
      return;
    }
    const ok = await createPersona(formData);
    if (ok) {
      setIsCreateModalOpen(false);
      resetCreateForm();
      setFeedback({ type: "success", msg: `Đã tạo đối tác “${formData.name}” thành công!` });
      setTimeout(() => setFeedback(null), 4000);
    } else {
      setFeedback({ type: "error", msg: "Không thể tạo đối tác. Vui lòng kiểm tra lại thông tin." });
    }
  };

  const handleGenerateAI = async () => {
    setFeedback(null);
    const targetDiff = formData.difficulty || (selectedDifficulty !== "All" ? selectedDifficulty : "N3");
    const { data: result, error: genError } = await generateRandomPersona({
      difficulty: targetDiff,
      theme: aiThemeHint.trim() || undefined,
    });

    if (result) {
      setFormData({
        name: result.name,
        role: result.role,
        description: result.description,
        personality: result.personality,
        speaking_style: result.speaking_style,
        difficulty: result.difficulty || targetDiff,
        system_prompt: result.system_prompt || "",
      });
      setIsCreateModalOpen(true);
      setFeedback({
        type: "success",
        msg: `✨ AI đã tạo đối tác “${result.name}” (${result.difficulty}). Bạn có thể chỉnh sửa rồi bấm Lưu.`,
      });
    } else {
      setFeedback({
        type: "error",
        msg: genError || "Không thể tạo đối tác bằng AI. Vui lòng kiểm tra cấu hình API Key trong mục Cài đặt.",
      });
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    const ok = await deletePersona(deleteTarget.id);
    if (ok) {
      setFeedback({ type: "success", msg: `Đã xóa đối tác “${deleteTarget.name}”.` });
      setTimeout(() => setFeedback(null), 3500);
    } else {
      setFeedback({ type: "error", msg: "Không thể xóa đối tác. Vui lòng thử lại." });
    }
    setDeleteTarget(null);
  };

  const handleRestoreDefaults = async () => {
    setFeedback(null);
    const ok = await restoreDefaults();
    if (ok) {
      setFeedback({
        type: "success",
        msg: "Đã khôi phục thành công các đối tác mẫu mặc định (Yuki Senpai, Takahashi Sensei, Ren, Tanaka Bucho)!",
      });
      setTimeout(() => setFeedback(null), 4000);
    } else {
      setFeedback({ type: "error", msg: "Không thể khôi phục đối tác mẫu. Vui lòng thử lại." });
    }
  };

  const isSessionActive =
    session !== null &&
    (state === "listening" ||
      state === "processing_stt" ||
      state === "ai_thinking" ||
      state === "ai_speaking" ||
      state === "paused" ||
      state === "ready");

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/speaking", sessionId: session?.id }), 300);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Coach proactive insight */}
      {insights.length > 0 && !isSessionActive && (
        <div className="space-y-2">
          {insights.slice(0, 1).map((ins, idx) => (
            <CoachInsightCard
              key={idx}
              insight={ins}
              onDismiss={() => dismiss(ins.insight_type)}
              onAction={() => handleCoachSelect(`Luyện ${ins.recommended_action || ins.insight_type} cho tui`)}
            />
          ))}
        </div>
      )}

      {/* Speaking + Coach quick actions bar */}
      {!isSessionActive && (
        <div className="p-3 rounded-xl bg-card border border-border flex flex-col gap-2">
          <span className="text-xs font-bold text-muted-foreground">🤖 AI Coach — Hỏi ngay khi đang chọn phòng</span>
          <CoachQuickActions route={pathname || "/speaking"} onSelect={handleCoachSelect} />
        </div>
      )}

      {/* Feedback Toast Banner */}
      {feedback && !isSessionActive && (
        <div
          className={`p-3.5 rounded-xl border text-sm flex items-center justify-between gap-3 shadow-sm ${
            feedback.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300"
              : "bg-destructive/10 border-destructive/20 text-destructive"
          }`}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            {feedback.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
            )}
            <span className="font-medium truncate">{feedback.msg}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-xs font-bold px-2 py-1 hover:opacity-75 rounded transition-opacity"
          >
            ✕
          </button>
        </div>
      )}

      {isSessionActive && activePersona ? (
        <div className="space-y-3">
          <SpeakingLiveCoachOverlay sessionId={session?.id} isActive={isSessionActive} />
          <ActiveSessionRoom
            session={session!}
            persona={activePersona}
            turns={turns}
            state={state}
            volumeLevel={volumeLevel}
            isUserSpeaking={isUserSpeaking}
            formattedElapsed={formattedElapsed}
            formattedSpeaking={formattedSpeaking}
            isVoiceMuted={isVoiceMuted}
            onToggleVoiceMute={toggleVoiceMute}
            autoEndOfSpeech={autoEndOfSpeech}
            onToggleAutoEndOfSpeech={toggleAutoEndOfSpeech}
            latestUserTranscript={latestUserTranscript}
            interimTranscript={interimTranscript}
            latestSttMetrics={latestSttMetrics}
            isManualRecording={isManualRecording}
            manualSeconds={manualSeconds}
            onStartManualRecording={startManualRecording}
            onStopManualRecording={stopAndSendManualRecording}
            hasPermission={hasPermission}
            onRequestPermission={requestPermission}
            onSendTextTurn={sendTextTurn}
            onPause={pauseSession}
            onResume={resumeSession}
            onEndSession={endSession}
            onReplayVoice={replayVoice}
          />
          <div className="p-3 rounded-xl bg-card border border-dashed flex flex-col gap-2">
            <span className="text-xs font-bold text-muted-foreground">
              🤖 Coach trong phiên nói — hỏi ngay không cần thoát
            </span>
            <CoachQuickActions route={pathname || "/speaking"} onSelect={handleCoachSelect} />
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header washi */}
          <div className="relative overflow-hidden rounded-[24px] border border-border bg-card washi-texture shadow-washi p-6">
            <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-enso-gradient opacity-40 pointer-events-none" />
            <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-5">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary">
                    <Mic className="h-5 w-5" />
                  </span>
                  <h1 className="text-xl font-bold tracking-tight text-foreground">
                    Phòng luyện nói <span className="font-jp text-sm font-normal text-muted-foreground">会話練習</span>
                  </h1>
                </div>
                <p className="text-sm text-muted-foreground max-w-xl">
                  Chọn, tạo mới hoặc xóa đối tác hội thoại AI để luyện nói tự nhiên theo thời gian thực (Faster-Whisper, AI Router, VOICEVOX).
                </p>
              </div>

              {/* Partner Management Action Buttons */}
              <div className="flex items-center gap-2.5 flex-wrap shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRestoreDefaults}
                  isLoading={actionLoading}
                  className="text-xs text-muted-foreground hover:text-foreground border-border"
                  title="Khôi phục lại các đối tác mẫu mặc định của hệ thống"
                >
                  <RotateCcw className="h-3.5 w-3.5 mr-1" />
                  Khôi phục mẫu
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateAI}
                  isLoading={generating}
                  className="text-xs border-primary/30 text-foreground hover:border-primary"
                >
                  <Wand2 className="h-4 w-4 text-primary" />
                  Tạo ngẫu nhiên AI
                </Button>

                <Button
                  variant="akane"
                  size="sm"
                  onClick={handleOpenCreateModal}
                  className="text-xs"
                >
                  <Plus className="h-4 w-4" />
                  Tạo đối tác mới
                </Button>
              </div>
            </div>

            {/* Difficulty Filter Bar */}
            <div className="relative mt-5 pt-4 border-t border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mr-1">
                  <Users className="h-3.5 w-3.5" /> Trình độ:
                </span>
                <div className="flex items-center gap-1 p-1 rounded-xl bg-muted border border-border overflow-x-auto">
                  {DIFFICULTIES.map((diff) => (
                    <button
                      key={diff}
                      onClick={() => setSelectedDifficulty(diff)}
                      className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors whitespace-nowrap ${
                        selectedDifficulty === diff
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {diff === "All" ? "Tất cả" : diff}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="sakura" size="sm">
                  {filteredPersonas.length} đối tác sẵn sàng
                </Badge>
              </div>
            </div>

            {/* System Status Ribbon */}
            <div className="relative mt-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-primary/5 border border-primary/10">
              <span className="flex items-center gap-2.5 text-xs">
                <span className="h-6 w-6 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
                  <Zap className="h-3.5 w-3.5" />
                </span>
                <span>
                  <span className="font-semibold text-foreground">Hệ thống hội thoại sẵn sàng</span>
                  <span className="text-muted-foreground hidden sm:inline"> — VAD → Whisper → AI Router → VOICEVOX</span>
                </span>
              </span>
              <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                ⚡ Tương tác thời gian thực
              </span>
            </div>
          </div>

          {/* Persona Grid */}
          {loading ? (
            <div className="p-16 text-center text-sm text-muted-foreground flex flex-col items-center justify-center gap-3">
              <RefreshCw className="h-6 w-6 animate-spin text-primary" />
              <span>Đang tải danh sách đối tác hội thoại…</span>
            </div>
          ) : filteredPersonas.length === 0 ? (
            <div className="p-12 text-center rounded-2xl border border-dashed border-border bg-card/50 space-y-4 max-w-lg mx-auto">
              <div className="h-12 w-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto text-xl">
                👥
              </div>
              <div>
                <h3 className="text-base font-bold text-foreground">Chưa có đối tác hội thoại nào</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedDifficulty !== "All"
                    ? `Không tìm thấy đối tác nào ở trình độ ${selectedDifficulty}. Bạn có thể tạo mới hoặc khôi phục các mẫu có sẵn.`
                    : "Danh sách đối tác đang trống. Hãy tạo đối tác riêng hoặc khôi phục lại các đối tác mẫu mặc định."}
                </p>
              </div>
              <div className="flex items-center justify-center gap-2.5 flex-wrap pt-1">
                <Button variant="akane" size="sm" onClick={handleOpenCreateModal}>
                  <Plus className="h-4 w-4" /> Tạo đối tác mới
                </Button>
                <Button variant="outline" size="sm" onClick={handleGenerateAI} isLoading={generating}>
                  <Wand2 className="h-4 w-4 text-primary" /> Sinh bằng AI
                </Button>
                <Button variant="outline" size="sm" onClick={handleRestoreDefaults} isLoading={actionLoading}>
                  <RotateCcw className="h-3.5 w-3.5" /> Khôi phục mẫu
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredPersonas.map((persona) => (
                <Card
                  key={persona.id}
                  variant="washi"
                  hoverable
                  className="p-5 flex flex-col justify-between overflow-hidden group hover:shadow-washi transition-all duration-200"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-primary via-akane-600 to-indigo-600 flex items-center justify-center text-white font-extrabold text-lg shadow-md shrink-0">
                          {persona.name.charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-sm font-bold text-foreground block truncate">{persona.name}</span>
                            {persona.is_system && (
                              <Badge variant="fuji" size="sm" className="text-[10px] py-0 px-1.5 h-4">
                                <Lock className="h-2.5 w-2.5 mr-0.5" /> Mẫu
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-primary font-medium truncate block">{persona.role}</span>
                        </div>
                      </div>
                      <Badge variant="jlpt" size="sm" className="shrink-0">
                        {persona.difficulty}
                      </Badge>
                    </div>

                    <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">{persona.description}</p>

                    <div className="space-y-1.5 pt-3 border-t border-border text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-muted-foreground">Phong cách:</span>
                        <span className="text-foreground font-medium truncate max-w-[170px]">{persona.speaking_style}</span>
                      </div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-muted-foreground">Tính cách:</span>
                        <span className="text-foreground font-medium truncate max-w-[170px]">
                          {persona.personality}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 mt-4 border-t border-border flex items-center gap-2">
                    <Button
                      variant="akane"
                      size="md"
                      className="flex-1"
                      onClick={() => handleOpenLobby(persona)}
                    >
                      <Mic className="h-4 w-4" />
                      Bắt đầu hội thoại
                    </Button>

                    <Button
                      variant="ghost"
                      size="md"
                      className="px-2.5 text-destructive hover:bg-destructive/10 hover:text-destructive shrink-0"
                      title="Xóa đối tác này"
                      onClick={() => setDeleteTarget(persona)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create / AI Generate Persona Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Tạo đối tác hội thoại mới"
        description="Điền thông tin đối tác hoặc dùng AI để sinh tự động theo chủ đề bạn chọn."
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {/* AI Quick Generator Box */}
          <div className="p-3 rounded-xl bg-primary/5 border border-primary/15 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" /> AI Tạo đối tác nhanh
              </span>
              <Badge variant="sakura" size="sm">
                Tự động
              </Badge>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="VD: Chủ tiệm ramen Tokyo, Bạn cùng lớp anime, Bác sĩ…"
                value={aiThemeHint}
                onChange={(e) => setAiThemeHint(e.target.value)}
                className="flex-1 px-3 py-1.5 text-xs rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleGenerateAI();
                  }
                }}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerateAI}
                isLoading={generating}
                className="text-xs shrink-0"
              >
                <Wand2 className="h-3.5 w-3.5 text-primary mr-1" />
                Sinh AI
              </Button>
            </div>
          </div>

          {/* Form Fields */}
          <Input
            label="Tên đối tác (Kèm cách đọc)"
            placeholder="VD: Haruto (ハルト) hoặc Sakura (桜)"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <Input
            label="Vai trò / Nghề nghiệp"
            placeholder="VD: Chủ quán trà truyền thống ở Kyoto"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-foreground">Trình độ JLPT</label>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                className="h-9 bg-background border border-border rounded-lg px-3 text-sm text-foreground focus:outline-none focus:border-primary"
              >
                {["N5", "N4", "N3", "N2", "N1"].map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <Input
              label="Phong cách nói"
              placeholder="VD: Lịch sự keigo, Thân mật casual…"
              value={formData.speaking_style}
              onChange={(e) => setFormData({ ...formData, speaking_style: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">Mô tả bối cảnh & Tính cách</label>
            <textarea
              rows={2}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary resize-none"
              placeholder="VD: Thân thiện, chu đáo, thích kể chuyện văn hóa và ẩm thực Nhật Bản."
              value={formData.description}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  description: e.target.value,
                  personality: formData.personality || e.target.value,
                })
              }
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">System Prompt (Chỉ dẫn AI vai diễn)</label>
            <textarea
              rows={3}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary resize-none"
              placeholder="You are Haruto, a ramen chef in Tokyo. Speak naturally in Japanese suitable for JLPT learners in 1-3 sentences."
              value={formData.system_prompt || ""}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-border sticky bottom-0 bg-card">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCreateModalOpen(false)}
              disabled={actionLoading}
            >
              Hủy
            </Button>
            <Button
              variant="akane"
              size="sm"
              onClick={handleCreatePersona}
              isLoading={actionLoading}
              disabled={!formData.name.trim() || !formData.role.trim()}
            >
              <Plus className="h-4 w-4 mr-1" />
              Lưu đối tác
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Xóa đối tác hội thoại?"
        description={`Bạn có chắc chắn muốn xóa đối tác “${deleteTarget?.name || ""}”?`}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              Đối tác này và lịch sử các phiên luyện nói liên quan sẽ bị xóa hoàn toàn khỏi hệ thống. Hành động này không thể hoàn tác (nhưng bạn có thể khôi phục lại các đối tác mẫu bất cứ lúc nào).
            </span>
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteTarget(null)}
              disabled={actionLoading}
            >
              Hủy
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleConfirmDelete}
              isLoading={actionLoading}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Xác nhận xóa
            </Button>
          </div>
        </div>
      </Modal>

      {/* Speaking Room Session Lobby Modal */}
      {activePersona && (
        <Modal
          isOpen={isLobbyOpen}
          onClose={() => setIsLobbyOpen(false)}
          title={`Phòng chờ: ${activePersona.name}`}
          description="Thiết lập chế độ luyện tập và cấu hình âm thanh trước khi bắt đầu."
          className="max-w-2xl sm:max-w-3xl"
        >
          <SessionLobby
            persona={activePersona}
            volumeLevel={volumeLevel}
            isInitializing={isInitializing}
            onStartSession={handleStartFromLobby}
            onClose={() => setIsLobbyOpen(false)}
          />
        </Modal>
      )}

      {/* Permission Denied Modal */}
      <MicrophonePermissionModal
        isOpen={state === "permission_denied"}
        onClose={() => {}}
        onRetry={requestPermission}
      />

      {/* Session Summary Modal */}
      {summary !== null && state === "ended" && (
        <div className="space-y-3">
          <SpeakingPostSessionCoachCard sessionId={session?.id || summary.session_id || undefined} />
        </div>
      )}
      <SessionSummaryModal
        isOpen={isSummaryOpen}
        summary={summary}
        onClose={handleCloseSummary}
        onReplayVoice={replayVoice}
      />

      {/* Coach Panel */}
      <CoachPanel
        open={coachOpen}
        onClose={() => setCoachOpen(false)}
        route={pathname || "/speaking"}
        sessionId={session?.id}
      />

      {/* Quick In-session Coach Button */}
      {isSessionActive && (
        <button
          onClick={() => setCoachOpen(true)}
          className="fixed bottom-24 right-4 z-30 md:bottom-6 px-3 py-2 rounded-xl bg-card border border-border shadow-lg text-xs font-bold flex items-center gap-1.5"
        >
          <span className="h-6 w-6 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">🤖</span>
          Hỏi Coach
        </button>
      )}
    </div>
  );
}
