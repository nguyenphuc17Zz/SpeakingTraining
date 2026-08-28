"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  Send,
  Volume2,
  Mic,
  MicOff,
  Bot,
  User,
  X,
  Minimize2,
  Maximize2,
  Trash2,
  RefreshCw,
  ChevronDown,
  Wand2,
  CheckCircle2,
  BookOpen,
  MessageCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { MarkdownContent } from "@/components/ui/markdown-content";
import { soundFX } from "@/lib/sound-fx";
import { aiApi } from "@/services/ai-api";
import { cn } from "@/lib/utils";

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  japaneseText?: string;
  romaji?: string;
  translation?: string;
}

type AssistantPersona = "inari" | "shiba";

const QUICK_CHIPS = [
  { label: "🎯 Sửa câu của tôi cho tự nhiên hơn", prompt: "Hãy giúp tôi sửa câu sau sang tiếng Nhật tự nhiên nhất (chia 3 cấp độ: thân mật, lịch sự, trang trọng): " },
  { label: "🎌 Phân biệt ngữ pháp khó", prompt: "Giải thích ngắn gọn và dễ hiểu cách phân biệt cặp ngữ pháp sau: " },
  { label: "🎙️ Mẹo phát âm & Pitch Accent", prompt: "Cho tôi mẹo phát âm ngữ điệu (Pitch Accent) chuẩn Tokyo cho từ: " },
  { label: "⚡ Khẩu ngữ Tokyo hay dùng hôm nay", prompt: "Hãy dạy tôi 2 khẩu ngữ tiếng Nhật cực kỳ tự nhiên mà người Tokyo dùng hằng ngày kèm ví dụ." },
  { label: "📖 Gợi ý bài học hôm nay", prompt: "Hôm nay tôi nên ưu tiên luyện kỹ năng gì: Hội thoại phản xạ hay Shadowing ngữ điệu?" },
];

const INARI_SYSTEM_PROMPT = `Bạn là Inari Sensei (稲荷先生 🦊) — Trợ lý AI và Gia sư tiếng Nhật thông thái, ấm áp, tận tụy của ứng dụng Hanasu AI.
Tính cách: Nhã nhặn, thông thái nhưng gần gũi, khích lệ người học không ngại sai.
Nhiệm vụ:
1. Giải đáp thắc mắc tiếng Nhật (ngữ pháp, từ vựng, kanji, văn hóa, phát âm Tokyo, kính ngữ Keigo).
2. Khi sửa câu cho người dùng, luôn đưa ra 3 sắc thái:
   - Thân mật (Casual / Tamego): Dùng với bạn bè
   - Lịch sự (Polite / Desu-Masu): Giao tiếp chuẩn mực
   - Trang trọng (Business / Keigo): Dùng trong công sở
3. Viết câu tiếng Nhật có kèm cách đọc Furigana/Romaji và giải nghĩa tiếng Việt súc tích, dễ hiểu.
4. Giữ câu trả lời ngắn gọn, trực quan, có định dạng rõ ràng, bullet points dễ đọc.`;

const SHIBA_SYSTEM_PROMPT = `Bạn là Shiba Senpai (柴犬先輩 🐕) — Trợ lý AI và Huấn luyện viên tiếng Nhật tràn đầy năng lượng, nhiệt huyết của Hanasu AI.
Tính cách: Trẻ trung, năng động, dùng từ ngữ vui tươi, cổ vũ người học giữ lửa streak và vượt qua thử thách.
Nhiệm vụ:
1. Giải đáp thắc mắc tiếng Nhật thực chiến, tập trung vào khẩu ngữ đời thường, Anime/Manga, du lịch và giao tiếp tự tin.
2. Khi người học đưa ra câu nói, hãy khen ngợi nỗ lực trước rồi chỉ ra cách nói 'cool ngầu' và chuẩn người bản xứ.
3. Kèm cách đọc Romaji và giải nghĩa tiếng Việt súc tích.`;

