"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Crown,
  Search,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Users,
  Building,
  Volume2,
  Sparkles,
} from "lucide-react";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { cn } from "@/lib/utils";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectWord?: (word: string) => void;
}

const KEIGO_VERB_TABLE = [
  { plain: "する (Làm)", sonkeigo: "なさる", kenjougo: "いたす", teineigo: "します", example: "ご検討なさる / 準備いたします" },
  { plain: "言う (Nói)", sonkeigo: "おっしゃる", kenjougo: "申す / 申し上げる", teineigo: "言います", example: "社長がおっしゃる / 田中と申します" },
  { plain: "行く (Đi)", sonkeigo: "いらっしゃる", kenjougo: "参る / 伺う", teineigo: "行きます", example: "どちらにいらっしゃいますか / 明日伺います" },
  { plain: "来る (Đến)", sonkeigo: "いらっしゃる / お見えになる", kenjougo: "参る", teineigo: "来ます", example: "お客様がお見えになりました" },
  { plain: "いる (Ở/Có)", sonkeigo: "いらっしゃる", kenjougo: "おる", teineigo: "います", example: "部長はいらっしゃいますか / 席におります" },
  { plain: "食べる・飲む (Ăn/Uống)", sonkeigo: "召し上がる", kenjougo: "いただく", teineigo: "食べます", example: "どうぞ召し上がってください / いただきます" },
  { plain: "見る (Xem/Nhìn)", sonkeigo: "ご覧になる", kenjougo: "拝見する", teineigo: "見ます", example: "資料をご覧になりましたか / 拝見しました" },
  { plain: "知っている (Biết)", sonkeigo: "ご存知だ", kenjougo: "存じている / 存じる", teineigo: "知っています", example: "ご存知ですか / 存じております" },
  { plain: "聞く (Nghe/Hỏi)", sonkeigo: "お聞きになる", kenjougo: "伺う / 拝聴する", teineigo: "聞きます", example: "お話を伺いました" },
  { plain: "会う (Gặp)", sonkeigo: "お会いになる", kenjougo: "お目にかかる", teineigo: "会います", example: "初めてお目にかかります" },
  { plain: "もらう (Nhận)", sonkeigo: "—", kenjougo: "いただく / 頂戴する", teineigo: "もらいます", example: "名刺を頂戴いたします" },
  { plain: "あげる (Tặng)", sonkeigo: "—", kenjougo: "差し上げる", teineigo: "あげます", example: "資料を差し上げます" },
  { plain: "くれる (Cho mình)", sonkeigo: "くださる", kenjougo: "—", teineigo: "くれます", example: "教えてくださり感謝いたします" },
  { plain: "伝える (Nhắn lại)", sonkeigo: "お伝えになる", kenjougo: "申し伝える", teineigo: "伝えます", example: "担当の者に申し伝えます" },
  { plain: "思う (Nghĩ)", sonkeigo: "お思いになる", kenjougo: "存じます", teineigo: "思います", example: "結構だと存じます" },
];

