import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { authAPI, tokenManager, postsAPI } from "../services/api";
import type { User, UpdateProfileRequest, Post } from "../services/api";

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showEditModal, setShowEditModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Form fields for edit modal
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");

  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!tokenManager.isAuthenticated()) {
        navigate("/login");
        return;
      }

      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        setFullName(userData.full_name || "");
        setUsername(userData.username || "");
        setBio(userData.bio || "");

        // Fetch user's posts
        if (userData.id) {
          try {
            const userPosts = await postsAPI.getUserPosts(userData.id);
            setPosts(userPosts);
          } catch (postsErr) {
            console.error("Failed to fetch user posts:", postsErr);
            // Don't set error state for posts failure, just log it
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
        // Global handler will redirect to login if token is expired
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserProfile();
  }, [navigate]);

  const handleSaveProfile = async () => {
    setIsSaving(true);
    setError("");
    
    try {
      if (!tokenManager.isAuthenticated()) {
        navigate("/login");
        return;
      }

      // Prepare update data - only send changed fields
      const updateData: UpdateProfileRequest = {};
      
      if (fullName !== user?.full_name) {
        updateData.full_name = fullName;
      }
      
      if (username !== user?.username) {
        updateData.username = username;
      }
      
      if (bio !== user?.bio) {
        updateData.bio = bio;
      }

      // Call API to update profile
      const updatedUser = await authAPI.updateProfile(updateData);
      setUser(updatedUser);
      
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        setShowEditModal(false);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setShowEditModal(false);
    setFullName(user?.full_name || "");
    setUsername(user?.username || "");
    setBio(user?.bio || "");
  };

  const handleChangePhoto = () => {
    // Handle profile photo change
    console.log("Change profile photo clicked");
  };

  if (isLoading) {
    return (
      <div>
        <Navbar />
        <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
          <div className="text-gray-600">Loading profile...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Navbar />
        <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
          <div className="text-red-600">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      
      {/* Profile Header */}
      <div className="max-w-4xl mx-auto border border-gray-200 mt-5">
        <div className="bg-white border-b border-gray-200 p-6">
          <div className="flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-8">
            {/* Profile Picture */}
            <div className="flex-shrink-0 relative">
              <div className="w-32 h-32 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white text-4xl font-bold">
                {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              {/* Small change photo button */}
              <button
                onClick={handleChangePhoto}
                className="absolute bottom-0 right-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold transition-colors"
              >
                +
              </button>
            </div>
            
            {/* Profile Info */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 mb-4">
                <h1 className="text-2xl font-light text-gray-900 mb-2 sm:mb-0">
                  {user?.username || 'username'}
                </h1>
                 <button 
                   onClick={() => setShowEditModal(true)}
                   className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-1.5 rounded-md text-sm font-medium transition-colors">
                   Edit Profile
                 </button>
              </div>
              
              {/* Bio */}
              <div className="space-y-1">
                <div className="text-sm font-semibold text-gray-900">
                  {user?.full_name || 'Full Name'}
                </div>
                {user?.bio && (
                  <div className="text-sm text-gray-900 whitespace-pre-wrap">
                    {user.bio}
                  </div>
                )}
                {!user?.bio && (
                  <div className="text-sm text-gray-500 italic">
                    No bio yet
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Posts Grid */}
        <div className="bg-white">
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex justify-center space-x-16 px-6">
              <button className="py-4 px-1 border-b-2 border-gray-900 text-sm font-medium text-gray-900 flex items-center">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 1v10h10V5H5z" clipRule="evenodd" />
                </svg>
                POSTS
              </button>
              <button className="py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 flex items-center">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                </svg>
                SAVED
              </button>
            </nav>
          </div>
          
          {/* Posts Grid */}
          <div className="p-6">
            {posts.length > 0 ? (
              <div className="grid grid-cols-3 gap-1">
                {posts.map((post) => (
                  <div
                    key={post.id}
                    className="relative aspect-square overflow-hidden bg-gray-100 cursor-pointer group"
                  >
                    <img
                      src={post.image_url}
                      alt={post.caption || 'Post'}
                      className="w-full h-full object-cover transition-transform group-hover:scale-105"
                    />
                    {/* Hover overlay with caption */}
                    {post.caption && (
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <p className="text-white text-sm text-center px-4 line-clamp-3">
                          {post.caption}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No posts yet</h3>
                <p className="text-gray-500 mb-4">When you share photos and videos, they'll appear on your profile.</p>
                <button
                  onClick={() => navigate('/upload')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Share Your First Photo
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleCancelEdit}
                  className="text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
                <h2 className="text-lg font-semibold text-gray-900">Edit Profile</h2>
              </div>
              <button
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                {isSaving ? "Saving..." : "Done"}
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                  <div className="text-sm text-red-700">{error}</div>
                </div>
              )}

              {saveSuccess && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="text-sm text-green-700">Profile updated successfully!</div>
                </div>
              )}

              <div className="space-y-6">
                {/* Form Fields */}
                <div className="space-y-4">
                  {/* Name Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your full name"
                    />
                  </div>

                  {/* Username Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username
                    </label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your username"
                    />
                  </div>

                  {/* Bio Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bio
                    </label>
                    <textarea
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      placeholder="Tell us about yourself"
                    />
                  </div>
                </div>

                {/* Help Text */}
                <div className="text-xs text-gray-500">
                  <p>• Use a maximum of 150 characters for your bio</p>
                  <p>• Press Enter for new lines</p>
                  <p>• Changes will be visible to other users</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
