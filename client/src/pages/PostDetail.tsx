import { useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import { postsAPI } from "../services/api";
import type { Post } from "../services/api";

const PostDetail = () => {
  const { id } = useParams();
  const location = useLocation();
  const locationState = location.state as { post?: Post } | null;
  const initialPost = locationState?.post;

  const [post, setPost] = useState<Post | null>(initialPost || null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [viewTracked, setViewTracked] = useState(false);

  useEffect(() => {
    const loadPost = async () => {
      if (!id) return;
      try {
        setIsLoading(true);
        setViewTracked(false); // Reset view tracking when post ID changes
        const data = await postsAPI.getPostById(Number(id));
        setPost(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load post");
      } finally {
        setIsLoading(false);
      }
    };

    loadPost();
  }, [id]);

  // Track view when post is loaded (only once per post ID)
  useEffect(() => {
    const trackView = async () => {
      if (!post || !id || viewTracked || isLoading) return;
      
      try {
        const result = await postsAPI.trackView(Number(id));
        setPost(prev => {
          if (!prev) return null;
          return { ...prev, views: result.views };
        });
        setViewTracked(true);
      } catch (err) {
        // Still mark as tracked to prevent retries
        setViewTracked(true);
      }
    };

    if (post && !isLoading) {
      trackView();
    }
  }, [post, id, viewTracked, isLoading]);

  const displayTitle = useMemo(() => {
    if (!post) return "Photo";
    if (post.title && post.title.trim().length > 0) {
      return post.title;
    }
    if (post.username) return `Photo by ${post.username}`;
    return "Photo";
  }, [post]);

  const tagsArray = useMemo(() => {
    if (!post || !post.tags) return [];
    return post.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
  }, [post]);

  const handleDownload = async (imageUrl: string, fallbackName: string) => {
    if (!post || !id) return;
    
    try {
      // Download the image first
      const response = await fetch(imageUrl, { mode: 'cors', cache: 'no-cache' });
      if (!response.ok) throw new Error(`Failed to fetch image: ${response.statusText}`);
      const blob = await response.blob();
      let extension = 'jpg';
      if (blob.type) {
        const mimeType = blob.type;
        if (mimeType.includes('png')) extension = 'png';
        else if (mimeType.includes('gif')) extension = 'gif';
        else if (mimeType.includes('webp')) extension = 'webp';
        else if (mimeType.includes('jpeg')) extension = 'jpg';
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeName = fallbackName.replace(/[^a-z0-9\-_. ]/gi, '').trim() || 'photo';
      a.download = `${safeName}.${extension}`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 100);

      // Track download after 2 seconds delay
      setTimeout(async () => {
        try {
          const result = await postsAPI.trackDownload(Number(id));
          setPost(prev => {
            if (!prev) return null;
            return { ...prev, downloads: result.downloads };
          });
        } catch (err) {
          // Silently fail - download already happened
        }
      }, 2000);
    } catch (err) {
      alert('Failed to download image. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading photo…</p>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] p-4">
          <p className="text-red-600">{error || 'Photo not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="px-6 sm:px-10 lg:px-16 xl:px-24 py-8">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">
          {/* Left: Photo */}
          <div className="w-full">
            <img
              src={post.image_url}
              loading="eager"
              fetchPriority="high"
              decoding="async"
              alt={post.caption || 'Photo'}
              className="w-full h-auto rounded-lg shadow"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = "https://via.placeholder.com/1200x800?text=Image+Not+Found";
              }}
            />
          </div>

          {/* Right: Details */}
          <div className="w-full flex flex-col gap-6">
            {/* Title */}
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">{displayTitle}</h1>
            </div>

            {/* Name and Username */}
            {(post.user_full_name || post.username) && (
              <div className="space-y-1">
                {post.user_full_name && (
                  <p className="text-base font-medium text-gray-800">{post.user_full_name}</p>
                )}
                {post.username && (
                  <p className="text-sm text-gray-500">@{post.username}</p>
                )}
              </div>
            )}

            {/* Description */}
            {post.caption && (
              <div className="bg-gray-100 rounded-md p-4">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{post.caption}</p>
              </div>
            )}

            {/* Tags */}
            {tagsArray.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tagsArray.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Metrics */}
            <div className="flex items-center gap-6 text-gray-600">
              <div className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span className="text-sm">Views: {post.views ?? 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span className="text-sm">Downloads: {post.downloads ?? 0}</span>
              </div>
            </div>

            {/* Dedicated Download Button */}
            <div className="pt-2">
              <button
                onClick={() => handleDownload(post.image_url, displayTitle)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-black transition-colors"
                type="button"
                aria-label="Download image"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostDetail;


