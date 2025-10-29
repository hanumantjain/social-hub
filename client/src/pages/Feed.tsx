import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
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
            <div key={post.id} className="break-inside-avoid mb-4 group cursor-pointer">
              <div className="relative bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
                {/* Image */}
                <div className="relative">
                  <img
                    src={post.image_url}
                    alt={post.caption || "Post"}
                    className="w-full h-auto object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "https://via.placeholder.com/600x400?text=Image+Not+Found";
                    }}
                  />
                  {/* Caption overlay on hover */}
                  {post.caption && (
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                      <p className="text-white text-sm line-clamp-3">{post.caption}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Feed;