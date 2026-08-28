"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Utensils,
  ShoppingBag,
  Train,
  HeartPulse,
  Briefcase,
  Hotel,
  Volume2,
  Search,
} from "lucide-react";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsCheatsheetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SITUATIONAL_CHEAT_DATA = [
  {
    category: "food",
    title: "Ẩm Thực & Quán Nhậu (飲食・居酒屋)",
    icon: <Utensils className="h-4 w-4 text-amber-500" />,
    items: [
      { jp: "2人ですが、入れますか？", vi: "Chúng tôi có 2 người, còn bàn vào được không ạ?", usage: "Vào quán hỏi bàn" },
      { jp: "禁煙席をお願いします。", vi: "Cho tôi xin bàn không hút thuốc ạ.", usage: "Yêu cầu bàn không khói" },
      { jp: "生ビールをふたつと枝豆をお願いします。", vi: "Cho tôi 2 bia tươi và đậu nành edamame.", usage: "Gọi món mở đầu" },
      { jp: "おすすめは何ですか？", vi: "Quán có món nào gợi ý hôm nay không ạ?", usage: "Hỏi món ngon" },
      { jp: "別々でお会計をお願いできますか？", vi: "Tính tiền riêng từng người (chia hóa đơn) được không ạ?", usage: "Thanh toán betsu-betsu" },
    ],
  },
  {
    category: "retail",
    title: "Mua Sắm & Konbini (買い物・コンビニ)",
    icon: <ShoppingBag className="h-4 w-4 text-emerald-500" />,
    items: [
      { jp: "袋は大丈夫です（結構です）。", vi: "Tôi không cần lấy túi nilon đâu ạ.", usage: "Từ chối túi" },
      { jp: "温めていただけますか？", vi: "Làm nóng cơm hộp bento giúp tôi được không ạ?", usage: "Yêu cầu quay lò vi sóng" },
      { jp: "Suica（電子マネー）で払います。", vi: "Tôi xin phép thanh toán bằng thẻ Suica.", usage: "Chọn phương thức thanh toán" },
      { jp: "領収書をいただけますか？", vi: "Cho tôi xin hóa đơn thanh toán với ạ.", usage: "Xin hóa đơn" },
      { jp: "これはどこにありますか？", vi: "Món đồ này đang được để ở quầy nào vậy ạ?", usage: "Hỏi tìm hàng hóa" },
    ],
  },
  {
    category: "transportation",
    title: "Giao Thông & Nhà Ga (交通・駅・空港)",
    icon: <Train className="h-4 w-4 text-sky-500" />,
    items: [
      { jp: "新大阪までの新幹線の指定席を1枚お願いします。", vi: "Cho tôi 1 vé Shinkansen ghế chỉ định đi Shin-Osaka.", usage: "Mua vé tàu cao tốc" },
      { jp: "新宿へ行くには何番線に乗ればいいですか？", vi: "Đi Shinjuku thì lên tàu ở đường ray số mấy ạ?", usage: "Hỏi đường ray" },
      { jp: "この電車は東京駅に止まりますか？", vi: "Chuyến tàu này có dừng ở ga Tokyo không ạ?", usage: "Xác nhận điểm dừng" },
      { jp: "東京駅までお願いします。", vi: "Bác tài làm ơn chở tôi đến ga Tokyo ạ.", usage: "Đi taxi" },
    ],
  },
  {
    category: "healthcare",
    title: "Y Tế & Hiệu Thuốc & Khẩn Cấp (医療・薬局・緊急)",
    icon: <HeartPulse className="h-4 w-4 text-rose-500" />,
    items: [
      { jp: "昨日から熱があって、頭も痛いです。", vi: "Tôi bị sốt từ hôm qua và đầu cũng rất đau.", usage: "Mô tả triệu chứng bệnh" },
      { jp: "風邪薬とトローチをください。", vi: "Cho tôi thuốc cảm cúm và kẹo ngậm viêm họng.", usage: "Mua thuốc tại quầy" },
      { jp: "電車に財布を忘れてしまったのですが。", vi: "Tôi lỡ để quên ví tiền trên tàu rồi ạ.", usage: "Báo mất đồ tại Kouban" },
      { jp: "保険証を持っています。", vi: "Tôi có mang theo thẻ bảo hiểm y tế ạ.", usage: "Tiếp tân phòng khám" },
    ],
  },
  {
    category: "workplace",
    title: "Công Sở & Đàm Phán (ビジネス・職場)",
    icon: <Briefcase className="h-4 w-4 text-purple-500" />,
    items: [
      { jp: "初めまして、〇〇社の田中と申します。", vi: "Rất hân hạnh được gặp, tôi là Tanaka đến từ công ty OO.", usage: "Trao danh thiếp Meishi" },
      { jp: "本日はお時間をいただき、ありがとうございます。", vi: "Cảm ơn quý vị đã dành thời gian quý báu hôm nay.", usage: "Mở đầu cuộc họp" },
      { jp: "プロジェクトの進捗についてご報告いたします。", vi: "Tôi xin phép báo cáo tiến độ dự án (Hou-Ren-So).", usage: "Báo cáo công việc" },
      { jp: "体調不良のため、本日はお休みをいただきたく存じます。", vi: "Vì lý do sức khỏe, hôm nay tôi xin phép được nghỉ phép ạ.", usage: "Xin nghỉ ốm lịch sự" },
    ],
  },
  {
    category: "travel",
    title: "Khách Sạn & Du Lịch (ホテル・観光・旅行)",
    icon: <Hotel className="h-4 w-4 text-cyan-500" />,
    items: [
      { jp: "チェックインをお願いします。予約した田中です。", vi: "Cho tôi làm thủ tục nhận phòng. Tôi là Tanaka đã đặt trước.", usage: "Check-in khách sạn" },
      { jp: "チェックイン前ですが、荷物を預かっていただけますか？", vi: "Chưa tới giờ nhận phòng, tôi gửi hành lý trước được không?", usage: "Gửi hành lý" },
      { jp: "この近くでおすすめのラーメン屋さんはありますか？", vi: "Quanh đây có quán ramen nào ngon gợi ý không ạ?", usage: "Hỏi địa điểm ăn uống" },
      { jp: "タクシーを1台呼んでいただけますか？", vi: "Làm ơn gọi giúp tôi 1 chiếc taxi được không ạ?", usage: "Nhờ lễ tân gọi taxi" },
    ],
  },
];

