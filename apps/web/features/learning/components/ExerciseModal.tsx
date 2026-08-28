"use client";

import React, { useState } from "react";
import {
  X,
  Sparkles,
  Target,
  Lightbulb,
  Mic,
  Send,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  RotateCw,
  Clock,
  Zap,
} from "lucide-react";
import { Exercise, ExerciseResult } from "@/types/learning";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ExerciseModalProps {
  isOpen: boolean;
  onClose: () => void;
  exercise: Exercise | null;
  result: ExerciseResult | null;
  loading: boolean;
  submitting: boolean;
  showHint: boolean;
  onRevealHint: () => void;
  onSubmitTranscript: (transcript: string) => void;
  onNextExercise?: () => void;
}

export const ExerciseModal: React.FC<ExerciseModalProps> = ({
  isOpen,
  onClose,
  exercise,
  result,
  loading,
  submitting,
  showHint,
  onRevealHint,
  onSubmitTranscript,
  onNextExercise,
}) => {
  const [transcript, setTranscript] = useState<string>("");
  const [isRecording, setIsRecording] = useState<boolean>(false);

  if (!isOpen || !exercise) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!transcript.trim()) return;
    onSubmitTranscript(transcript.trim());
  };

  const handleSimulatedSpeech = () => {
    // Quick starter snippet based on target patterns
    if (exercise.target_patterns && exercise.target_patterns.length > 0) {
      const pat = exercise.target_patterns[0];
      setTranscript(`実は、行きたくない${pat}ですが、時間がありません。`);
    } else {
      setTranscript("はい、わかりました。よろしくお願いいたします。");
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="">
      <div className="p-6 space-y-6 max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs uppercase bg-indigo-950/60 border-indigo-700 text-indigo-300">
                {exercise.exercise_type.replace("_", " ")}
              </Badge>
              <Badge variant="outline" className="text-xs capitalize bg-card border-border text-foreground">
                {exercise.difficulty}
              </Badge>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" /> {exercise.estimated_minutes} min
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">{exercise.title}</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        {!result ? (
          <div className="space-y-5">
            {/* Objective & Target Patterns */}
            <div className="p-4 rounded-xl bg-background/80 border border-border space-y-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-indigo-400" /> Mục tiêu bài tập:
                </span>
                <p className="text-sm font-medium text-foreground mt-1">{exercise.objective}</p>
              </div>

              {exercise.target_patterns && exercise.target_patterns.length > 0 && (
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400/90 block mb-1.5">
                    Mẫu cấu trúc / Từ vựng trọng tâm:
                  </span>
                  <div className="flex gap-2 flex-wrap">
                    {exercise.target_patterns.map((pat, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 bg-amber-950/40 border border-amber-500/30 text-amber-300 rounded-md font-mono text-xs font-semibold"
                      >
                        {pat}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Scenario & Instructions */}
            {exercise.scenario && (
              <div className="p-3.5 rounded-xl bg-card/60 border border-border/80 text-xs text-foreground space-y-1">
                <span className="font-semibold text-foreground block text-xs">🎭 Bối cảnh tình huống:</span>
                <p className="leading-relaxed">{exercise.scenario}</p>
              </div>
            )}

            <div className="p-3.5 rounded-xl bg-card/40 border border-border text-xs text-foreground space-y-1">
              <span className="font-semibold text-foreground block text-xs">📝 Hướng dẫn thực hiện:</span>
              <p className="leading-relaxed">{exercise.instructions}</p>
            </div>

            {/* Scaffolding Hint */}
            {exercise.scaffold_hint && (
              <div className="pt-1">
                {showHint ? (
                  <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-200 space-y-1 animate-in fade-in">
                    <span className="font-bold flex items-center gap-1 text-amber-300">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400" /> Gợi ý mẫu câu:
                    </span>
                    <p>{exercise.scaffold_hint}</p>
                  </div>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={onRevealHint}
                    className="text-xs border-dashed border-border text-muted-foreground hover:text-amber-300 hover:border-amber-500/50 flex items-center gap-1.5"
                  >
                    <Lightbulb className="w-3.5 h-3.5" /> Xem gợi ý hỗ trợ (Scaffolding Hint)
                  </Button>
                )}
              </div>
            )}

            {/* Speech Input Form */}
            <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-border">
              <div>
                <label className="text-xs font-semibold text-foreground block mb-1.5 flex items-center justify-between">
                  <span>Câu nói tiếng Nhật của bạn:</span>
                  <button
                    type="button"
                    onClick={handleSimulatedSpeech}
                    className="text-[11px] text-indigo-400 hover:underline flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" /> Mẫu câu thử nghiệm
                  </button>
                </label>
                <textarea
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Nói hoặc nhập câu trả lời tiếng Nhật của bạn tại đây..."
                  rows={3}
                  className="w-full bg-background border border-border rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              <div className="flex items-center justify-between gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsRecording(!isRecording)}
                  className={`text-xs flex items-center gap-1.5 ${
                    isRecording ? "bg-rose-950 border-rose-500 text-rose-300 animate-pulse" : "border-border text-foreground"
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" /> {isRecording ? "Đang ghi âm..." : "Ghi âm giọng nói"}
                </Button>

                <Button
                  type="submit"
                  disabled={!transcript.trim() || submitting}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-5 py-2 h-auto flex items-center gap-1.5 shadow-lg shadow-indigo-600/30"
                >
                  {submitting ? (
                    <>
                      <RotateCw className="w-3.5 h-3.5 animate-spin" /> Đang đánh giá...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" /> Nộp bài đánh giá
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        ) : (
          /* Result Assessment Card */
          <div className="space-y-5 animate-in fade-in zoom-in-95">
            <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-border text-center space-y-3">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-card border-2 border-indigo-500/40 text-2xl font-black text-white shadow-xl shadow-indigo-500/10">
                {Math.round(result.score)}
              </div>

              <div>
                <h3 className="text-lg font-bold text-white flex items-center justify-center gap-2">
                  {result.success ? (
                    <span className="text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-5 h-5" /> Hoàn thành xuất sắc!
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1.5">
                      <AlertCircle className="w-5 h-5" /> Cần tiếp tục rèn luyện
                    </span>
                  )}
                </h3>
                <p className="text-xs text-muted-foreground mt-1 capitalize">
                  Mức độ độc lập: <span className="font-semibold text-foreground">{result.independence.replace("_", " ")}</span>
                </p>
              </div>

              {/* Mastery Delta Pill */}
              {Object.keys(result.target_mastery_delta || {}).length > 0 && (
                <div className="pt-2 flex justify-center">
                  {Object.entries(result.target_mastery_delta).map(([k, d]) => (
                    <div
                      key={k}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-semibold"
                    >
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                      {k}: <span className="text-emerald-200">{d >= 0 ? `+${d}` : d} Mastery</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Pedagogical Feedback */}
            <div className="p-4 rounded-xl bg-background/80 border border-border space-y-2">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Nhận xét từ AI Coach:
              </span>
              <p className="text-xs text-foreground leading-relaxed pl-5">{result.feedback}</p>

              {result.evidence && result.evidence.length > 0 && (
                <div className="mt-2 pt-2 border-t border-border text-[11px] text-muted-foreground space-y-1">
                  <span className="font-semibold text-muted-foreground block">Dẫn chứng cụ thể:</span>
                  {result.evidence.map((ev, i) => (
                    <p key={i} className="pl-3 border-l-2 border-border italic">
                      "{ev}"
                    </p>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button variant="outline" size="sm" onClick={onClose} className="text-xs border-border text-foreground">
                Đóng
              </Button>
              {onNextExercise && (
                <Button
                  size="sm"
                  onClick={onNextExercise}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 h-auto"
                >
                  Bài tiếp theo →
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
