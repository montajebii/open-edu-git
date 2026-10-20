"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";


export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [unverified, setUnverified] = useState(false);
  const [resendState, setResendState] = useState<"idle" | "sending" | "sent">("idle");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setUnverified(false);

    try {
      // Tokens come back as httpOnly cookies; nothing is stored in JS.
      const response = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        if (response.status === 403 && data.detail === "Email address is not verified") {
          setUnverified(true);
          return;
        }
        throw new Error(data.detail || "Login failed");
      }

      router.push("/pamphlets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendState("sending");
    try {
      const response = await apiFetch("/api/v1/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setResendState(response.ok ? "sent" : "idle");
    } catch {
      setResendState("idle");
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md card">
        <h1>ورود</h1>
        {error && <div className="error">{error}</div>}
        {unverified && (
          <div className="error">
            <p className="mb-2">ایمیل شما هنوز تأیید نشده است.</p>
            {resendState === "sent" ? (
              <p>ایمیل تأیید جدیدی ارسال شد. لطفاً صندوق ورودی خود را بررسی کنید.</p>
            ) : (
              <button type="button" onClick={handleResend} disabled={resendState === "sending"}>
                {resendState === "sending" ? "در حال ارسال..." : "ارسال مجدد ایمیل تأیید"}
              </button>
            )}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email">ایمیل</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="password">رمز عبور</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
          >
            {loading ? "در حال ورود..." : "ورود"}
          </button>
        </form>
        <div className="mt-6">
          <p>
            حساب کاربری ندارید؟ <a href="/register" className="text-blue-600 underline">ثبت‌نام کنید</a>
          </p>
        </div>
      </div>
    </main>
  );
}
