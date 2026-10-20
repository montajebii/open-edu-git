"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [message, setMessage] = useState("در حال تأیید ایمیل...");
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    const verifyEmail = async () => {
      try {
        const response = await apiFetch(
          `/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "تأیید ایمیل ناموفق بود.");
        }

        if (!cancelled) {
          setMessage("ایمیل شما با موفقیت تأیید شد!");
          setTimeout(() => router.push("/login"), 3000);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تأیید ایمیل ناموفق بود.");
        }
      }
    };

    verifyEmail();
    return () => {
      cancelled = true;
    };
  }, [token, router]);

  const shownError = error || (token ? "" : "توکن تأیید یافت نشد.");

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md card text-center">
        {shownError ? (
          <>
            <h1 className="text-red-600">خطا</h1>
            <p className="mb-8">{shownError}</p>
            <a
              href="/login"
              className="button"
            >
              بازگشت به ورود
            </a>
          </>
        ) : (
          <>
            <h1>تأیید ایمیل</h1>
            <p className="mb-8">{message}</p>
          </>
        )}
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center p-8">در حال تأیید ایمیل...</div>}>
      <VerifyEmailInner />
    </Suspense>
  );
}
