"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Volume2, BookOpen, Music, Check } from "lucide-react";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface PitchCheatsheetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PitchCheatsheetModal({ isOpen, onClose }: PitchCheatsheetModalProps) {
  const [activeTab, setActiveTab] = useState<"contours" | "minimal_pairs" | "mora" | "devoicing">("contours");

  const playTTS = (text: string) => {
    soundFX.playFurin();
    speakJapaneseText(text, { rate: 1.0 });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Cẩm Nang Cao Độ & Phách Tiếng Nhật (Pitch & Mora Handbook)"
      description="Tra cứu nhanh 4 mô hình cao độ Tokyo, bảng cặp từ tối thiểu, quy tắc đếm phách và vô thanh hóa"
      className="max-w-3xl"
    >
      <div className="space-y-4 pt-2">
        {/* Navigation Tabs */}
        <div className="flex items-center p-1 rounded-2xl bg-muted/70 border border-border overflow-x-auto scrollbar-thin">
          {[
            { id: "contours", label: "📈 4 Mô Hình Cao Độ Tokyo" },
            { id: "minimal_pairs", label: "👥 Bảng Cặp Từ Tối Thiểu" },
            { id: "mora", label: "⏱️ Quy Tắc Đếm Phách (Mora)" },
            { id: "devoicing", label: "🔇 Vô Thanh Hóa (Devoicing)" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                soundFX.playFurin();
                setActiveTab(tab.id as any);
              }}
              className={cn(
                "flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all whitespace-nowrap text-center",
                activeTab === tab.id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: 4 Tokyo Pitch Contours */}
        {activeTab === "contours" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {[
              {
                type: "平板型 (Heiban - Kiểu Bằng [0])",
                pattern: "L - H - H - H...",
                desc: "Âm thứ nhất THẤP, âm thứ hai và các âm tiếp theo CAO, khi đi kèm trợ từ (が, を) vẫn giữ CAO.",
                examples: [
                  { w: "日本語 (にほんご)", exp: "L-H-H-H" },
                  { w: "飴 (あめ)", exp: "L-H (Viên kẹo)" },
                  { w: "桜 (さくら)", exp: "L-H-H" },
                  { w: "友達 (ともだち)", exp: "L-H-H-H" },
                ],
              },
              {
                type: "頭高型 (Atamadaka - Kiểu Đầu Cao [1])",
                pattern: "H - L - L - L...",
                desc: "Âm đầu tiên CAO, hạ giọng ngay ở âm thứ hai và giữ THẤP cho đến hết từ và trợ từ.",
                examples: [
                  { w: "雨 (あめ)", exp: "H-L (Cơn mưa)" },
                  { w: "箸 (はし)", exp: "H-L (Đôi đũa)" },
                  { w: "寿司 (すし)", exp: "H-L" },
                  { w: "本 (ほん)", exp: "H-L" },
                ],
              },
              {
                type: "中高型 (Nakadaka - Kiểu Giữa Cao [2..N-1])",
                pattern: "L - H... - L - L...",
                desc: "Âm đầu THẤP, lên CAO ở giữa rồi HẠ giọng xuống THẤP trước khi kết thúc từ.",
                examples: [
                  { w: "ありがとう", exp: "L-H-L-L-L (Hạ ở âm thứ 2)" },
                  { w: "卵 (たまご)", exp: "L-H-L" },
                  { w: "飛行機 (ひこうき)", exp: "L-H-L-L" },
                ],
              },
              {
                type: "尾高型 (Odaka - Kiểu Đuôi Cao [N])",
                pattern: "L - H - H... (Hạ khi gặp trợ từ)",
                desc: "Âm đầu THẤP, các âm sau CAO đến hết từ; nhưng HẠ ngay xuống THẤP khi có trợ từ (が, を, に).",
                examples: [
                  { w: "橋 (はし)", exp: "L-H (Cây cầu) ➔ はしが (L-H-L)" },
                  { w: "花 (はな)", exp: "L-H (Bông hoa) ➔ はなが (L-H-L)" },
                  { w: "山 (やま)", exp: "L-H (Ngọn núi)" },
                ],
              },
            ].map((c, i) => (
              <div key={i} className="p-4 rounded-2xl border border-border/80 bg-card space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-xs text-foreground">{c.type}</h4>
                  <Badge variant="fuji" size="sm" className="font-mono">{c.pattern}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">{c.desc}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {c.examples.map((ex, j) => (
                    <button
                      key={j}
                      onClick={() => playTTS(ex.w)}
                      className="px-2.5 py-1 rounded-xl bg-muted/50 hover:bg-muted border text-xs font-jp flex items-center gap-1.5 transition-all"
                    >
                      <Volume2 className="h-3 w-3 text-primary" />
                      <span>{ex.w}</span>
                      <span className="text-[10px] text-muted-foreground font-sans">({ex.exp})</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Minimal Pairs */}
        {activeTab === "minimal_pairs" && (
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {[
              { a: "雨 (あめ)", typeA: "頭高 [1] (Mưa)", b: "飴 (あめ)", typeB: "平板 [0] (Kẹo)" },
              { a: "箸 (はし)", typeA: "頭高 [1] (Đũa)", b: "橋 (はし)", typeB: "尾高 [2] (Cây cầu)" },
              { a: "酒 (さけ)", typeA: "平板 [0] (Rượu)", b: "鮭 (さけ)", typeB: "頭高 [1] (Cá hồi)" },
              { a: "柿 (かき)", typeA: "平板 [0] (Quả hồng)", b: "牡蠣 (かき)", typeB: "頭高 [1] (Con hàu)" },
              { a: "白 (しろ)", typeA: "頭高 [1] (Màu trắng)", b: "城 (しろ)", typeB: "平板 [0] (Lâu đài)" },
              { a: "雲 (くも)", typeA: "頭高 [1] (Đám mây)", b: "蜘蛛 (くも)", typeB: "平板 [0] (Con nhện)" },
              { a: "今 (いま)", typeA: "頭高 [1] (Bây giờ)", b: "居間 (いま)", typeB: "平板 [0] (Phòng khách)" },
              { a: "花 (はな)", typeA: "尾高 [2] (Bông hoa)", b: "鼻 (はな)", typeB: "平板 [0] (Cái mũi)" },
            ].map((p, i) => (
              <div key={i} className="p-3 rounded-xl border border-border/70 bg-card flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 flex-1">
                  <button onClick={() => playTTS(p.a)} className="font-bold font-jp text-primary hover:underline flex items-center gap-1">
                    <Volume2 className="h-3 w-3" />
                    <span>{p.a}</span>
                  </button>
                  <span className="text-muted-foreground text-[11px]">({p.typeA})</span>
                </div>
                <span className="text-muted-foreground font-bold">vs</span>
                <div className="flex items-center gap-2 flex-1 justify-end">
                  <button onClick={() => playTTS(p.b)} className="font-bold font-jp text-primary hover:underline flex items-center gap-1">
                    <Volume2 className="h-3 w-3" />
                    <span>{p.b}</span>
                  </button>
                  <span className="text-muted-foreground text-[11px]">({p.typeB})</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 3: Mora Timing */}
        {activeTab === "mora" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 text-xs">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">1. Trường Âm (長音 - Long Vowels): Tính là 1 phách riêng</h4>
              <p className="text-muted-foreground">おばさん (4 mora - Cô/Dì) ↔ おばあさん (5 mora - Bà cụ)</p>
              <p className="text-muted-foreground">ビル (2 mora - Tòa nhà) ↔ ビール (3 mora - Đồ uống Bia)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">2. Âm Ngắt (促音 - Small Tsu っ): Tính là 1 phách im lặng</h4>
              <p className="text-muted-foreground">きて (2 mora - Hãy đến) ↔ きって (3 mora - Con tem)</p>
              <p className="text-muted-foreground">さか (2 mora - Con dốc) ↔ さっか (3 mora - Nhà văn)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">3. Âm Mũi (撥音 - Âm ん): Tính là 1 phách riêng</h4>
              <p className="text-muted-foreground">ほん (2 mora - Quyển sách) • にほん (3 mora - Nước Nhật)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">4. Âm Ghép (拗音 - Âm nhỏ ゃ, ゅ, ょ): Tính chung 1 phách</h4>
              <p className="text-muted-foreground">きゃく (2 mora: [きゃ] + [く] - Khách hàng) • きょう (2 mora: [きょ] + [う] - Hôm nay)</p>
            </div>
          </div>
        )}

        {/* Tab 4: Vowel Devoicing */}
        {activeTab === "devoicing" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 text-xs">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">Quy tắc Vô thanh hóa (母音無声化):</h4>
              <p className="text-muted-foreground leading-relaxed">
                Nguyên âm <strong>[ i ]</strong> và <strong>[ u ]</strong> không rung dây thanh (chỉ phát ra luồng hơi gió nhẹ) khi:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                <li>Đứng giữa 2 phụ âm vô thanh: <strong>k, s, t, h, p</strong> (VD: すき [suki] ➔ âm [su] vô thanh; つき [tsuki] ➔ âm [tsu] vô thanh).</li>
                <li>Đứng ở cuối câu sau phụ âm vô thanh: <strong>~です [desu]</strong>, <strong>~ました [mashita]</strong>.</li>
              </ul>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {[
                { w: "ありがとうございます", d: "す ở cuối câu vô thanh" },
                { w: "好きです (すきです)", d: "す vô thanh trước phụ âm k" },
                { w: "聞きます (ききます)", d: "き đầu tiên vô thanh" },
                { w: "二つ (ふたつ)", d: "ふ vô thanh trước phụ âm t" },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-xl border border-border/70 bg-card flex items-center justify-between">
                  <div>
                    <div className="font-bold font-jp text-foreground">{item.w}</div>
                    <div className="text-[11px] text-muted-foreground">{item.d}</div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => playTTS(item.w)} className="h-7 w-7 p-0">
                    <Volume2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="pt-3 border-t border-border flex justify-end">
          <Button size="sm" onClick={onClose} className="text-xs font-bold gap-1.5">
            <Check className="h-3.5 w-3.5" />
            <span>Đã hiểu</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
}
