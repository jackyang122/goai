"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Flame,
  GraduationCap,
  LayoutDashboard,
  MessageSquare,
  Moon,
  Sparkles,
  Sun,
  Target,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { FEATURES, type FeatureKey } from "@/lib/features";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/components/theme-provider";
import { IS_MOCK } from "@/lib/api";

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  feature?: FeatureKey; // gate behind a flag in lib/features.ts
};

const NAV: readonly NavItem[] = [
  { href: "/", label: "仪表盘", icon: LayoutDashboard },
  { href: "/learn", label: "学习", icon: BookOpen },
  { href: "/practice", label: "练习", icon: Target, feature: "practice" },
  { href: "/home", label: "对话", icon: MessageSquare },
  { href: "/me", label: "我的", icon: User },
];

// Feature-gated navigation: entries whose flag is off are hidden in both the
// desktop sidebar and the mobile header.
const VISIBLE_NAV = NAV.filter((item) => !item.feature || FEATURES[item.feature]);

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar (desktop) */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card/40 md:flex">
        <div className="flex h-16 items-center gap-2 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">Personal Learning OS</div>
            <div className="text-[11px] text-muted-foreground">学习型操作系统</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-2">
          {VISIBLE_NAV.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className="h-[18px] w-[18px]" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border p-3">
          <div className="flex items-center gap-3 rounded-md px-2 py-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/15 text-accent">
              <User className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1 leading-tight">
              <div className="truncate text-sm font-medium">同学</div>
              <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <Flame className="h-3 w-3 text-warning" /> 连续 4 天
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:px-8">
          {/* Mobile nav */}
          <div className="flex items-center gap-2 overflow-x-auto md:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div className="flex gap-1">
              {VISIBLE_NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-md p-2",
                    isActive(pathname, item.href) ? "bg-secondary" : "text-muted-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                </Link>
              ))}
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              aria-label="切换主题"
            >
              {theme === "light" ? <Moon className="h-[18px] w-[18px]" /> : <Sun className="h-[18px] w-[18px]" />}
            </Button>
            <Link href="/home">
              <Button variant="accent" size="sm" className="gap-1.5">
                <Sparkles className="h-4 w-4" />
                问 AI
              </Button>
            </Link>
          </div>
        </header>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
