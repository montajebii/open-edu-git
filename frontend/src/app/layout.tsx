import type { Metadata } from "next";
import { Vazirmatn } from "next/font/google";
import "./styles/globals.css";

const vazirmatn = Vazirmatn({ subsets: ["arabic"] });

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
      <body className={vazirmatn.className}>
        {children}
      </body>
    </html>
  );
}