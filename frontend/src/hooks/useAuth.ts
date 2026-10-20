"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export interface SessionUser {
  id: number;
  email: string;
  full_name: string;
  is_verified: boolean;
}

/**
 * Session state backed by the backend's httpOnly cookies.
 *
 * The server owns the tokens; this hook only asks who is logged in.
 */
export const useAuth = () => {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    const loadSession = async () => {
      try {
        const response = await apiFetch("/api/v1/auth/me");
        if (!cancelled) {
          setUser(response.ok ? ((await response.json()) as SessionUser) : null);
        }
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // The cookies are cleared server-side; ignore network failures and
      // drop the local session state either way.
    }
    setUser(null);
    router.push("/login");
  }, [router]);

  return { user, loading, logout };
};