export function AIAssistantChatbox({
  streakDays = 1,
  className,
}: {
  streakDays?: number;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [persona, setPersona] = useState<AssistantPersona>("inari");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize Welcome Message from LocalStorage or Default
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedPersona = localStorage.getItem("hanasu-assistant-persona") as AssistantPersona | null;
    if (savedPersona) setPersona(savedPersona);

    const savedChat = localStorage.getItem("hanasu-assistant-chat");
    if (savedChat) {
      try {
        setMessages(JSON.parse(savedChat));
      } catch (e) {
        console.warn("Invalid chat cache", e);
      }
    } else {
      setMessages([
        {
          id: "welcome-1",
          sender: "ai",
          text: "Xin chào! Mình là Inari Sensei (お稲荷先生 🦊). Hôm nay bạn có thắc mắc ngữ pháp nào, muốn sửa câu cho tự nhiên hay cần mẹo phát âm tiếng Nhật không? Cứ hỏi mình nhé!",
          timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, []);

  // Save messages to LocalStorage
  const saveMessages = (msgs: ChatMessage[]) => {
    setMessages(msgs);
    if (typeof window !== "undefined") {
      localStorage.setItem("hanasu-assistant-chat", JSON.stringify(msgs));
    }
  };

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || isLoading) return;

    soundFX.playSuikinkutsu();
    setInputText("");

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    };

    const newHistory = [...messages, userMsg];
    saveMessages(newHistory);
    setIsLoading(true);

    try {
      const systemInstruction = persona === "inari" ? INARI_SYSTEM_PROMPT : SHIBA_SYSTEM_PROMPT;
      const apiMessages = newHistory.slice(-6).map((m) => ({
        role: (m.sender === "user" ? "user" : "assistant") as "user" | "assistant",
        content: m.text,
      }));

      const res = await aiApi.generate({
        system_instruction: systemInstruction,
        messages: apiMessages,
        task: "conversation",
        temperature: 0.7,
        max_output_tokens: 600,
      });

      const replyText =
        res?.text ||
        "Xin lỗi bạn, kết nối của mình đang bị chập chờn một chút. Bạn thử gửi lại câu hỏi nhé!";

      soundFX.playFurin();

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        text: replyText,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      };

      saveMessages([...newHistory, aiMsg]);
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: `ai-err-${Date.now()}`,
        sender: "ai",
        text: `Đã xảy ra lỗi kết nối AI (${err?.message || "Lỗi máy chủ"}). Bạn vui lòng thử lại sau nhé!`,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      };
      saveMessages([...newHistory, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    soundFX.playHankoStamp();
    const freshWelcome: ChatMessage[] = [
      {
        id: `welcome-${Date.now()}`,
        sender: "ai",
        text: `Đã làm mới cuộc trò chuyện! ${
          persona === "inari" ? "Inari Sensei 🦊" : "Shiba Senpai 🐕"
        } đã sẵn sàng hỗ trợ bạn.`,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      },
    ];
    saveMessages(freshWelcome);
  };

  const handleSwitchPersona = (p: AssistantPersona) => {
    soundFX.playFurin();
    setPersona(p);
    if (typeof window !== "undefined") {
      localStorage.setItem("hanasu-assistant-persona", p);
    }
  };

  const handleSpeakText = (msgId: string, text: string) => {
    if (typeof window === "undefined") return;
    setPlayingAudioId(msgId);
    soundFX.playSuikinkutsu();

    // Extract Japanese characters or read entire text
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ja-JP";
    utterance.rate = 0.95;
    utterance.onend = () => setPlayingAudioId(null);
    utterance.onerror = () => setPlayingAudioId(null);
    window.speechSynthesis.speak(utterance);
  };

  // Browser Speech Recognition for voice input
  const handleVoiceInput = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Trình duyệt của bạn chưa hỗ trợ Web Speech Recognition. Bạn hãy gõ câu hỏi bằng bàn phím nhé!");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      soundFX.playSuikinkutsu();
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const speechResult = event.results[0][0].transcript;
      setInputText((prev) => (prev ? `${prev} ${speechResult}` : speechResult));
      setIsListening(false);
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognition.start();
  };

  // Floating Trigger Button
  if (!isOpen) {
    return (
      <div className={cn("fixed bottom-5 right-5 z-40 flex items-center gap-2 select-none", className)}>
        {/* Helper Hint Pill */}
        <button
          onClick={() => {
            soundFX.playFurin();
            setIsOpen(true);
          }}
          className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-2xl border border-primary/30 bg-card/95 washi-texture backdrop-blur-xl shadow-sumi-lg text-xs font-bold text-foreground hover:border-primary transition-all duration-200 group"
        >
          <span className="text-base">{persona === "inari" ? "🦊" : "🐕"}</span>
          <span>Hỏi {persona === "inari" ? "Inari Sensei" : "Shiba Senpai"}</span>
          <span className="text-[10px] font-jp text-primary font-bold px-1.5 py-0.2 rounded bg-primary/10 border border-primary/20">
            AI 相談
          </span>
        </button>

        {/* Main Floating Avatar Button */}
        <button
          onClick={() => {
            soundFX.playFurin();
            setIsOpen(true);
          }}
          className="relative h-14 w-14 rounded-2xl border-2 border-primary/50 bg-gradient-to-br from-card to-muted shadow-sumi-lg flex items-center justify-center text-2xl hover:scale-105 active:scale-95 transition-all duration-200 group"
          title="Mở Trợ Lý AI Tiếng Nhật"
        >
          <span>{persona === "inari" ? "🦊" : "🐕"}</span>
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/75 opacity-75" />
            <span className="relative inline-flex rounded-full h-4 w-4 bg-primary border-2 border-card text-[9px] text-primary-foreground font-bold items-center justify-center">
              AI
            </span>
          </span>
        </button>
      </div>
    );
  }

  // Open Chatbox Window
  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 flex flex-col rounded-[26px] border-2 border-primary/35 bg-card/95 washi-texture backdrop-blur-2xl shadow-sumi-lg overflow-hidden transition-all duration-300",
        isMinimized
          ? "w-72 sm:w-80 h-14"
          : "w-[calc(100vw-32px)] sm:w-[380px] md:w-[420px] h-[580px] max-h-[calc(100vh-80px)]",
        className
      )}
    >
      {/* Background Shoji Lattice */}
      <div className="absolute inset-0 shoji-grid opacity-20 pointer-events-none" />

      {/* Header Bar */}
      <div className="h-14 px-4 border-b border-border/80 bg-card/90 flex items-center justify-between shrink-0 relative z-10">
        <div className="flex items-center gap-2.5">
          <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary/20 to-primary/30 border border-primary/30 flex items-center justify-center text-lg shadow-sm">
            {persona === "inari" ? "🦊" : "🐕"}
          </span>
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs font-black font-display text-foreground">
                {persona === "inari" ? "Inari Sensei" : "Shiba Senpai"}
              </h3>
              <span className="text-[10px] font-jp font-bold text-primary px-1.5 py-0.2 rounded-full bg-primary/10 border border-primary/20">
                {persona === "inari" ? "稲荷先生" : "柴犬先輩"}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-matcha-500 animate-pulse" />
              <span>Gia sư AI luôn trực tuyến</span>
            </p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-1">
          {/* Persona switch button */}
          <button
            onClick={() => handleSwitchPersona(persona === "inari" ? "shiba" : "inari")}
            className="h-7 px-2 rounded-lg bg-muted hover:bg-muted/80 border border-border text-[10px] font-bold text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            title={`Đổi sang ${persona === "inari" ? "Shiba Senpai 🐕" : "Inari Sensei 🦊"}`}
          >
            <span>Đổi {persona === "inari" ? "🐕" : "🦊"}</span>
          </button>

          <button
            onClick={handleClearHistory}
            className="h-7 w-7 rounded-lg bg-muted hover:bg-muted/80 border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
            title="Làm mới lịch sử chat"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="h-7 w-7 rounded-lg bg-muted hover:bg-muted/80 border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
            title={isMinimized ? "Mở rộng" : "Thu nhỏ"}
          >
            {isMinimized ? <Maximize2 className="h-3.5 w-3.5" /> : <Minimize2 className="h-3.5 w-3.5" />}
          </button>

          <button
            onClick={() => setIsOpen(false)}
            className="h-7 w-7 rounded-lg bg-muted hover:bg-muted/80 border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
            title="Đóng chatbox"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Body when expanded */}
      {!isMinimized && (
        <>
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 scrollbar-thin relative z-10">
            {messages.map((msg) => {
              const isAi = msg.sender === "ai";
              return (
                <div
                  key={msg.id}
                  className={cn(
                    "flex flex-col gap-1 max-w-[88%]",
                    isAi ? "items-start mr-auto" : "items-end ml-auto"
                  )}
                >
                  <div className="flex items-center gap-1.5 px-1">
                    <span className="text-[10px] font-bold text-muted-foreground">
                      {isAi ? (persona === "inari" ? "🦊 Inari Sensei" : "🐕 Shiba Senpai") : "👤 Bạn"}
                    </span>
                    <span className="text-[9px] text-muted-foreground/60">{msg.timestamp}</span>
                  </div>

                  <div
                    className={cn(
                      "p-3 rounded-2xl text-xs leading-relaxed transition-all shadow-sm",
                      isAi
                        ? "bg-card border border-border/80 text-foreground rounded-tl-sm washi-texture"
                        : "bg-primary text-white font-medium rounded-tr-sm shadow-md"
                    )}
                  >
                    {isAi ? (
                      <MarkdownContent content={msg.text} />
                    ) : (
                      <p className="whitespace-pre-wrap select-text">{msg.text}</p>
                    )}

                    {/* Audio TTS button for AI messages */}
                    {isAi && (
                      <div className="mt-2 pt-2 border-t border-border/50 flex items-center justify-between gap-2">
                        <button
                          onClick={() => handleSpeakText(msg.id, msg.text)}
                          className="text-[10px] text-primary hover:opacity-80 font-bold flex items-center gap-1 transition-opacity"
                        >
                          <Volume2 className={cn("h-3 w-3", playingAudioId === msg.id && "animate-pulse")} />
                          <span>{playingAudioId === msg.id ? "Đang phát..." : "Nghe phát âm"}</span>
                        </button>
                        <HankoStamp text="指導" subtext="Sensei" variant="gold" size="sm" />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* AI Typing Indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 p-3 rounded-2xl bg-card border border-border text-xs text-muted-foreground w-fit animate-pulse">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
                <span>{persona === "inari" ? "Inari Sensei" : "Shiba Senpai"} đang soạn câu trả lời...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Chips */}
          <div className="px-3 py-1.5 border-t border-border/60 bg-muted/40 flex items-center gap-1.5 overflow-x-auto scrollbar-none shrink-0 relative z-10">
            {QUICK_CHIPS.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInputText(chip.prompt);
                  inputRef.current?.focus();
                }}
                className="whitespace-nowrap px-2.5 py-1 rounded-full border border-border/80 bg-card hover:bg-muted text-[10px] font-semibold text-muted-foreground hover:text-foreground transition-colors shrink-0"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-3 border-t border-border/80 bg-card/95 flex items-center gap-2 shrink-0 relative z-10"
          >
            {/* Voice Input Mic Button */}
            <button
              type="button"
              onClick={handleVoiceInput}
              className={cn(
                "h-9 w-9 rounded-xl border flex items-center justify-center transition-all shrink-0",
                isListening
                  ? "bg-primary text-primary-foreground border-primary animate-pulse shadow-md"
                  : "bg-muted hover:bg-muted/80 text-muted-foreground border-border"
              )}
              title={isListening ? "Đang lắng nghe..." : "Bấm để nói tiếng Nhật/Việt bằng giọng nói"}
            >
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>

            {/* Text Input */}
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Hỏi ${persona === "inari" ? "Inari Sensei" : "Shiba Senpai"} bất kỳ câu hỏi nào...`}
              disabled={isLoading}
              className="flex-1 h-9 px-3 rounded-xl border border-border bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />

            {/* Send Button */}
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!inputText.trim() || isLoading}
              className="h-9 w-9 p-0 rounded-xl shrink-0"
              title="Gửi câu hỏi"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </>
      )}
    </div>
  );
}
