"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { Mic, Clock, Play, Square, Trophy, Settings2, Zap, BookOpen, BarChart3, Lightbulb, AlertCircle, Sparkles, HelpCircle, Keyboard, Send, FileText } from "lucide-react";
import { useMonologue } from "@/hooks/use-monologue";
import { useAudioRecorder } from "@/features/audio/hooks/useAudioRecorder";
import { toast } from "@/lib/toast";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";

const DURATIONS = [30,45,60,90,120,180,300];
const PREP_OPTIONS = [0,15,30,60];
const SUPPORT_LABEL: Record<number,string> = {0:"Blind",1:"Keywords",2:"Guided Qs",3:"Structure",4:"Minimal"};

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject)=>{
    const reader = new FileReader();
    reader.onload = ()=>{
      const res = reader.result as string;
      // data:audio/webm;base64,xxxx
      const idx = res.indexOf(",");
      resolve(idx>=0? res.slice(idx+1) : res);
    };
    reader.onerror = ()=>reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

export default function SpeechPage() {
  const mono = useMonologue();
  const recorder = useAudioRecorder();
  const { matchesAction, keybindings } = useSystemKeybindings();
  const [durationSec, setDurationSec] = useState(60);
  const [prepSec, setPrepSec] = useState(30);
  const [genre, setGenre] = useState<string>("");
  const [supportLevel, setSupportLevel] = useState<number | undefined>(undefined);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showHint, setShowHint] = useState(false);
  const [usedHint, setUsedHint] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const startedAtRef = useRef<number | null>(null);
  const [prepLeft, setPrepLeft] = useState(0);
  const [recLeft, setRecLeft] = useState(0);
  const [recElapsed, setRecElapsed] = useState(0);
  const rafRef = useRef<number | null>(null);
  const recRafRef = useRef<number | null>(null);
  const phaseRef = useRef(mono.phase);
  const lastPrepTickRef = useRef(0);
  const lastRecTickRef = useRef(0);

  const speechConfig = (mono.exercise?.extra_metadata as any)?.speech_config;

  // keep phaseRef in sync
  useEffect(()=>{ phaseRef.current = mono.phase; }, [mono.phase]);

  // surface backend/recorder errors via global toast (single source)
  useEffect(()=>{
    if (mono.error) toast.error(mono.error);
  }, [mono.error]);
  useEffect(()=>{
    if (recorder.error) toast.error(recorder.error);
  }, [recorder.error]);

  const startPrepCountdown = useCallback((sec: number) => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setPrepLeft(sec);
    if (sec<=0) { mono.setPhase("ready"); return; }
    const t0 = performance.now();
    lastPrepTickRef.current = 0;
    const tick = (now:number) => {
      if (phaseRef.current!=="preparing") return;
      // throttle to 100ms
      if (now - lastPrepTickRef.current < 100) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      lastPrepTickRef.current = now;
      const elapsed = (now - t0)/1000;
      const left = Math.max(0, sec - elapsed);
      setPrepLeft(left);
      if (left>0 && phaseRef.current==="preparing") {
        // handle visibility throttling: if hidden, use setTimeout
        if (document.hidden) {
          setTimeout(()=> { rafRef.current = requestAnimationFrame(tick); }, 200);
        } else {
          rafRef.current = requestAnimationFrame(tick);
        }
      } else if (phaseRef.current==="preparing") {
        mono.setPhase("ready");
      }
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  useEffect(()=>{
    if (mono.phase==="preparing" && speechConfig) {
      const p = speechConfig.prep_duration_sec ?? prepSec;
      startPrepCountdown(p);
    }
    return ()=>{ if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [mono.phase, speechConfig, prepSec, startPrepCountdown]);

  useEffect(()=>{
    return ()=>{
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
      recorder.releaseMicrophone();
    };
  },[]);

  // Release microphone whenever phase is idle or result
  useEffect(() => {
    if (mono.phase === "idle" || mono.phase === "result") {
      recorder.releaseMicrophone();
    }
  }, [mono.phase]);

  const handleGenerate = async () => {
    try {
      setTranscriptInput(""); setShowHint(false); setUsedHint(false); setRecElapsed(0); setRecLeft(0);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
      await mono.generate({ duration_sec: durationSec, prep_sec: prepSec, genre: genre||undefined, support_level: supportLevel });
    } catch (e:any) {
      toast.error(e.message || "Topic generation failed (AI down) — please retry");
    }
  };

  const startRecording = async () => {
    try {
      const ok = await recorder.requestPermission();
      if (!ok) { toast.error(recorder.error || "Microphone permission denied"); return; }
      await recorder.startRecording();
      mono.setPhase("recording");
      const t0 = performance.now();
      startedAtRef.current = t0;
      setRecLeft(durationSec);
      lastRecTickRef.current = 0;
      if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
      const tick = (now:number) => {
        if (phaseRef.current!=="recording") return;
        if (now - lastRecTickRef.current < 100) {
          recRafRef.current = requestAnimationFrame(tick);
          return;
        }
        lastRecTickRef.current = now;
        const elapsed = (now - t0)/1000;
        setRecElapsed(elapsed);
        setRecLeft(Math.max(0, durationSec - elapsed));
        if (elapsed >= durationSec) {
          handleStopRecording();
          return;
        }
        if (phaseRef.current==="recording") {
          if (document.hidden) {
            setTimeout(()=>{ recRafRef.current = requestAnimationFrame(tick); }, 200);
          } else {
            recRafRef.current = requestAnimationFrame(tick);
          }
        }
      };
      recRafRef.current = requestAnimationFrame(tick);
    } catch (e:any) {
      toast.error(e.message || "Failed to start recording");
    }
  };

  const handleStopRecording = async () => {
    if (recRafRef.current) { cancelAnimationFrame(recRafRef.current); recRafRef.current=null; }
    try {
      const blob = await recorder.stopRecording();
      const endedAt = performance.now();
      if (!blob || blob.size < 500) {
        toast.error("Audio too short or empty — please record again (audio is required)");
        mono.setPhase("ready");
        return;
      }
      if (blob.size > 10*1024*1024) {
        toast.error("Audio too large (>10MB) — please try shorter duration");
        mono.setPhase("ready");
        return;
      }
      const durationMs = startedAtRef.current ? Math.round(endedAt - startedAtRef.current) : Math.round(recElapsed*1000);
      // Prefer multipart (keep both per user choice) to avoid 33% base64 overhead
      const basePayload = {
        user_transcript: transcriptInput.trim() || undefined,
        speech_metrics: {
          started_at: startedAtRef.current ? new Date(Date.now() - durationMs).toISOString() : new Date().toISOString(),
          ended_at: new Date().toISOString(),
          target_duration_ms: durationSec*1000,
          speech_duration_ms: durationMs,
        },
        used_hint: usedHint,
      };
      // Use multipart for audio (efficient), fallback to base64 JSON if multipart fails
      try {
        await (mono as any).submitMultipart(blob, basePayload);
      } catch (multipartErr:any) {
        // fallback to base64 JSON (keep both)
        try {
          const b64 = await blobToBase64(blob);
          await mono.submit({ ...basePayload, audio_base64: b64 } as any);
        } catch {
          throw multipartErr;
        }
      }
      toast.info("Submitted — analyzing…");
    } catch (e:any) {
      toast.error(e.message || "Submit failed");
    }
  };

  const handleDirectTextSubmit = async () => {
    const text = transcriptInput.trim();
    if (!text) {
      toast.error("Vui lòng nhập nội dung bài nói tiếng Nhật của bạn.");
      return;
    }
    if (text.length < 15) {
      toast.error("Bài nói cần tối thiểu 15 ký tự tiếng Nhật để AI phân tích cấu trúc và lập luận.");
      return;
    }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
    recorder.releaseMicrophone();

    const targetSec = speechConfig?.target_duration_sec ?? durationSec;
    const estimatedDurationMs = Math.max(8000, Math.min(targetSec * 1000, Math.round((text.length / 5.0) * 1000)));

    const basePayload = {
      user_transcript: text,
      speech_metrics: {
        started_at: new Date(Date.now() - estimatedDurationMs).toISOString(),
        ended_at: new Date().toISOString(),
        target_duration_ms: targetSec * 1000,
        speech_duration_ms: estimatedDurationMs,
      },
      used_hint: usedHint,
    };

    try {
      toast.info("Đang nộp bài nói văn bản để AI phân tích...");
      await mono.submit(basePayload);
    } catch (e: any) {
      toast.error(e.message || "Chấm điểm bài nói thất bại.");
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input" || tag === "select") {
        return;
      }

      if (matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowHelp((v) => !v);
        return;
      }

      // Space / Mic: Start recording if ready, stop recording if recording
      if (matchesAction(e, "speakingMic") || matchesAction(e, "drillReplayAudio")) {
        e.preventDefault();
        if (mono.phase === "ready") {
          startRecording();
        } else if (mono.phase === "recording") {
          handleStopRecording();
        }
        return;
      }

      // Enter: Start or submit or next
      if (matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (mono.phase === "idle" || !mono.exercise) {
          handleGenerate();
        } else if (mono.phase === "preparing") {
          mono.setPhase("ready");
        } else if (mono.phase === "result") {
          handleGenerate();
        }
        return;
      }

      // Retry
      if (matchesAction(e, "drillRetry") && mono.phase === "result") {
        e.preventDefault();
        mono.setPhase("ready");
        return;
      }

      if (e.key === "Escape") {
        if (mono.phase !== "idle") {
          mono.setPhase("idle" as any);
        } else {
          setShowHelp(false);
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mono.phase, mono.exercise, matchesAction]);

  const phase = mono.phase;
  const result = mono.result;

  if (phase==="idle" || !mono.exercise) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in">
        
        <div className="relative overflow-hidden rounded-[24px] border bg-card p-6">
          <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-enso-gradient opacity-30" />
          <div className="relative flex items-center gap-3">
            <span className="h-9 w-9 rounded-xl bg-primary/10 border flex items-center justify-center text-primary"><Mic className="h-5 w-5"/></span>
            <div>
              <h1 className="text-xl font-black">1分間スピーチ <span className="text-sm font-normal text-muted-foreground">Monologue Lab — Mode 5</span></h1>
              <p className="text-sm text-muted-foreground">Sustain thought, structure ideas, speak continuously — AI generates fresh topic/genre/constraint each time</p>
            </div>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">No hard-coded DB • Preparation 0-4 • Durations 30-300s • Deterministic pause/filler → AI semantic • Genre-specific scoring • Audio required (no transcript-only)</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <Card className="lg:col-span-2 p-5 space-y-4">
            <div className="flex items-center gap-2"><Badge variant="sakura">Generate</Badge><span className="text-xs text-muted-foreground">AI + VarietyPolicy (SHA256) + Validator — hard error if AI down</span></div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-bold mb-1">Duration</div>
                <div className="flex flex-wrap gap-1.5">
                  {DURATIONS.map(d=>(
                    <button key={d} onClick={()=>setDurationSec(d)} className={`px-2.5 py-1 rounded-full text-xs font-bold border ${durationSec===d?"bg-primary text-primary-foreground border-primary":"bg-muted border-border"}`}>{d}s</button>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs font-bold mb-1">Prep</div>
                <div className="flex flex-wrap gap-1.5">
                  {PREP_OPTIONS.map(p=>(
                    <button key={p} onClick={()=>setPrepSec(p)} className={`px-2.5 py-1 rounded-full text-xs font-bold border ${prepSec===p?"bg-primary text-primary-foreground border-primary":"bg-muted border-border"}`}>{p}s</button>
                  ))}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-bold mb-1">Genre (optional)</div>
                <select value={genre} onChange={e=>setGenre(e.target.value)} className="w-full rounded-lg border bg-background px-2 py-1.5 text-sm">
                  <option value="">Auto (adaptive)</option>
                  {["personal","story","opinion","explanation","comparison","argument","problem_solution","reflection","summary","report","interview","business_update","presentation","persuasion","critique","prediction"].map(g=>(
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <div>
                <div className="text-xs font-bold mb-1">Support (optional)</div>
                <select value={supportLevel ?? ""} onChange={e=>setSupportLevel(e.target.value===""?undefined:parseInt(e.target.value))} className="w-full rounded-lg border bg-background px-2 py-1.5 text-sm">
                  <option value="">Auto</option>
                  {[0,1,2,3,4].map(l=>(
                    <option key={l} value={l}>{l} - {SUPPORT_LABEL[l]}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="text-[11px] text-muted-foreground">Prep levels: 0 Blind → 1 Keywords → 2 Guided Qs → 3 Structure → 4 Minimal. Adaptive reduces scaffolding as mastery ↑.</div>
            {mono.loading ? (
              <ZenLoadingState
                variant="ai"
                title="AI Đang Thiết Lập Đề Bài & Dàn Ý Phát Biểu..."
                ja="スピーチ課題生成中..."
                description="Đang sinh chủ đề độc quyền, thể loại lập luận và các ràng buộc phản xạ..."
              />
            ) : (
              <Button variant="akane" size="lg" className="w-full font-bold gap-2" onClick={handleGenerate}>
                <Zap className="h-4 w-4" />
                <span>Sinh Đề Bài Phát Biểu Mới (AI Dynamic)</span>
              </Button>
            )}
            {mono.error && <div className="text-xs text-red-600 border border-red-200 bg-red-50 rounded-lg p-3 flex items-center gap-2"><AlertCircle className="h-4 w-4 shrink-0"/>{mono.error}</div>}
          </Card>
          <div className="space-y-4">
            <Card className="p-4">
              <div className="text-sm font-bold flex items-center gap-1.5"><BookOpen className="h-4 w-4"/> How it works</div>
              <ol className="mt-2 text-xs text-muted-foreground space-y-1 list-decimal list-inside">
                <li>Learning Engine picks target → AI generates genre/topic/constraint (VI+JP hybrid) — <b>no fallback</b>, AI down → 503 + Retry</li>
                <li>Prep → Ready → Record continuously (no interruption, audio required)</li>
                <li>STT authoritative (Faster-Whisper) → deterministic metrics (no mock 78)</li>
                <li>AI semantic + native upgrade → genre-specific scoring</li>
              </ol>
            </Card>
            <Card className="p-4 bg-amber-500/5 dark:bg-amber-500/10 border-amber-500/20 dark:border-amber-500/30 space-y-1">
              <div className="text-xs font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                <span>Deterministic authority</span>
              </div>
              <div className="text-xs text-foreground/85 dark:text-foreground/85 leading-relaxed font-medium">
                pause/filler/mora from code, AI only interprets. No mock scores — missing signal → Low confidence.
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in">
      
      <div className="flex items-center justify-between">
        <Badge variant="sakura">{speechConfig?.genre ?? mono.exercise.exercise_type} • {speechConfig?.target_duration_sec ?? durationSec}s • Prep {speechConfig?.prep_duration_sec ?? prepSec}s • Lvl {speechConfig?.support_level} {SUPPORT_LABEL[speechConfig?.support_level ?? 0]}</Badge>
        <Button variant="ghost" size="sm" onClick={()=>{
          if (rafRef.current) cancelAnimationFrame(rafRef.current);
          if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
          recorder.releaseMicrophone();
          mono.reset();
        }}>Exit</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          <Card className="p-4 space-y-3">
            <div className="text-xs font-bold text-muted-foreground">Topic (VI+JP hybrid)</div>
            <div className="text-lg font-black">{speechConfig?.topic || mono.exercise.title}</div>
            <div className="text-sm text-foreground border-l-2 border-primary pl-3 py-1 bg-primary/5 rounded-r">指示: {speechConfig?.instruction || mono.exercise.instructions}</div>
            <div className="flex flex-wrap gap-1.5">
              {(speechConfig?.constraints || mono.exercise.constraints || []).map((c:string)=>(
                <Badge key={c} variant="jlpt" size="sm">{c}</Badge>
              ))}
            </div>
            {(speechConfig?.support?.keywords?.length>0 || speechConfig?.support?.guided_questions?.length>0 || speechConfig?.support?.outline?.length>0) && (
              <div className="pt-2 border-t">
                {!showHint ? (
                  <Button variant="outline" size="sm" onClick={()=>{setShowHint(true); setUsedHint(true);}}>Show hint (counts as assisted)</Button>
                ) : (
                  <div className="space-y-1 text-sm">
                    {speechConfig.support.keywords?.length>0 && <div><span className="font-bold">Keywords:</span> {speechConfig.support.keywords.join(" • ")}</div>}
                    {speechConfig.support.guided_questions?.length>0 && <div><span className="font-bold">Guided:</span> {speechConfig.support.guided_questions.join(" | ")}</div>}
                    {speechConfig.support.outline?.length>0 && <div><span className="font-bold">Outline:</span> {speechConfig.support.outline.join(" → ")}</div>}
                  </div>
                )}
              </div>
            )}
          </Card>

          {phase==="preparing" && (
            <Card className="p-6 text-center space-y-3">
              <div className="text-sm font-bold flex items-center justify-center gap-2"><Clock className="h-4 w-4"/> Preparing</div>
              <div className="text-4xl font-black tabular-nums">{prepLeft.toFixed(1)}s</div>
              <div className="h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-primary transition-all" style={{width:`${Math.max(0, (1 - prepLeft/(speechConfig?.prep_duration_sec||prepSec))*100)}%`}}/></div>
              <div className="text-xs text-muted-foreground">Throttled 100ms + visibility handling. Organize: {speechConfig?.outline_hint?.join(" → ") || "Position → Reason → Example → Conclusion"}</div>
              <Button variant="akane" size="sm" onClick={()=>{
                if (rafRef.current) cancelAnimationFrame(rafRef.current);
                mono.setPhase("ready");
              }}>Skip to Ready</Button>
            </Card>
          )}
          {phase==="ready" && (
            <Card className="p-6 space-y-4">
              <div className="text-center space-y-1">
                <div className="text-base font-bold text-foreground">Sẵn sàng phát biểu — Mục tiêu: {speechConfig?.target_duration_sec ?? durationSec} giây</div>
                <div className="text-xs text-muted-foreground">Chọn thu âm qua micro hoặc soạn bài nói trực tiếp nếu đang ở văn phòng / hỏng mic.</div>
              </div>

              {/* Action Choices */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {/* Option 1: Mic Recording */}
                <div className="p-4 rounded-2xl border border-primary/30 bg-primary/5 washi-texture flex flex-col justify-between space-y-3 text-center">
                  <div className="space-y-1">
                    <div className="font-extrabold text-sm flex items-center justify-center gap-1.5 text-primary">
                      <Mic className="h-4 w-4" />
                      <span>Thu Âm Bằng Micro</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Bật micro và nói tự do liên tục theo dàn ý gợi ý</p>
                  </div>
                  <Button variant="akane" onClick={startRecording} className="w-full font-bold gap-1.5 shadow-xs">
                    <Mic className="h-4 w-4" />
                    <span>Bắt đầu thu âm ({speechConfig?.target_duration_sec ?? durationSec}s)</span>
                  </Button>
                </div>

                {/* Option 2: Direct Text / Office Mode */}
                <div className="p-4 rounded-2xl border border-border bg-card washi-texture flex flex-col justify-between space-y-3">
                  <div className="space-y-1">
                    <div className="font-extrabold text-sm flex items-center gap-1.5 text-foreground">
                      <Keyboard className="h-4 w-4 text-emerald-500" />
                      <span>Soạn Bài Nói (Chế Độ Văn Phòng)</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Gõ bài phát biểu tiếng Nhật của bạn vào ô bên dưới</p>
                  </div>
                  <div className="text-[11px] font-mono text-muted-foreground">
                    {transcriptInput.trim().length} chữ ~ {Math.round(transcriptInput.trim().length / 5.0)}s
                  </div>
                </div>
              </div>

              {/* Full Text Input Editor Box */}
              <div className="p-4 rounded-2xl border border-border bg-muted/20 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="flex items-center gap-1 text-foreground">
                    <FileText className="h-3.5 w-3.5 text-primary" />
                    <span>Nội dung bài nói tiếng Nhật:</span>
                  </span>
                  <span className="text-[11px] font-normal text-muted-foreground">
                    Tối thiểu 15 chữ
                  </span>
                </div>
                <textarea
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  placeholder="Gõ bài phát biểu tiếng Nhật của bạn tại đây... (Ví dụ: 私の意見としては、テレワークには多くのメリットがあると思います。なぜなら通勤時間がなくなり、効率的に仕事ができるからです。)"
                  rows={4}
                  className="w-full rounded-xl border bg-background p-3 text-sm font-jp leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] text-muted-foreground">
                    🏢 Không cần mic — AI chấm đầy đủ cấu trúc & từ vựng
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="akane"
                      size="sm"
                      onClick={handleDirectTextSubmit}
                      disabled={transcriptInput.trim().length < 15}
                      className="font-bold gap-1.5 shadow-xs"
                    >
                      <Send className="h-3.5 w-3.5" />
                      <span>Nộp bài viết</span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (rafRef.current) cancelAnimationFrame(rafRef.current);
                        recorder.releaseMicrophone();
                        mono.reset();
                      }}
                    >
                      Hủy
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )}
          {phase==="recording" && (
            <Card className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500 animate-pulse"/> Đang thu âm bài nói liên tục</span>
                <span className="text-sm font-mono font-bold tabular-nums">{Math.floor(recElapsed)}s / {durationSec}s (còn {recLeft.toFixed(1)}s)</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-red-500 transition-all" style={{width:`${Math.min(100, recElapsed/durationSec*100)}%`}}/></div>
              <div className="flex items-center gap-2">
                <div className="h-8 flex-1 rounded bg-muted overflow-hidden flex items-end gap-px p-1">
                  <div className="flex-1 bg-primary" style={{height:`${Math.round(recorder.volumeLevel*100)}%`}}/>
                </div>
                <span className="text-xs text-muted-foreground">{Math.round(recorder.volumeLevel*100)}%</span>
              </div>
              <div className="flex gap-2">
                <Button variant="akane" onClick={handleStopRecording}><Square className="h-4 w-4"/> Dừng & Nộp bài ghi âm</Button>
                <Button variant="ghost" size="sm" onClick={async()=>{
                  if (recRafRef.current) { cancelAnimationFrame(recRafRef.current); recRafRef.current=null; }
                  await recorder.stopRecording();
                  recorder.releaseMicrophone();
                  mono.setPhase("ready");
                }}>Hủy thu âm</Button>
              </div>
              <div className="pt-3 border-t space-y-2">
                <div className="text-xs font-bold">Hoặc gõ văn bản bài nói (Chế độ Văn phòng):</div>
                <textarea
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  placeholder="Gõ bài nói của bạn tại đây nếu không thể nói to..."
                  className="w-full rounded-xl border bg-background p-2.5 text-sm font-jp min-h-[72px]"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDirectTextSubmit}
                  disabled={!transcriptInput.trim()}
                  className="font-bold text-xs gap-1.5"
                >
                  <Send className="h-3 w-3" />
                  <span>Nộp bài gõ</span>
                </Button>
              </div>
            </Card>
          )}
          {phase==="processing" && (
            <ZenLoadingState
              variant="ai"
              title="AI Đang Phân Tích Bài Nói & Nâng Cấp Tự Nhiên..."
              ja="スピーチ評価・AI添削中..."
              description="Đang xử lý nhận diện giọng nói (STT), phân tích tính lưu loát, cấu trúc luận điểm và đề xuất nâng cấp câu văn chuẩn bản xứ..."
            />
          )}
          {phase==="retry" && (
            <Card className="p-6 text-center space-y-2 border-amber-500/30 bg-amber-500/10 dark:bg-amber-950/25">
              <div className="text-sm font-bold text-amber-700 dark:text-amber-300 flex items-center justify-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400"/> Audio quality low — RETRY_AUDIO
              </div>
              <div className="text-xs text-foreground/80 dark:text-foreground/80 font-medium">{mono.result?.feedback || mono.error || "Please retry in quieter environment"}</div>
              <Button variant="akane" size="sm" onClick={()=>{
                if (rafRef.current) cancelAnimationFrame(rafRef.current);
                if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
                mono.setPhase("ready");
              }}>Retry Recording</Button>
            </Card>
          )}
          {phase==="result" && result && (
            <Card className="p-4 space-y-4">
              <div className="flex items-center gap-2"><Trophy className="h-4 w-4 text-amber-600"/> <span className="font-black">Result — Overall {result.score ?? result.assessment?.overall}</span><Badge variant={result.success?"kintsugi":"jlpt"}>{result.success?"Success":"Needs work"}</Badge><span className="ml-auto text-xs text-muted-foreground">conf {(result.confidence ?? result.assessment?.confidence ?? 0).toFixed(2)} {result.assessment?.ai_error? "• AI unavailable":""}</span></div>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[
                  ["Fluency", result.assessment?.fluency],
                  ["Coherence", result.assessment?.coherence],
                  ["Grammar", result.assessment?.grammar],
                  ["Vocab", result.assessment?.vocabulary],
                  ["Natural", result.assessment?.naturalness],
                  ["Relevance", result.assessment?.relevance],
                  ["Discourse", result.assessment?.discourse],
                  ["Pronunc.", result.assessment?.pronunciation],
                ].map(([k,v])=>(
                  <div key={k as string} className="rounded-xl border bg-muted/40 p-2">
                    <div className="text-[11px] font-bold text-muted-foreground">{k}</div>
                    <div className={`text-lg font-black ${v==null?"text-muted-foreground text-sm":""}`}>{v ?? "—"}</div>
                  </div>
                ))}
              </div>
              {result.assessment?.ai_error && <div className="text-xs text-amber-700 dark:text-amber-300 border border-amber-500/30 bg-amber-500/10 dark:bg-amber-950/30 rounded-lg p-2.5 font-medium">AI unavailable: {result.assessment.ai_error} — showing deterministic only (Low confidence)</div>}
              <div className="text-sm border-l-2 border-primary pl-3 bg-primary/5 rounded-r p-2">Feedback: {result.feedback}</div>
              {result.evidence?.length>0 && <div className="text-xs text-muted-foreground">Evidence: {result.evidence.join(" • ")}</div>}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="rounded-lg border p-2"><div className="font-bold">Duration</div><div>{((result.metrics?.speech_duration_ms ?? result.metrics?.speech_metrics_core?.speech_duration_ms ?? 0)/1000).toFixed(1)}s / {(speechConfig?.target_duration_sec ?? durationSec)}s</div></div>
                <div className="rounded-lg border p-2"><div className="font-bold">Rate</div><div>{result.metrics?.speech_metrics_core?.chars_per_min ?? result.metrics?.chars_per_min ?? "—"} chars/min {result.metrics?.speech_metrics_core?.mora_per_sec ? `${result.metrics.speech_metrics_core.mora_per_sec} mora/sec` : ""}</div></div>
                <div className="rounded-lg border p-2"><div className="font-bold">Fillers</div><div>{result.metrics?.filler_summary?.filler_count ?? result.metrics?.speech_metrics_core?.filler_count ?? 0} ({result.metrics?.filler_summary?.filler_per_min ?? 0}/min)</div></div>
                <div className="rounded-lg border p-2"><div className="font-bold">Pauses</div><div>{result.metrics?.pause_summary?.total ?? 0} (long {result.metrics?.pause_summary?.long ?? 0} stall {result.metrics?.pause_summary?.stall ?? 0})</div></div>
                <div className="rounded-lg border p-2"><div className="font-bold">Self-repair</div><div>{result.metrics?.repair_summary?.repair_count ?? 0} abandoned {result.metrics?.repair_summary?.abandoned_count ?? 0}</div></div>
                <div className="rounded-lg border p-2"><div className="font-bold">Ideas</div><div>{result.metrics?.idea_density?.unique_ideas ?? 0} ideas, {result.metrics?.idea_density?.examples ?? 0} examples</div></div>
              </div>
              {result.metrics?.fluency_timeline?.length>0 && (
                <div className="space-y-1">
                  <div className="text-xs font-bold flex items-center gap-1"><BarChart3 className="h-3.5 w-3.5"/> Fluency Timeline</div>
                  <div className="text-xs font-mono space-y-0.5 bg-muted/40 rounded-lg p-2">
                    {result.metrics.fluency_timeline.map((t:any,i:number)=>(
                      <div key={i}>{t.display} — pauses:{t.pauses} fillers:{t.fillers}</div>
                    ))}
                  </div>
                </div>
              )}
              {result.metrics?.filler_timeline?.length>0 && (
                <div className="space-y-1">
                  <div className="text-xs font-bold">Filler Timeline</div>
                  <div className="flex flex-wrap gap-1">
                    {result.metrics.filler_timeline.map((f:any,i:number)=>(
                      <Badge key={i} variant="jlpt" size="sm">{(f.at_ms/1000).toFixed(1)}s {f.token}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {result.metrics?.discourse && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg border p-2">
                    <div className="font-bold">Discourse Map</div>
                    <div className="mt-1 font-mono">{result.metrics.discourse.detected_structure?.join(" → ") || "—"}</div>
                    <div className="text-muted-foreground">Missing: {result.metrics.discourse.missing_elements?.join(", ")||"none"} • Connectors: {JSON.stringify(result.metrics.discourse.connector_counts)}</div>
                  </div>
                  <div className="rounded-lg border p-2">
                    <div className="font-bold">Lexical Profile {result.metrics.lexical_profile?.provider_available===false?"(provider unavailable — Low confidence)":""}</div>
                    <div>TTR {result.metrics.lexical_profile?.type_token_ratio} MATTR {result.metrics.lexical_profile?.mattr} • {JSON.stringify(result.metrics.lexical_profile?.frequency_profile)}</div>
                    {result.metrics.lexical_profile?.repetition_clusters?.length>0 && <div className="text-amber-700 dark:text-amber-300 font-medium">Repetition: {result.metrics.lexical_profile.repetition_clusters.map((c:any)=>`${c.lemma||c.phrase}×${c.count}`).join(", ")}</div>}
                    {result.metrics.lexical_profile?.provider_available===false && <div className="text-[11px] text-muted-foreground">Vocab hidden — provider unavailable</div>}
                  </div>
                </div>
              )}
              {result.upgrade && (
                <div className="space-y-2 border-t pt-3">
                  <div className="text-xs font-bold flex items-center gap-1"><Lightbulb className="h-3.5 w-3.5"/> Native Upgrade</div>
                  <div className="rounded-lg border p-2 bg-muted/20">
                    <div className="text-xs font-bold">Minimal correction</div><div className="text-sm">{result.upgrade.minimal_correction || "—"}</div>
                  </div>
                  <div className="rounded-lg border p-2 bg-primary/5">
                    <div className="text-xs font-bold">Native version</div><div className="text-sm">{result.upgrade.native_version || "—"}</div>
                  </div>
                  {result.upgrade.professional_version && <div className="rounded-lg border p-2"><div className="text-xs font-bold">Professional</div><div className="text-sm">{result.upgrade.professional_version}</div></div>}
                  {result.upgrade_explanations?.length>0 && (
                    <div className="space-y-1">
                      {result.upgrade_explanations.map((ex:any,i:number)=>(
                        <div key={i} className="text-xs rounded border p-2"><span className="font-bold">Original:</span> {ex.original} → <span className="font-bold">Correction:</span> {ex.correction} <span className="text-muted-foreground">({ex.why})</span> → <span className="font-bold">Alt:</span> {ex.alternative}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                <Button variant="akane" onClick={handleGenerate}>Next Challenge</Button>
                <Button variant="outline" onClick={()=>{
                  if (rafRef.current) cancelAnimationFrame(rafRef.current);
                  if (recRafRef.current) cancelAnimationFrame(recRafRef.current);
                  recorder.releaseMicrophone();
                  mono.reset();
                }}>Back to Generate</Button>
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-3">
          <Card className="p-3">
            <div className="text-xs font-bold flex items-center gap-1.5"><Settings2 className="h-3.5 w-3.5"/> Speech Status</div>
            <div className="mt-2 text-xs space-y-1">
              <div>Phase: <Badge size="sm" variant="jlpt">{phase}</Badge></div>
              <div>Target: {speechConfig?.target_duration_sec ?? durationSec}s • Prep: {speechConfig?.prep_duration_sec ?? prepSec}s</div>
              <div>Genre: {speechConfig?.genre ?? "auto"} • Domain: {speechConfig?.topic_domain ?? "auto"}</div>
              <div>Support: {SUPPORT_LABEL[speechConfig?.support_level ?? 0] ?? "auto"}</div>
            </div>
          </Card>
          <Card className="p-3">
            <div className="text-xs font-bold">Audio</div>
            <div className="text-[11px] text-muted-foreground">Volume {Math.round(recorder.volumeLevel*100)}% • {recorder.state}</div>
            <div className="h-2 rounded-full bg-muted overflow-hidden mt-1"><div className="h-full bg-primary" style={{width:`${Math.round(recorder.volumeLevel*100)}%`}}/></div>
            {recorder.error && <div className="text-xs text-red-600 mt-1 flex items-center gap-1"><AlertCircle className="h-3 w-3"/>{recorder.error}</div>}
          </Card>
          <Card className="p-3 bg-muted/30">
            <div className="text-xs font-bold">Transcript (supplementary)</div>
            <textarea value={transcriptInput} onChange={e=>setTranscriptInput(e.target.value)} placeholder="STT transcript will appear here; you may edit supplementally but audio is required" className="mt-1 w-full rounded-lg border bg-background p-2 text-sm min-h-[90px]"/>
            <div className="text-[11px] text-muted-foreground mt-1">Audio required — text-only submit is rejected with error toast.</div>
          </Card>
        </div>
      </div>

      <Modal isOpen={showHelp} onClose={()=>setShowHelp(false)} title="Phím tắt Monologue Lab">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg border bg-muted/40 p-2.5"><div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.speakingMic)}</div><div className="text-muted-foreground">Bắt đầu / Dừng ghi âm</div></div>
          <div className="rounded-lg border bg-muted/40 p-2.5"><div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillSubmitOrNext)}</div><div className="text-muted-foreground">Tạo đề / Bỏ qua chuẩn bị / Tiếp tục</div></div>
          <div className="rounded-lg border bg-muted/40 p-2.5"><div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillRetry)}</div><div className="text-muted-foreground">Làm lại bài nói</div></div>
          <div className="rounded-lg border bg-muted/40 p-2.5"><div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillToggleHelp)}</div><div className="text-muted-foreground">Toggle help</div></div>
          <div className="rounded-lg border bg-muted/40 p-2.5"><div className="font-bold font-mono text-primary">Esc</div><div className="text-muted-foreground">Thoát / Hủy</div></div>
        </div>
      </Modal>
    </div>
  );
}

