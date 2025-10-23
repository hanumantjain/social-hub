import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { authAPI, tokenManager } from "../services/api";
import type { User } from "../services/api";
import { mockProfileAPI, type ProfileData } from "../data/mockProfileData";

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
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
      const token = tokenManager.getToken();
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        // Fetch both user data and profile data
        const [userData, profileData] = await Promise.all([
          authAPI.getCurrentUser(token),
          mockProfileAPI.getProfile()
        ]);
        
        setUser(userData);
        setProfileData(profileData);
        setFullName(profileData.full_name || "");
        setUsername(profileData.username || "");
        setBio(profileData.bio || "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
        // If token is invalid, redirect to login
        if (err instanceof Error && err.message.includes("credentials")) {
          tokenManager.removeToken();
          navigate("/login");
        }
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
      // Update profile using mock API
      const updatedProfile = await mockProfileAPI.updateProfile({
        full_name: fullName,
        username: username,
        bio: bio
      });
      
      setProfileData(updatedProfile);
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
    setFullName(profileData?.full_name || "");
    setUsername(profileData?.username || "");
    setBio(profileData?.bio || "");
  };

  const handleChangePhoto = () => {
    // Handle profile photo change
    console.log("Change profile photo clicked");
  };

  // if (isLoading) {
  //   return (
  //     <div>
  //       <Navbar />
  //       <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
  //         <div className="text-gray-600">Loading profile...</div>
  //       </div>
  //     </div>
  //   );
  // }

  // if (error) {
  //   return (
  //     <div>
  //       <Navbar />
  //       <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
  //         <div className="text-red-600">{error}</div>
  //       </div>
  //     </div>
  //   );
  // }

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
                {profileData?.full_name?.charAt(0)?.toUpperCase() || 'U'}
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
                  {profileData?.username || 'username'}
                </h1>
                 <button 
                   onClick={() => setShowEditModal(true)}
                   className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-1.5 rounded-md text-sm font-medium transition-colors">
                   Edit Profile
                 </button>
              </div>
              
              {/* Stats */}
              <div className="flex space-x-8 mb-4">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">{profileData?.posts_count || 0}</div>
                  <div className="text-sm text-gray-600">posts</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">{profileData?.followers_count || 0}</div>
                  <div className="text-sm text-gray-600">followers</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">{profileData?.following_count || 0}</div>
                  <div className="text-sm text-gray-600">following</div>
                </div>
              </div>
              
              {/* Bio */}
              <div className="space-y-1">
                <div className="text-sm font-semibold text-gray-900">
                  {profileData?.full_name || 'Full Name'}
                </div>
                <div className="text-sm text-gray-900 whitespace-pre-line">
                  {profileData?.bio || 'No bio yet'}
                </div>
                {profileData?.location && (
                  <div className="text-sm text-gray-900">
                    📍 {profileData.location}
                  </div>
                )}
                {profileData?.website && (
                  <div className="text-sm text-gray-900">
                    🌐 <a href={profileData.website} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{profileData.website}</a>
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
            {profileData ? (
              <div className="grid grid-cols-3 gap-1">
                {profileData.posts_count > 0 ? (
                  // Show mock posts
                  [1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                    <div key={i} className="aspect-square bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center text-gray-500 text-2xl font-bold hover:opacity-90 transition-opacity cursor-pointer">
                      {i}
                    </div>
                  ))
                ) : (
                  // Empty state - no posts yet
                  <div className="col-span-3 text-center py-12">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No posts yet</h3>
                    <p className="text-gray-500">When you share photos and videos, they'll appear on your profile.</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-gray-500">Loading profile...</div>
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
