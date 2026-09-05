"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { TutivraSession, DEFAULT_SESSION } from "@/lib/session";

interface SessionContextValue {
  session: TutivraSession;
  update: (partial: Partial<TutivraSession>) => void;
  reset: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<TutivraSession>(DEFAULT_SESSION);

  const update = useCallback((partial: Partial<TutivraSession>) => {
    setSession((prev) => ({ ...prev, ...partial }));
  }, []);

  const reset = useCallback(() => {
    setSession(DEFAULT_SESSION);
  }, []);

  return (
    <SessionContext.Provider value={{ session, update, reset }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside <SessionProvider>");
  return ctx;
}
