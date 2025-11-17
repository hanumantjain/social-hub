import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import { Link } from "react-router-dom";
import { postsAPI } from "../services/api";
import type { Post } from "../services/api";

const Feed = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const data = await postsAPI.getAllPosts();
        setPosts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load posts");
      } finally {
        setIsLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const handleDownload = async (imageUrl: string, postId: number) => {
    try {
      const response = await fetch(imageUrl, {
        mode: 'cors',
        cache: 'no-cache',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.statusText}`);
      }

      const blob = await response.blob();
      
      // Determine file extension from blob type or URL
      let extension = 'jpg';
      if (blob.type) {
        const mimeType = blob.type;
        if (mimeType.includes('png')) extension = 'png';
        else if (mimeType.includes('gif')) extension = 'gif';
        else if (mimeType.includes('webp')) extension = 'webp';
        else if (mimeType.includes('jpeg')) extension = 'jpg';
      } else {
        // Fallback: try to extract from URL
        const urlMatch = imageUrl.match(/\.(jpg|jpeg|png|gif|webp)/i);
        if (urlMatch) {
          extension = urlMatch[1].toLowerCase();
          if (extension === 'jpeg') extension = 'jpg';
        }
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `post-${postId}.${extension}`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Clean up after a short delay
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
    } catch (err) {
      console.error("Failed to download image:", err);
      alert("Failed to download image. Please try again.");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading feed...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)]">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      
      <div className="px-8 sm:px-12 lg:px-16 xl:px-20 py-8">
        <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4">
          {posts.map((post) => (
            <div key={post.id} className="break-inside-avoid mb-4 group cursor-pointer relative group-hover:z-20">
              <Link to={`/post/${post.id}`} state={{ post }} className="relative block bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 ease-in-out group-hover:scale-102">
                {/* Image */}
                <div className="relative overflow-hidden">
                  <img
                    src={post.image_url}
                    alt={post.caption || "Post"}
                    className="w-full h-auto object-cover"
                    loading="lazy"
                    decoding="async"
                    fetchPriority="low"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "https://via.placeholder.com/600x400?text=Image+Not+Found";
                    }}
                  />
                  {/* Gray overlay on hover */}
                  <div className="absolute inset-0 bg-gray-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out z-0"></div>
                  {/* Download icon button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleDownload(post.image_url, post.id);
                    }}
                    className="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 rounded-full transition-all opacity-0 group-hover:opacity-100 z-20"
                    aria-label="Download image"
                    type="button"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  </button>
                  {/* Title overlay */}
                  {post.title && (
                    <div className="absolute bottom-0 left-0 right-0 px-3 py-2 transition-all opacity-0 group-hover:opacity-100 z-20">
                      <p className="text-white text-sm font-medium line-clamp-2 drop-shadow-lg">{post.title}</p>
                    </div>
                  )}
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Feed;