"use client";

import React from "react";
import { RefreshCw, CheckCircle2, Clock, Play, Flame } from "lucide-react";
import { LearningItem } from "@/types/learning";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface ReviewQueueCardProps {
  dueReviews: LearningItem[];
  onStartReview: (itemId: string) => void;
}

export const ReviewQueueCard: React.FC<ReviewQueueCardProps> = ({ dueReviews, onStartReview }) => {
  return (
    <Card className="border border-border bg-card/80 p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-indigo-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Hàng đợi ôn tập định kỳ <span className="text-xs font-normal text-muted-foreground">(Spaced Reviews)</span>
          </h3>
        </div>
        <Badge variant="outline" className="text-xs border-indigo-500/30 text-indigo-300 bg-indigo-950/40">
          {dueReviews.length} mục cần ôn
        </Badge>
      </div>

      {dueReviews.length === 0 ? (
        <div className="py-6 text-center text-muted-foreground space-y-2 bg-background/40 rounded-xl border border-border/60 p-4">
          <CheckCircle2 className="w-7 h-7 text-emerald-400 mx-auto" />
          <p className="text-xs font-medium text-foreground">Tất cả kiến thức đã được ôn tập đúng hạn!</p>
          <p className="text-[11px] text-muted-foreground">Hệ thống sẽ tự động nhắc lịch khi đến chu kỳ ghi nhớ tiếp theo.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {dueReviews.map((item) => (
            <div
              key={item.id}
              className="p-3 rounded-xl bg-background/80 border border-border/80 hover:border-border flex items-center justify-between gap-3 transition-all"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] uppercase bg-card border-border text-muted-foreground">
                    {item.item_type}
                  </Badge>
                  <h4 className="text-sm font-semibold text-white">{item.title}</h4>
                </div>

                <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1 text-amber-400/90 font-medium">
                    <Flame className="w-3 h-3 text-amber-400" /> Chuỗi ôn tập: {item.review_streak} lần
                  </span>
                  <span>•</span>
                  <span>Độ thuần thục: {Math.round(item.overall_mastery * 100)}%</span>
                </div>
              </div>

              <Button
                size="sm"
                onClick={() => onStartReview(item.id)}
                className="bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs px-3 py-1.5 h-auto shrink-0 shadow"
              >
                Ôn ngay <Play className="w-3 h-3 ml-1 fill-current" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
