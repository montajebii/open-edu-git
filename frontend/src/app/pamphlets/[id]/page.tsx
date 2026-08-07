"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";

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
  author: {
    id: number;
    full_name: string;
  };
}

interface Review {
  id: number;
  rating: number;
  comment?: string;
  created_at: string;
  user: {
    id: number;
    full_name: string;
  };
}

export default function PamphletDetailPage({ params }: { params: { id: string } }) {
  const [pamphlet, setPamphlet] = useState<Pamphlet | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const { token, tokenPayload } = useAuth();

  useEffect(() => {
    const fetchPamphlet = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/pamphlets/${params.id}`);
        if (!response.ok) {
          throw new Error("Failed to fetch pamphlet");
        }
        const data = await response.json();
        setPamphlet(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    };

    const fetchReviews = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/reviews/pamphlets/${params.id}/reviews`);
        if (!response.ok) {
          throw new Error("Failed to fetch reviews");
        }
        const data = await response.json();
        setReviews(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchPamphlet();
    fetchReviews();
  }, [params.id]);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setReviewError("Please login to submit a review");
      return;
    }
    setReviewLoading(true);
    setReviewError("");

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/reviews/pamphlets/${params.id}/reviews`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({ rating, comment }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to submit review");
      }

      // Refresh reviews
      const reviewsResponse = await fetch(
        `http://localhost:8000/api/v1/reviews/pamphlets/${params.id}/reviews`
      );
      if (reviewsResponse.ok) {
        const data = await reviewsResponse.json();
        setReviews(data);
      }
      setComment("");
      setRating(5);
    } catch (err) {
      setReviewError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setReviewLoading(false);
    }
  };

  if (loading) return <div className="container mx-auto px-4 py-8">Loading...</div>;
  if (error) return <div className="container mx-auto px-4 py-8 text-red-600">{error}</div>;
  if (!pamphlet) return <div className="container mx-auto px-4 py-8">Pamphlet not found</div>;

  const hasReviewed = reviews.some((review) => review.user.id === tokenPayload?.sub);
  const averageRating = reviews.length
    ? (reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length).toFixed(1)
    : "No reviews yet";

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/pamphlets" className="text-blue-600 hover:underline">← Back to Pamphlets</Link>
      </div>

      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h1 className="text-2xl font-bold mb-4">{pamphlet.title}</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-gray-600"><strong>Grade:</strong> {pamphlet.grade}</p>
            <p className="text-gray-600"><strong>Subject:</strong> {pamphlet.subject}</p>
            <p className="text-gray-600"><strong>Chapter:</strong> {pamphlet.chapter}</p>
          </div>
          <div>
            <p className="text-gray-600"><strong>Method:</strong> {pamphlet.method || "-"}</p>
            <p className="text-gray-600"><strong>Difficulty:</strong> {pamphlet.difficulty || "-"}</p>
            <p className="text-gray-600"><strong>Tags:</strong> {pamphlet.tags.join(", ") || "-"}</p>
          </div>
        </div>
        <p className="text-gray-600 mb-4"><strong>Author:</strong> {pamphlet.author.full_name}</p>
        <p className="text-gray-600 mb-4"><strong>Average Rating:</strong> {averageRating}</p>
        <a
          href={`http://localhost:9000/${pamphlet.versions?.[0]?.file_path}`}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 inline-block"
          target="_blank"
          rel="noopener noreferrer"
        >
          Download Pamphlet
        </a>
      </div>

      {/* Reviews Section */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Reviews ({reviews.length})</h2>
        {reviews.length === 0 ? (
          <p>No reviews yet. Be the first to review!</p>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div key={review.id} className="border p-4 rounded">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="font-medium">{review.user.full_name}</p>
                    <p className="text-yellow-500">
                      {'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}
                    </p>
                  </div>
                  <p className="text-sm text-gray-500">{new Date(review.created_at).toLocaleDateString()}</p>
                </div>
                {review.comment && <p className="text-gray-700">{review.comment}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Form */}
      {!hasReviewed && token && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Submit a Review</h2>
          {reviewError && <div className="bg-red-100 text-red-700 p-3 mb-4 rounded">{reviewError}</div>}
          <form onSubmit={handleReviewSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Rating</label>
              <select
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
                className="w-full p-2 border rounded"
                required
              >
                {[1, 2, 3, 4, 5].map((num) => (
                  <option key={num} value={num}>{num} Star{num > 1 ? 's' : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Comment</label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full p-2 border rounded"
                rows={4}
              />
            </div>
            <button
              type="submit"
              disabled={reviewLoading}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {reviewLoading ? "Submitting..." : "Submit Review"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}