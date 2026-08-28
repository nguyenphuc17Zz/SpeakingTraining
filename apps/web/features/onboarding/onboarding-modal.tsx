"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Mic,
  Volume2,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Compass,
  Zap,
  Flame,
  ShieldCheck,
  Award,
} from "lucide-react";

interface OnboardingModalProps {
  forceOpen?: boolean;
  onComplete?: () => void;
}

const GOALS = [
  { id: "fluency", label: "Everyday Conversational Fluency", ja: "日常会話のスムーズな発話", icon: "💬" },
  { id: "jlpt", label: "JLPT Speaking & Grammar Mastery", ja: "JLPT対策・文法と語彙の定着", icon: "📚" },
  { id: "business", label: "Business & Formal Keigo", ja: "ビジネス日本語・敬語の習得", icon: "💼" },
  { id: "travel", label: "Travel & Culture Immersion", ja: "旅行・アニメ・趣味の日本語", icon: "🗾" },
];

const LEVELS = [
  { id: "beginner", label: "Beginner (初級 N5-N4)", desc: "Can form basic sentences, want to practice speaking without hesitation." },
  { id: "intermediate", label: "Intermediate (中級 N3)", desc: "Can converse reasonably well, want to fix recurring grammar & pitch habits." },
  { id: "advanced", label: "Advanced (上級 N2-N1)", desc: "Seeking natural native phrasing, nuanced nuances, and workplace Keigo." },
];

const STYLES = [
  { id: "polite", label: "Polite (丁寧語 です/ます)", desc: "Standard courteous Japanese for general conversations." },
  { id: "casual", label: "Casual (ため口・口語)", desc: "Friendly informal Japanese for friends, anime, and daily life." },
  { id: "adaptive", label: "Adaptive (状況に合わせて変化)", desc: "Match persona role and workplace hierarchy dynamically." },
];

