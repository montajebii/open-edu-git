export default function VerifyEmailSentPage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md card text-center">
        <h1>ایمیل تأیید ارسال شد</h1>
        <p className="mb-4">
          یک ایمیل حاوی لینک تأیید به آدرس شما ارسال شده است.
        </p>
        <p className="mb-8">
          لطفاً صندوق ورودی خود را بررسی کنید و روی لینک کلیک کنید تا ایمیل شما تأیید شود.
        </p>
        <a
          href="/login"
          className="button"
        >
          بازگشت به ورود
        </a>
      </div>
    </main>
  );
}