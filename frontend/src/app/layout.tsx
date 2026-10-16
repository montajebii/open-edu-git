import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "OpenEdu Git",
  description: "پلتفرم آموزشی گیت‌محور برای جزوه‌های درسی ایران",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        {children}
      </body>
    </html>
  );
}