export function OnboardingModal({ forceOpen = false, onComplete }: OnboardingModalProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);

  // Form State
  const [selectedGoal, setSelectedGoal] = useState("fluency");
  const [selectedLevel, setSelectedLevel] = useState("intermediate");
  const [selectedStyle, setSelectedStyle] = useState("polite");
  const [micTested, setMicTested] = useState(false);
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState(0);

  useEffect(() => {
    if (forceOpen) {
      setIsOpen(true);
      return;
    }
    const completed = localStorage.getItem("hanasu_onboarding_completed");
    if (!completed) {
      setIsOpen(true);
    }
  }, [forceOpen]);

  const testStreamRef = useRef<MediaStream | null>(null);
  const testAudioCtxRef = useRef<AudioContext | null>(null);

  const cleanupTestMic = () => {
    if (testStreamRef.current) {
      testStreamRef.current.getTracks().forEach((t: MediaStreamTrack) => {
        try {
          t.stop();
        } catch {}
      });
      testStreamRef.current = null;
    }
    if (testAudioCtxRef.current && testAudioCtxRef.current.state !== "closed") {
      try {
        testAudioCtxRef.current.close();
      } catch {}
      testAudioCtxRef.current = null;
    }
    setIsTestingMic(false);
  };

  useEffect(() => {
    return () => {
      cleanupTestMic();
    };
  }, []);

  const testMicrophone = async () => {
    setIsTestingMic(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      testStreamRef.current = stream;
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      testAudioCtxRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      let frames = 0;
      const interval = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setVolumeLevel(Math.min(100, Math.round((avg / 128) * 100)));
        frames++;
        if (frames > 30) {
          clearInterval(interval);
          cleanupTestMic();
          setMicTested(true);
        }
      }, 100);
    } catch (e) {
      console.warn("Mic test error or cancelled", e);
      cleanupTestMic();
      setMicTested(true); // Don't block user
    }
  };

  const handleFinish = (goToSpeaking = true) => {
    localStorage.setItem("hanasu_onboarding_completed", "true");
    localStorage.setItem(
      "hanasu_learner_preferences",
      JSON.stringify({
        goal: selectedGoal,
        level: selectedLevel,
        style: selectedStyle,
      })
    );
    setIsOpen(false);
    if (onComplete) onComplete();
    if (goToSpeaking) {
      router.push("/speaking");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-card border border-border rounded-3xl p-6 sm:p-8 shadow-2xl shadow-primary/5 space-y-6">
        {/* Progress Header */}
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-primary to-aizome-600 flex items-center justify-center font-bold text-primary-foreground text-sm">
              話
            </div>
            <div>
              <span className="text-xs font-black tracking-wider text-primary uppercase">
                Hanasu AI Onboarding (初期設定)
              </span>
              <p className="text-[11px] text-muted-foreground">Step {step} of 4</p>
            </div>
          </div>

          <button
            onClick={() => handleFinish(false)}
            className="text-xs text-muted-foreground hover:text-foreground underline font-medium"
          >
            Skip to Dashboard
          </button>
        </div>

        {/* Step 1: Welcome & Goal */}
        {step === 1 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <h2 className="text-lg font-bold text-foreground">Welcome to Japanese Speaking Training OS! 🎌</h2>
              <p className="text-xs text-muted-foreground mt-1">
                What is your primary speaking goal? We'll tailor your conversation topics, corrections, and daily drills.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {GOALS.map((g) => (
                <button
                  key={g.id}
                  onClick={() => setSelectedGoal(g.id)}
                  className={`p-3.5 rounded-2xl border text-left transition-all ${
                    selectedGoal === g.id
                      ? "bg-primary/10 border-primary/40 text-foreground shadow-md shadow-primary/5"
                      : "bg-background/40 border-border text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <div className="text-xl mb-1.5">{g.icon}</div>
                  <p className="text-xs font-bold">{g.label}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5 font-jp">{g.ja}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Speaking Level */}
        {step === 2 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <h2 className="text-lg font-bold text-foreground">Select Your Target Speaking Level 🎯</h2>
              <p className="text-xs text-muted-foreground mt-1">
                This anchors your AI conversation speed, vocabulary complexity, and pronunciation tolerance.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              {LEVELS.map((l) => (
                <button
                  key={l.id}
                  onClick={() => setSelectedLevel(l.id)}
                  className={`w-full p-4 rounded-2xl border text-left transition-all ${
                    selectedLevel === l.id
                      ? "bg-aizome-500/10 border-aizome-500/40 text-foreground shadow-md shadow-aizome-500/5"
                      : "bg-background/40 border-border text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <p className="text-xs font-bold text-foreground">{l.label}</p>
                  <p className="text-[11px] text-muted-foreground mt-1">{l.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Speaking Style */}
        {step === 3 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <h2 className="text-lg font-bold text-foreground">Preferred Speaking Style & Formality 👘</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Choose how you would like conversation partners to respond to you.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStyle(s.id)}
                  className={`w-full p-4 rounded-2xl border text-left transition-all ${
                    selectedStyle === s.id
                      ? "bg-primary/10 border-primary/40 text-foreground"
                      : "bg-background/40 border-border text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <p className="text-xs font-bold text-foreground">{s.label}</p>
                  <p className="text-[11px] text-muted-foreground mt-1">{s.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Microphone & Ready */}
        {step === 4 && (
          <div className="space-y-5 animate-in fade-in duration-150">
            <div>
              <h2 className="text-lg font-bold text-foreground">Audio & Speech Setup 🎙️</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Let's make sure your microphone is ready for real-time Faster-Whisper transcription.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-background border border-border flex flex-col items-center justify-center text-center space-y-3">
              <div
                className={`h-12 w-12 rounded-2xl flex items-center justify-center transition-all ${
                  micTested
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : isTestingMic
                    ? "bg-primary/20 text-primary animate-pulse"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <Mic className="h-6 w-6" />
              </div>

              <div>
                <p className="text-xs font-bold text-foreground">
                  {micTested
                    ? "Microphone Configured & Ready! ✅"
                    : isTestingMic
                    ? "Speak into your microphone now..."
                    : "Test Microphone Permissions"}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Faster-Whisper auto-detects GPU CUDA acceleration for &lt;200ms latency.
                </p>
              </div>

              {isTestingMic && (
                <div className="w-48 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-75"
                    style={{ width: `${volumeLevel}%` }}
                  />
                </div>
              )}

              {!micTested && !isTestingMic && (
                <Button variant="outline" size="sm" onClick={testMicrophone}>
                  <Mic className="h-3.5 w-3.5 mr-1" />
                  <span>Start 3-second Mic Test</span>
                </Button>
              )}
            </div>

            <div className="p-3.5 rounded-2xl bg-aizome-500/10 border border-aizome-500/20 flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-aizome-400 shrink-0" />
              <p className="text-[11px] text-aizome-200">
                You're all set! Onboarding completion will earn you <strong className="text-amber-400">+100 XP</strong> and unlock your first conversational partner.
              </p>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          {step > 1 ? (
            <Button variant="outline" size="sm" onClick={() => setStep(step - 1)}>
              <ArrowLeft className="h-3.5 w-3.5 mr-1" />
              <span>Back</span>
            </Button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <Button variant="primary" size="sm" onClick={() => setStep(step + 1)}>
              <span>Next</span>
              <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => handleFinish(false)}>
                <span>Dashboard</span>
              </Button>
              <Button variant="primary" size="sm" onClick={() => handleFinish(true)}>
                <Mic className="h-3.5 w-3.5 mr-1" />
                <span>Start First Speaking Session!</span>
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
