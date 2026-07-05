export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto card">
        <h1>OpenEdu Git</h1>
        <p className="mb-8">
          پلتفرم آموزشی گیت‌محور برای جزوه‌های درسی ایران.
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="button"
          >
            ورود
          </a>
          <a
            href="/register"
            className="button bg-white text-black dark:bg-black dark:text-white"
          >
            ثبت‌نام
          </a>
        </div>
      </div>
    </main>
  );
}