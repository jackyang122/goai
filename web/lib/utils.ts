import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes with conditional logic (shadcn convention). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format minutes as "Xh Ym" / "Ym". */
export function formatMinutes(min: number): string {
  if (min < 60) return `${min}m`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

/** Clamp + format a 0..1 mastery level to a percentage label. */
export function masteryLabel(level: number): string {
  return `${Math.round(Math.max(0, Math.min(1, level)) * 100)}%`;
}

/** Map a 0..1 mastery level to a semantic tone. */
export function masteryTone(level: number): "success" | "warning" | "danger" {
  if (level >= 0.75) return "success";
  if (level >= 0.5) return "warning";
  return "danger";
}

/** Simulate network latency for the mock backend (keeps the demo feeling real). */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
