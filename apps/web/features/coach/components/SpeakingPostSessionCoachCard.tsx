"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { coachCoreApi } from "../services/coachCoreApi";
import { Sparkles, ArrowRight, RefreshCw } from "lucide-react";

export function SpeakingPostSessionCoachCard({ sessionId }: { sessionId?: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchSummary = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await coachCoreApi.chat({
        message: "Review this just-finished speaking session and give me: 1) one strength, 2) one repeated mistake with example, 3) a 5-min drill to fix it. Evidence-backed, concise.",
        current_route: "/speaking",
        current_session_id: sessionId,
      });
      setData(res);
    } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { fetchSummary(); }, [sessionId]);

  if (!sessionId) return null;
  if (loading) return <div className="p-4 rounded-xl bg-muted border text-xs flex items-center gap-2"><RefreshCw className="w-3 h-3 animate-spin" /> Coach đang tổng kết buổi nói…</div>;
  if (!data) return null;

  return (
    <div className="p-4 rounded-xl bg-card border border-primary/20 shadow-sm space-y-3">
      <div className="flex items-center gap-2">
        <span className="h-7 w-7 rounded-lg bg-primary text-primary-foreground flex items-center justify-center"><Sparkles className="w-4 h-4" /></span>
        <span className="text-sm font-black">Coach tổng kết buổi nói</span>
        <button onClick={fetchSummary} className="ml-auto text-xs px-2 py-1 rounded bg-muted border">Refresh</button>
      </div>
      <p className="text-xs leading-relaxed whitespace-pre-wrap">{data.response}</p>
      {data.recommendations?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.recommendations.slice(0,2).map((rec: any, i: number)=>(
            <Link key={i} href={rec.practice_url || "/speaking"} className="px-3 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold flex items-center gap-1">
              {rec.reason || rec.target} <ArrowRight className="w-3 h-3" />
            </Link>
          ))}
        </div>
      )}
      {data.next_action && (
        <Link href={data.next_action.payload?.exercise_url || data.next_action.payload?.navigate_to || "/speaking"} className="inline-flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white">
          {data.next_action.label || "Bắt đầu luyện bù 5′"} <ArrowRight className="w-3 h-3" />
        </Link>
      )}
    </div>
  );
}