export function KeigoCheatsheetModal({ isOpen, onClose, onSelectWord }: Props) {
  const [activeTab, setActiveTab] = useState<"verbs" | "uchi_soto" | "double_keigo">("verbs");
  const [searchQuery, setSearchQuery] = useState("");
  const [speakingText, setSpeakingText] = useState<string | null>(null);

  const handleSpeak = (text: string) => {
    if (!text || text === "—") return;
    setSpeakingText(text);
    speakJapaneseText(text, {
      rate: 0.95,
      onEnd: () => setSpeakingText(null),
      onError: () => setSpeakingText(null),
    });
  };

  const filteredVerbs = KEIGO_VERB_TABLE.filter(
    (v) =>
      v.plain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.sonkeigo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.kenjougo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.example.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="📖 Sổ Tay Kính Ngữ Công Sở (Pocket Reference)" className="max-w-4xl">
      <div className="space-y-4 text-sm">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-border/80 pb-2">
          <Button
            size="sm"
            variant={activeTab === "verbs" ? "akane" : "ghost"}
            onClick={() => setActiveTab("verbs")}
            className="gap-1.5 font-bold"
          >
            <Crown className="h-4 w-4" /> Bảng Động Từ Bất Quy Tắc
          </Button>
          <Button
            size="sm"
            variant={activeTab === "uchi_soto" ? "akane" : "ghost"}
            onClick={() => setActiveTab("uchi_soto")}
            className="gap-1.5 font-bold"
          >
            <Users className="h-4 w-4" /> Quy Tắc Trong/Ngoài (Uchi - Soto)
          </Button>
          <Button
            size="sm"
            variant={activeTab === "double_keigo" ? "akane" : "ghost"}
            onClick={() => setActiveTab("double_keigo")}
            className="gap-1.5 font-bold"
          >
            <ShieldAlert className="h-4 w-4" /> Bẫy Nhị Trùng Kính Ngữ
          </Button>
        </div>

        {/* Tab 1: Verbs Table */}
        {activeTab === "verbs" && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm: 食べる, 召し上がる, 申す, ăn, nói, gặp..."
                className="w-full rounded-xl border bg-background pl-9 pr-4 py-2 text-xs focus:border-primary focus:ring-1 focus:ring-primary/20"
              />
            </div>

            <div className="max-h-[380px] overflow-y-auto rounded-2xl border border-border/80 bg-card">
              <table className="w-full text-left text-xs border-collapse font-jp">
                <thead className="sticky top-0 bg-muted/90 backdrop-blur-xs border-b border-border text-[11px] font-bold text-muted-foreground z-10">
                  <tr>
                    <th className="p-2.5 font-sans">Động từ gốc</th>
                    <th className="p-2.5 text-rose-600 dark:text-rose-400 font-sans">Tôn Kính (尊敬語) ↑</th>
                    <th className="p-2.5 text-emerald-600 dark:text-emerald-400 font-sans">Khiêm Nhường (謙譲語) ↓</th>
                    <th className="p-2.5 text-muted-foreground hidden md:table-cell font-sans">Ví dụ ứng dụng</th>
                    <th className="p-2.5 text-right font-sans">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredVerbs.map((v, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="p-2.5 font-bold text-foreground font-sans">{v.plain}</td>
                      <td className="p-2.5">
                        <div className="flex items-center gap-1.5 font-extrabold text-rose-600 dark:text-rose-400">
                          <UniversalFurigana text={v.sonkeigo} fontSize="sm" />
                          {v.sonkeigo !== "—" && (
                            <button
                              onClick={() => handleSpeak(v.sonkeigo)}
                              className="text-muted-foreground hover:text-rose-600 p-0.5"
                              title="Nghe phát âm"
                            >
                              <Volume2 className={cn("h-3 w-3", speakingText === v.sonkeigo && "animate-bounce text-rose-600")} />
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="p-2.5">
                        <div className="flex items-center gap-1.5 font-extrabold text-emerald-600 dark:text-emerald-400">
                          <UniversalFurigana text={v.kenjougo} fontSize="sm" />
                          {v.kenjougo !== "—" && (
                            <button
                              onClick={() => handleSpeak(v.kenjougo.split("/")[0].trim())}
                              className="text-muted-foreground hover:text-emerald-600 p-0.5"
                              title="Nghe phát âm"
                            >
                              <Volume2 className={cn("h-3 w-3", speakingText === v.kenjougo.split("/")[0].trim() && "animate-bounce text-emerald-600")} />
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="p-2.5 text-muted-foreground text-[11px] hidden md:table-cell">
                        <UniversalFurigana text={v.example} fontSize="sm" />
                      </td>
                      <td className="p-2.5 text-right">
                        {onSelectWord && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              onSelectWord(v.plain.split(" ")[0]);
                              onClose();
                            }}
                            className="h-6 px-2 text-[10px] font-bold text-primary hover:bg-primary/10"
                          >
                            Luyện từ này
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 rounded-xl bg-muted/40 border text-xs text-muted-foreground space-y-1">
              <p className="font-bold text-foreground">💡 Quy tắc biến đổi động từ thường (không bất quy tắc):</p>
              <p>• <strong>Tôn Kính Ngữ:</strong> お＋V_stem＋になる (Ví dụ: お読みになる, お待ちになる)</p>
              <p>• <strong>Khiêm Nhường Ngữ:</strong> お＋V_stem＋する / いたす (Ví dụ: お持ちする, お手伝いいたします)</p>
            </div>
          </div>
        )}

        {/* Tab 2: Uchi / Soto Principle */}
        {activeTab === "uchi_soto" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-4 rounded-2xl bg-rose-500/8 border border-rose-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="sakura" size="sm">Uchi (身内)</Badge>
                  <span className="font-bold text-xs text-rose-700 dark:text-rose-300">Bản thân & Người công ty mình</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Bản thân, đồng nghiệp, và khi nói chuyện với đối tác ngoài thì <strong>Giám đốc/Trưởng phòng công ty mình</strong> cũng được tính là người trong nhà (Uchi).
                </p>
                <div className="p-2.5 rounded-xl bg-background/80 border text-xs space-y-1">
                  <span className="font-bold text-primary">Hành động của Uchi ➔ Dùng Khiêm Nhường Ngữ (謙譲語 ↓)</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-emerald-500/8 border border-emerald-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="matcha" size="sm">Soto (他者)</Badge>
                  <span className="font-bold text-xs text-emerald-700 dark:text-emerald-300">Khách hàng & Đối tác ngoài</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Khách hàng, đối tác, người gọi điện từ công ty khác đến đều là người ngoài (Soto).
                </p>
                <div className="p-2.5 rounded-xl bg-background/80 border text-xs space-y-1">
                  <span className="font-bold text-rose-600 dark:text-rose-400">Hành động của Soto ➔ Dùng Tôn Kính Ngữ (尊敬語 ↑)</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-500/8 border border-amber-500/20 space-y-3">
              <div className="font-bold text-xs text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <Building className="h-4 w-4" /> Tình huống kinh điển: Nói về Giám đốc mình với khách hàng ngoài
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-2 text-rose-600 dark:text-rose-400">
                  <span className="font-bold">❌ Sai lầm:</span>
                  <span>「田中社長はおっしゃいました」(Tôn xưng sếp mình trước mặt khách ngoài)</span>
                </div>
                <div className="flex items-start gap-2 text-emerald-600 dark:text-emerald-400 font-bold">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                  <span>「社長の田中が申しました」(Bỏ chức danh và dùng khiêm nhường ngữ 申す)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Double Keigo Pitfalls */}
        {activeTab === "double_keigo" && (
          <div className="space-y-3">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" /> Nhị trùng kính ngữ (二重敬語) là gì?
              </h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Là lỗi dùng 2 lần kính ngữ trên cùng một động từ, khiến câu nói trở nên rườm rà, quá đà và thiếu chuyên nghiệp.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl border border-rose-500/30 bg-rose-500/5 space-y-2">
                <div className="font-bold text-rose-600">❌ Các lỗi Nhị trùng kính ngữ phổ biến:</div>
                <ul className="space-y-1.5 text-muted-foreground list-disc pl-4 font-jp">
                  <li><span className="line-through text-foreground">おっしゃられる</span> (おっしゃる ＋ られる ❌)</li>
                  <li><span className="line-through text-foreground">ご覧になられる</span> (ご覧になる ＋ られる ❌)</li>
                  <li><span className="line-through text-foreground">お召し上がりになられる</span> ❌</li>
                </ul>
              </div>

              <div className="p-3.5 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 space-y-2">
                <div className="font-bold text-emerald-600">✅ Cách nói chuẩn mực:</div>
                <ul className="space-y-1.5 text-foreground list-disc pl-4 font-jp font-bold">
                  <li>おっしゃる / 言われる</li>
                  <li>ご覧になる / 見られる</li>
                  <li>召し上がる</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <Button size="sm" variant="outline" onClick={onClose}>Đóng (Esc)</Button>
        </div>
      </div>
    </Modal>
  );
}
