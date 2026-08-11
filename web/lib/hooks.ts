"use client";

import { useCallback, useEffect, useState } from "react";
import { api, LEARNER_ID } from "@/lib/api";
import type { LearnerState } from "@/lib/api";

/** Loads the current learner's LearnerState once on mount, with refresh. */
export function useLearnerState() {
  const [state, setState] = useState<LearnerState | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setState(await api.getLearnerState(LEARNER_ID));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { state, loading, refresh: load, setState };
}
