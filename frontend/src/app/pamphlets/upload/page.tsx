"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";


export default function UploadPamphletPage() {
  const [title, setTitle] = useState("");
  const [grade, setGrade] = useState("");
  const [subject, setSubject] = useState("");
  const [chapter, setChapter] = useState("");
  const [method, setMethod] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [tags, setTags] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { token } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!token) {
      setError("لطفاً ابتدا وارد شوید.");
      setLoading(false);
      return;
    }

    try {
      // Step 1: Create pamphlet
      const pamphletResponse = await fetch("http://localhost:8000/api/v1/pamphlets/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          grade,
          subject,
          chapter,
          method: method || undefined,
          difficulty: difficulty || undefined,
          is_public: isPublic ? 1 : 0,
          tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        }),
      });

      if (!pamphletResponse.ok) {
        const data = await pamphletResponse.json();
        throw new Error(data.detail || "خطا در ایجاد جزوه");
      }

      const pamphletData = await pamphletResponse.json();

      // Step 2: Upload file
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("version_number", "1.0");
        formData.append("notes", notes);

        const versionResponse = await fetch(
          `http://localhost:8000/api/v1/pamphlets/${pamphletData.id}/versions`,
          {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${token}`,
            },
            body: formData,
          }
        );

        if (!versionResponse.ok) {
          const data = await versionResponse.json();
          throw new Error(data.detail || "خطا در آپلود فایل");
        }
      }

      router.push("/pamphlets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطای ناشناخته");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">آپلود جزوه جدید</h1>
      {error && <div className="bg-red-100 text-red-700 p-3 mb-4 rounded">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">عنوان جزوه</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">پایه</label>
          <input
            type="text"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">درس</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">فصل</label>
          <input
            type="text"
            value={chapter}
            onChange={(e) => setChapter(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">روش تدریس</label>
          <input
            type="text"
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="w-full p-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">سطح دشواری</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">انتخاب کنید</option>
            <option value="آسان">آسان</option>
            <option value="متوسط">متوسط</option>
            <option value="سخت">سخت</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">عمومی</label>
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="mr-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">تگ‌ها (با کاما جدا کنید)</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="w-full p-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">فایل جزوه</label>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">یادداشت‌ها</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full p-2 border rounded"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? "در حال آپلود..." : "آپلود جزوه"}
        </button>
      </form>
    </div>
  );
}