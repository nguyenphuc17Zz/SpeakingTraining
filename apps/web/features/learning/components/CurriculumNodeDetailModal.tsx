"use client";

import React from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Play,
  CheckCircle2,
  BookOpen,
  Sparkles,
  ArrowRight,
  Clock,
  RotateCcw,
} from "lucide-react";
import { CurriculumNode } from "@/types/learning";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface CurriculumNodeDetailModalProps {
  node: CurriculumNode | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleComplete: (nodeId: string, isCompleted: boolean) => Promise<void>;
}

export function CurriculumNodeDetailModal({
  node,
  isOpen,
  onClose,
  onToggleComplete,
}: CurriculumNodeDetailModalProps) {
  if (!node) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={node.title}
      description={`Mục tiêu rèn luyện tại phòng: ${node.mode_label}`}
      className="max-w-xl"
    >
      <div className="space-y-5 pt-2">
        {/* Header Badges */}
        <div className="flex items-center gap-2">
          <Badge variant="matcha" size="sm" className="font-bold">
            {node.mode_label}
          </Badge>
          <Badge variant="outline" size="sm" className="font-mono text-[10px]">
            Độ khó: {node.difficulty}
          </Badge>
          <span className="text-xs text-muted-foreground font-mono">
            Thời lượng ước tính: {node.estimated_minutes} phút
          </span>
        </div>

        {/* Description Box */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
          <div className="text-xs font-bold text-foreground">Mục Tiêu & Nội Dung Bài Học:</div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {node.description}
          </p>
        </div>

        {/* Key Linguistic Patterns */}
        {node.key_patterns && node.key_patterns.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-bold text-foreground">Các Mẫu Trọng Điểm Cần Nắm:</div>
            <div className="flex flex-wrap gap-1.5">
              {node.key_patterns.map((pat, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-xl bg-card border border-primary/30 text-primary text-xs font-jp font-bold shadow-2xs"
                >
                  {pat}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="pt-3 border-t border-border flex flex-wrap items-center justify-between gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              soundFX.playFurin();
              await onToggleComplete(node.id, !node.is_completed);
              onClose();
            }}
            className="text-xs font-bold gap-1.5 rounded-xl"
          >
            <CheckCircle2 className={cn("h-4 w-4", node.is_completed ? "text-emerald-500" : "text-muted-foreground")} />
            <span>{node.is_completed ? "Đánh dấu chưa học" : "Đánh dấu đã hoàn thành"}</span>
          </Button>

          <Link href={node.target_mode || "/speaking"} onClick={onClose}>
            <Button
              variant="akane"
              size="sm"
              onClick={() => soundFX.playKatana()}
              className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shadow-md"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Vào Học Bài Này Ngay ({node.mode_label})</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </div>
    </Modal>
  );
}
