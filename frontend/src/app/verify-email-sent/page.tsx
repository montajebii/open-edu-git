export default function VerifyEmailSentPage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md text-center">
        <h1 className="text-3xl font-bold mb-6">ایمیل تأیید ارسال شد</h1>
        <p className="mb-4">
          یک ایمیل حاوی لینک تأیید به آدرس شما ارسال شده است.
        </p>
        <p className="mb-8">
          لطفاً صندوق ورودی خود را بررسی کنید و روی لینک کلیک کنید تا ایمیل شما تأیید شود.
        </p>
        <a
          href="/login"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          بازگشت به ورود
        </a>
      </div>
    </main>
  );
}