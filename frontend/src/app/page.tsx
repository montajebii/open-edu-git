export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">OpenEdu Git</h1>
        <p className="text-lg mb-8">
          پلتفرم آموزشی گیت‌محور برای جزوه‌های درسی ایران.
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            ورود
          </a>
          <a
            href="/register"
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            ثبت‌نام
          </a>
        </div>
      </div>
    </main>
  );
}