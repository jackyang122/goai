/**
 * Feature flags — gate UI/features that are not yet released.
 *
 * Each flag defaults to `false` (hidden everywhere) and is flipped to `true` to
 * surface that feature across the app (nav entries + their routes). Centralised
 * here so "coming soon" features can be enabled in exactly one place as they ship.
 *
 * To open a feature: set its flag to `true`. No other change needed — the nav
 * entry reappears and the route serves its real content.
 */
export const FEATURES = {
  /** 智能测验 / 练习 — 暂时隐藏，待功能完善后开放。 */
  practice: false,
} as const;

export type FeatureKey = keyof typeof FEATURES;
