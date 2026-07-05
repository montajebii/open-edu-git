"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";


export default function VerifyEmailPage({
  searchParams,
}: {
  searchParams: { token?: string }
}) {
  const [message, setMessage] = useState("در حال تأیید ایمیل...");
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!searchParams.token) {
      setError("توکن تأیید یافت نشد.");
      return;
    }
    
    const verifyEmail = async () => {
      try {
        const response = await fetch(
          `http://backend:8000/api/v1/auth/verify-email?token=${searchParams.token}`
        );
        
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "تأیید ایمیل ناموفق بود.");
        }
        
        setMessage("ایمیل شما با موفقیت تأیید شد!");
        setTimeout(() => router.push("/login"), 3000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "تأیید ایمیل ناموفق بود.");
      }
    };
    
    verifyEmail();
  }, [searchParams.token, router]);

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md card text-center">
        {error ? (
          <>
            <h1 className="text-red-600">خطا</h1>
            <p className="mb-8">{error}</p>
            <a
              href="/register"
              className="button"
            >
              ارسال مجدد ایمیل تأیید
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