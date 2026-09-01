"use client";

import React from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BookOpen, Sparkles, Zap, Target, ArrowRight, Layers } from "lucide-react";

interface RampCheatsheetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RampCheatsheetModal({ isOpen, onClose }: RampCheatsheetModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Cẩm Nang Phục Hồi Phát Ngôn (Mode 6 Cheatsheet)"
      description="Sơ đồ 11 nấc thang phát triển câu và mẫu từ nối chuẩn tiếng Nhật tự nhiên."
      className="max-w-2xl sm:max-w-3xl"
    >
      <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
        {/* 1. Sơ đồ 11 Nấc thang */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">Sơ đồ 11 Nấc Thang Phát Ngôn (Stage 0 → 10)</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 0: Echo (Nhại âm)</span>
                <Badge variant="outline" className="text-[10px]">Cơ bản</Badge>
              </div>
              <p className="text-muted-foreground">Lặp lại chính xác câu tiếng Nhật mẫu với nhịp điệu và ngữ điệu tự nhiên.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 1: Thay thế (Substitute)</span>
                <Badge variant="outline" className="text-[10px]">Biến số</Badge>
              </div>
              <p className="text-muted-foreground">Giữ nguyên khung mẫu câu, chỉ thay thế từ vựng mới (thời gian, địa điểm, đối tượng).</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 2: Hoàn thành câu (Complete)</span>
                <Badge variant="outline" className="text-[10px]">Điền tiếp</Badge>
              </div>
              <p className="text-muted-foreground">Nhận vế đầu của câu mồi và tự phát ngôn vế sau một cách hợp lý.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 3: 1 Câu hoàn chỉnh (One Sentence)</span>
                <Badge variant="outline" className="text-[10px]">Ngăn câu cụt</Badge>
              </div>
              <p className="text-muted-foreground">Tuyệt đối không chỉ nói từ đơn (VD: không chỉ nói `映画`), phải nói trọn vẹn 1 câu.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 4: Mở rộng (Expand)</span>
                <Badge variant="outline" className="text-[10px]">2 câu liên kết</Badge>
              </div>
              <p className="text-muted-foreground">Thêm 1 chiều thông tin mới (thêm ai, ở đâu, cảm xúc thế nào) để nối thành 2 câu.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 5: Đưa lý do (Reason)</span>
                <Badge variant="outline" className="text-[10px]">Từ nối</Badge>
              </div>
              <p className="text-muted-foreground">Bắt buộc kèm lý do giải thích bằng `〜から / 〜ので / なぜなら`.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 6: Đưa ví dụ (Example)</span>
                <Badge variant="outline" className="text-[10px]">Minh họa</Badge>
              </div>
              <p className="text-muted-foreground">Nêu ví dụ thực tế bằng `例えば / 例として / 〜など`.</p>
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary">Stage 7–10: Tự do & Độc lập</span>
                <Badge variant="outline" className="text-[10px]">20s – 60s</Badge>
              </div>
              <p className="text-muted-foreground">Phát ngôn tự lập theo chuỗi câu hỏi đào sâu (Follow-up) mà không cần gợi ý giàn giáo.</p>
            </div>
          </div>
        </div>

        {/* 2. Bộ từ nối mở rộng câu chuẩn Nhật */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-500" />
            <h3 className="text-sm font-bold text-foreground">Bộ Từ Nối Cứu Cánh (Transition Connectors)</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-card border border-border space-y-1.5">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" /> Giải thích lý do (Why)
              </span>
              <ul className="space-y-1 text-muted-foreground font-jp">
                <li>• <strong>〜からです / 〜から：</strong> Vì...</li>
                <li>• <strong>〜ので、〜：</strong> Do... nên...</li>
                <li>• <strong>なぜなら、〜からです：</strong> Bởi vì là vì...</li>
                <li>• <strong>その理由は〜：</strong> Lý do của việc đó là...</li>
              </ul>
            </div>

            <div className="p-3 rounded-xl bg-card border border-border space-y-1.5">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-sky-500" /> Nêu ví dụ minh họa (Example)
              </span>
              <ul className="space-y-1 text-muted-foreground font-jp">
                <li>• <strong>例えば、〜：</strong> Ví dụ như là...</li>
                <li>• <strong>〜などが挙げられます：</strong> Có thể kể đến như...</li>
                <li>• <strong>具体的に言うと、〜：</strong> Cụ thể mà nói thì...</li>
              </ul>
            </div>

            <div className="p-3 rounded-xl bg-card border border-border space-y-1.5">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-purple-500" /> Nêu cảm xúc & Ý kiến (Opinion)
              </span>
              <ul className="space-y-1 text-muted-foreground font-jp">
                <li>• <strong>〜と思います：</strong> Tôi nghĩ là...</li>
                <li>• <strong>〜と感じました：</strong> Tôi đã cảm thấy là...</li>
                <li>• <strong>〜てよかったです：</strong> Thật tốt vì đã...</li>
              </ul>
            </div>

            <div className="p-3 rounded-xl bg-card border border-border space-y-1.5">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> Nối ý chuyển tiếp (Transition)
              </span>
              <ul className="space-y-1 text-muted-foreground font-jp">
                <li>• <strong>そして / それに：</strong> Và / Hơn nữa</li>
                <li>• <strong>でも / しかし：</strong> Nhưng / Tuy nhiên</li>
                <li>• <strong>その結果、〜：</strong> Kết quả là...</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Quy tắc vàng */}
        <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 text-xs space-y-1.5">
          <span className="font-bold text-primary flex items-center gap-1.5">
            <Sparkles className="h-4 w-4" /> Quy tắc vàng trong Mode 6:
          </span>
          <p className="text-muted-foreground leading-relaxed">
            Đừng sợ sai ngữ pháp nhỏ! Mục tiêu của bạn là <strong>biến từ ngữ trong đầu thành câu nói trọn vẹn</strong>. Khi gặp câu hỏi, hãy luôn tự nhủ: <em>"Nói xong 1 câu, hãy thêm 1 lý do hoặc 1 ví dụ!"</em>
          </p>
        </div>
      </div>

      <div className="flex justify-end pt-4 border-t border-border mt-4">
        <Button variant="primary" size="sm" onClick={onClose}>
          Đã hiểu, tiếp tục luyện tập
        </Button>
      </div>
    </Modal>
  );
}