export function SituationsCheatsheetModal({ isOpen, onClose }: SituationsCheatsheetModalProps) {
  const [activeCat, setActiveCat] = useState("food");
  const [search, setSearch] = useState("");

  const currentSection = SITUATIONAL_CHEAT_DATA.find((s) => s.category === activeCat);

  const filteredItems = currentSection?.items.filter(
    (item) =>
      item.jp.toLowerCase().includes(search.toLowerCase()) ||
      item.vi.toLowerCase().includes(search.toLowerCase()) ||
      item.usage.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Sổ Tay 100+ Mẫu Câu Giao Tiếp Thực Chiến"
      description="Tra cứu các mẫu câu giao tiếp tiếng Nhật tự nhiên phân loại theo 6 bối cảnh đời sống Nhật Bản"
      className="max-w-3xl"
    >
      <div className="space-y-4 pt-2">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm mẫu câu tiếng Nhật hoặc tiếng Việt..."
            className="w-full bg-background border border-border rounded-xl pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-primary placeholder:text-muted-foreground"
          />
        </div>

        {/* 6 Category Tabs */}
        <div className="flex items-center p-1 rounded-2xl bg-muted/60 border border-border overflow-x-auto scrollbar-thin">
          {SITUATIONAL_CHEAT_DATA.map((cat) => (
            <button
              key={cat.category}
              onClick={() => {
                soundFX.playFurin();
                setActiveCat(cat.category);
              }}
              className={cn(
                "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
                activeCat === cat.category
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {cat.icon}
              <span>{cat.title.split(" ")[0]}</span>
            </button>
          ))}
        </div>

        {/* Items List */}
        <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
          {filteredItems?.map((item, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl border border-border/70 bg-card hover:border-primary/40 transition-all flex items-center justify-between gap-3 shadow-2xs"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" size="sm" className="text-[10px] font-bold">
                    {item.usage}
                  </Badge>
                </div>
                <div className="text-sm font-bold font-jp text-foreground">{item.jp}</div>
                <div className="text-xs text-muted-foreground">{item.vi}</div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  speakJapaneseText(item.jp, { rate: 1.0 });
                }}
                className="h-8 w-8 p-0 shrink-0 text-primary hover:bg-primary/10 rounded-xl"
                title="Phát âm mẫu câu này"
              >
                <Volume2 className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {filteredItems?.length === 0 && (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Không tìm thấy mẫu câu phù hợp trong chuyên mục này.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="pt-3 border-t border-border flex justify-end">
          <Button
            size="sm"
            onClick={onClose}
            className="text-xs font-bold"
          >
            Đóng Sổ Tay
          </Button>
        </div>
      </div>
    </Modal>
  );
}
