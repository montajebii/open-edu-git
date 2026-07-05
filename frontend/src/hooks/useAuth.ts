"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";


export const useAuth = () => {
  const [token, setToken] = useState<string | null>(null);
  const [tokenPayload, setTokenPayload] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const accessToken = localStorage.getItem("access_token");
    setToken(accessToken);
    
    if (accessToken) {
      try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        setTokenPayload(payload);
      } catch {
        setTokenPayload(null);
      }
    }
    setLoading(false);
  }, []);

  const login = (accessToken: string, refreshToken: string) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    setToken(accessToken);
    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      setTokenPayload(payload);
    } catch {
      setTokenPayload(null);
    }
    router.push("/pamphlets");
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setTokenPayload(null);
    router.push("/login");
  };

  return { token, tokenPayload, loading, login, logout };
};