"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Mic, Zap, Crown, Music, Compass, GraduationCap, Swords, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/dashboard", label: "Trang chủ", icon: LayoutDashboard },
  { href: "/speaking", label: "Hội thoại", icon: Mic },
  { href: "/reflex", label: "Phản xạ", icon: Zap },
  { href: "/keigo", label: "Kính ngữ", icon: Crown },
  { href: "/pitch", label: "Cao độ", icon: Music },
  { href: "/situations", label: "Tình huống", icon: Compass },
  { href: "/learning", label: "Học tập", icon: GraduationCap },
  { href: "/game", label: "Dojo", icon: Swords },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t border-border bg-card/95 backdrop-blur-md supports-[backdrop-filter]:bg-card/80 pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center justify-around px-1 py-1.5">
        {TABS.map((t) => {
          const Icon = t.icon;
          const active =
            t.href === "/speaking"
              ? pathname === "/speaking" || (pathname.startsWith("/speaking/") && !["/speaking/speech", "/speaking/reflex", "/speaking/pronunciation"].some((p) => pathname.startsWith(p)))
              : pathname === t.href || (t.href !== "/dashboard" && pathname.startsWith(t.href)) || (t.href === "/game" && ["/quests", "/skills", "/bosses", "/achievements", "/unlocks"].some((p) => pathname.startsWith(p)));
          return (
            <Link
              key={t.href}
              href={t.href}
              prefetch={true}
              className={cn(
                "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl min-w-[64px] transition-colors",
                active ? "text-primary bg-primary/10" : "text-muted-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5", active && "text-primary")} />
              <span className="text-[11px] font-medium leading-none">{t.label}</span>
            </Link>
          );
        })}
        <Link
          href="/settings"
          prefetch={true}
          className={cn(
            "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl min-w-[64px]",
            pathname.startsWith("/settings") ? "text-primary bg-primary/10" : "text-muted-foreground"
          )}
        >
          <Settings className="h-5 w-5" />
          <span className="text-[11px] font-medium leading-none">Cài đặt</span>
        </Link>
      </div>
    </nav>
  );
}
