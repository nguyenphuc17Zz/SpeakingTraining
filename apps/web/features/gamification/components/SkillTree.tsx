"use client";

import React, { useState } from "react";
import Link from "next/link";
import { SkillTreeOverviewDTO, SkillNodeDTO } from "../types/game";
import { SkillNode } from "./SkillNode";
import { MessageSquare, Sparkles, ArrowRight, ShieldAlert, CheckCircle2, Mic, Zap } from "lucide-react";

interface SkillTreeProps {
  skillTree: SkillTreeOverviewDTO;
}

export const SkillTree: React.FC<SkillTreeProps> = ({ skillTree }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [activeNode, setActiveNode] = useState<SkillNodeDTO | null>(null);

  const filteredNodes =
    selectedCategory === "all"
      ? skillTree.nodes
      : skillTree.nodes.filter((n) => n.category === selectedCategory);

  const getCategoryLabel = (cat: string) => {
    switch (cat) {
      case "fluency":
        return "🗣 Fluency (流暢さ・瞬発力)";
      case "naturalness":
        return "🌸 Naturalness (自然さ・敬語)";
      case "grammar":
        return "📜 Grammar (文法・助詞)";
      case "pronunciation":
        return "🎯 Pronunciation (発音・音調)";
      default:
        return "🌟 All Skills (全スキル)";
    }
  };

  return (
    <div className="space-y-6">
      {/* Category Tab Bar */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl bg-card/80 border border-border">
        <button
          onClick={() => setSelectedCategory("all")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            selectedCategory === "all"
              ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All Branches (全体)
        </button>
        {skillTree.categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedCategory === cat
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {getCategoryLabel(cat)}
          </button>
        ))}
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 p-6 rounded-3xl bg-card/40 border border-border/80 backdrop-blur-md">
        {filteredNodes.map((node) => (
          <div key={node.key} className="flex justify-center">
            <SkillNode
              node={node}
              onClick={(n) => setActiveNode(n)}
              isSelected={activeNode?.key === node.key}
            />
          </div>
        ))}
      </div>

      {/* Node Detail Inspector Modal / Drawer */}
      {activeNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-lg p-6 rounded-3xl bg-card border border-border shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-black text-foreground font-jp">
                    {activeNode.name}
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/20 text-primary border border-primary/30 uppercase tracking-wider">
                    {activeNode.category}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{activeNode.description}</p>
              </div>
              <button
                onClick={() => setActiveNode(null)}
                className="w-8 h-8 rounded-full bg-muted text-muted-foreground hover:text-white flex items-center justify-center text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Current Mastery Metric */}
            <div className="p-4 rounded-2xl bg-background/60 border border-border space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                <span>Learning Engine Mastery</span>
                <span className="font-mono text-primary font-bold">
                  {Math.round(activeNode.current_mastery * 100)}%
                </span>
              </div>
              <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-aizome-500"
                  style={{ width: `${Math.round(activeNode.current_mastery * 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                Mastery is synthesized directly from your real spoken responses and exercise evaluations.
              </p>
            </div>

            {/* Linked Active Learning Items */}
            {activeNode.linked_learning_items.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                  Linked Targets (関連する学習項目)
                </h4>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {activeNode.linked_learning_items.map((item) => (
                    <div
                      key={item.key}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-background/40 border border-border/60 text-xs"
                    >
                      <span className="font-medium text-foreground">{item.title}</span>
                      <span className="font-mono font-bold text-muted-foreground text-[11px]">
                        {Math.round(item.mastery * 100)}% ({item.lifecycle})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Action */}
            <div className="pt-2 flex items-center gap-3">
              <Link href="/learning" className="flex-1">
                <button className="w-full py-2.5 rounded-xl bg-gradient-to-r from-primary to-aizome-600 hover:opacity-90 text-primary-foreground text-xs font-bold flex items-center justify-center gap-1.5 shadow-md shadow-primary/20">
                  <Zap className="w-4 h-4" />
                  <span>Train This Skill (特訓を開始)</span>
                </button>
              </Link>
              <button
                onClick={() => setActiveNode(null)}
                className="px-4 py-2.5 rounded-xl bg-muted hover:bg-slate-700 text-foreground text-xs font-bold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
