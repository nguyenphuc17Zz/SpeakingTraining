import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { RouteProgressBar } from "@/components/layout/RouteProgressBar";
import { ThemeProvider } from "@/components/theme-provider";
import { GlobalToast } from "@/components/ui/global-toast";
import { VocabularyLookupProvider } from "@/features/vocabulary-lookup";

// Fonts loaded via system fallback to avoid build-time Google fetch in offline env.
// CSS variables --font-jp / --font-display fallback to Noto Sans JP stack defined in globals.css
const zenMaru = { variable: "" } as const;
const notoSansJP = { variable: "" } as const;
const shippori = { variable: "" } as const;

export const metadata: Metadata = {
  title: "Hanasu AI — Luyện nói tiếng Nhật cùng AI",
  description:
    "Nền tảng luyện nói tiếng Nhật với hội thoại thời gian thực, Shadowing YouTube và lộ trình cá nhân hóa.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <ThemeProvider>
          <Suspense fallback={null}>
            <RouteProgressBar />
          </Suspense>
          <VocabularyLookupProvider>
            <AppShell>{children}</AppShell>
            <GlobalToast />
          </VocabularyLookupProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
