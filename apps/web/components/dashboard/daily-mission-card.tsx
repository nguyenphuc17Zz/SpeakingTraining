import React from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sparkles, Trophy, ArrowRight, Clock } from "lucide-react";

export function DailyMissionCard() {
  return (
    <Card variant="washi" className="relative overflow-hidden border-primary/15 washi-texture">
      {/* Subtle Japanese watermarking / decorative element */}
      <div className="absolute top-2 right-4 text-7xl font-jp font-black text-primary/5 select-none pointer-events-none">
        任務
      </div>

      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="fuji" size="sm">
                <Sparkles className="h-3 w-3" />
                <span>今日のデイリーミッション (Today's Quest)</span>
              </Badge>
              <Badge variant="amber" size="sm">
                <Trophy className="h-3 w-3" />
                <span>+120 XP</span>
              </Badge>
            </div>

            <h2 className="text-xl font-bold text-foreground tracking-tight">
              Yuki Senpaiと週末の予定について話そう！
            </h2>
            <p className="text-xs text-foreground leading-relaxed">
              Talk with Yuki Senpai about your upcoming weekend plans. Practice using 〜たい (desires) and 〜に行く (going to do) sentence structures for 5 minutes.
            </p>

            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-primary" />
                <span>Est. 5-8 mins</span>
              </span>
              <span>•</span>
              <span className="text-foreground font-medium">Difficulty: N3 Practical</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <Link href="/speaking">
              <Button variant="primary" size="lg" className="w-full sm:w-auto">
                <span>ミッション開始 (Start Mission)</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
