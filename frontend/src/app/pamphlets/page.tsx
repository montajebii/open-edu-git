"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

interface Pamphlet {
  id: number;
  title: string;
  grade: string;
  subject: string;
  chapter: string;
  method?: string;
  difficulty?: string;
  is_public: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export default function PamphletsPage() {
  const [pamphlets, setPamphlets] = useState<Pamphlet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [grade, setGrade] = useState("");
  const [subject, setSubject] = useState("");
  const [chapter, setChapter] = useState("");
  const { token } = useAuth();

  useEffect(() => {
    const fetchPamphlets = async () => {
      try {
        const params = new URLSearchParams();
        if (grade) params.append("grade", grade);
        if (subject) params.append("subject", subject);
        if (chapter) params.append("chapter", chapter);

        const response = await fetch(
          `http://localhost:8000/api/v1/pamphlets/?${params.toString()}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }
        );

        if (!response.ok) {
          throw new Error("خطا در دریافت جزوات");
        }

        const data = await response.json();
        setPamphlets(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "خطای ناشناخته");
      } finally {
        setLoading(false);
      }
    };

    fetchPamphlets();
  }, [grade, subject, chapter, token]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">جزوات</h1>
        <Link
          href="/pamphlets/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          آپلود جزوه جدید
        </Link>
      </div>

      <div className="mb-6 flex space-x-4">
        <div>
          <label className="block text-sm font-medium mb-1">پایه</label>
          <input
            type="text"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="p-2 border rounded"
            placeholder="مثال: یازدهم"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">درس</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="p-2 border rounded"
            placeholder="مثال: ریاضی"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">فصل</label>
          <input
            type="text"
            value={chapter}
            onChange={(e) => setChapter(e.target.value)}
            className="p-2 border rounded"
            placeholder="مثال: مشتق"
          />
        </div>
      </div>

      {error && <div className="bg-red-100 text-red-700 p-3 mb-4 rounded">{error}</div>}

      {loading ? (
        <div>در حال بارگذاری...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pamphlets.map((pamphlet) => (
            <div key={pamphlet.id} className="border p-4 rounded shadow">
              <h2 className="text-xl font-bold mb-2">{pamphlet.title}</h2>
              <p className="text-sm text-gray-600 mb-1">
                <strong>پایه:</strong> {pamphlet.grade} | <strong>درس:</strong> {pamphlet.subject} | <strong>فصل:</strong> {pamphlet.chapter}
              </p>
              <p className="text-sm text-gray-600 mb-1">
                <strong>روش:</strong> {pamphlet.method || "-"} | <strong>سطح:</strong> {pamphlet.difficulty || "-"}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                <strong>تگ‌ها:</strong> {pamphlet.tags.join(", ") || "-"}
              </p>
              <Link
                href={`/pamphlets/${pamphlet.id}`}
                className="text-blue-600 hover:underline"
              >
                مشاهده جزوه و نظرات
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}