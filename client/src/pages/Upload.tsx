import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { tokenManager } from "../services/api";

const Upload = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication on component mount
  useEffect(() => {
    setIsAuthenticated(tokenManager.isAuthenticated());
  }, []);

  const handleFileSelect = (file: File) => {
    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file");
      return;
    }

    // Validate file size (50MB for direct S3 upload)
    if (file.size > 50 * 1024 * 1024) {
      setError("File size must not exceed 50MB. Please choose a smaller image.");
      return;
    }

    setSelectedFile(file);
    setError("");

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select an image");
      return;
    }

    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    if (!description.trim()) {
      setError("Description is required");
      return;
    }

    const token = tokenManager.getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    // Double-check file size before upload (50MB for direct S3 upload)
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError("File size must not exceed 50MB. Please choose a smaller image.");
      return;
    }

    setIsUploading(true);
    setError("");

    try {
      // Step 1: Get presigned URL from backend
      console.log("Requesting presigned URL...");
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/posts/presigned-url`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            filename: selectedFile.name,
            content_type: selectedFile.type,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get upload URL");
      }

      const presignedData = await response.json();
      console.log("Presigned URL received:", presignedData.key);

      // Step 2: Upload directly to S3
      console.log("Uploading to S3...");
      const uploadResponse = await fetch(presignedData.upload_url, {
        method: "PUT",
        headers: {
          "Content-Type": selectedFile.type,
        },
        body: selectedFile,
      });

      if (!uploadResponse.ok) {
        throw new Error(`S3 upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`);
      }

      console.log("Upload to S3 successful!");

      // Step 3: Confirm upload with backend
      console.log("Confirming upload...");
      const confirmResponse = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/posts/confirm-upload`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            image_url: presignedData.public_url,
            title: title.trim(),
            caption: description.trim(),
            tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
          }),
        }
      );

      if (!confirmResponse.ok) {
        const error = await confirmResponse.json();
        throw new Error(error.detail || "Failed to confirm upload");
      }

      console.log("Upload confirmed!");
      
      // Success - redirect to feed
      navigate("/");
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Failed to upload image");
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setPreview(null);
    setTitle("");
    setDescription("");
    setTags("");
    setError("");
  };

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="max-w-4xl mx-auto px-4 py-8 relative min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden w-full max-w-2xl relative">
          {/* Header */}
          <div className="border-b border-gray-200 px-6 py-4">
            <h1 className="text-2xl font-semibold text-gray-900">Create New Post</h1>
          </div>

          {/* Content */}
          <div className="p-6">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <svg
                    className="w-5 h-5 text-red-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <p className="ml-3 text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            <div className="space-y-6">
              {/* Upload Area */}
              {!preview ? (
                <div
                  className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                    dragActive
                      ? "border-black bg-gray-50"
                      : "border-gray-300 hover:border-gray-400"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <svg
                    className="mx-auto h-16 w-16 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <p className="mt-4 text-lg text-gray-600">
                    Drag and drop your image here
                  </p>
                  <p className="mt-2 text-sm text-gray-500">or</p>
                  <label className="mt-4 inline-block">
                    <span className="px-6 py-3 bg-black text-white font-medium rounded-lg hover:bg-gray-900 cursor-pointer transition-colors">
                      Select from computer
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      accept="image/*"
                      onChange={handleFileInput}
                    />
                  </label>
                  <p className="mt-4 text-xs text-gray-500">
                    PNG, JPG, GIF, WEBP up to 50MB
                  </p>
                </div>
              ) : (
                /* Image Preview */
                <div className="relative">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full max-h-96 object-contain bg-gray-100 rounded-lg"
                  />
                  <button
                    onClick={handleCancel}
                    className="absolute top-4 right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition-colors"
                  >
                    <svg
                      className="w-5 h-5 text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              )}

              {/* Title Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter a title..."
                  required
                />
              </div>

              {/* Description Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Write a description..."
                  required
                />
                <p className="mt-2 text-sm text-gray-500">
                  {description.length}/2200 characters
                </p>
              </div>

              {/* Tags Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter tags separated by commas (e.g., nature, photography, sunset)"
                />
                <p className="mt-2 text-sm text-gray-500">
                  {tags.split(',').filter(tag => tag.trim().length > 0).length} tag(s)
                </p>
              </div>

              {/* Action Buttons */}
              {preview && (
                <div className="flex justify-end space-x-4">
                  <button
                    onClick={handleCancel}
                    disabled={isUploading}
                    className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="px-6 py-3 bg-black text-white font-medium rounded-lg hover:bg-gray-900 disabled:opacity-50 transition-colors"
                  >
                    {isUploading ? (
                      <span className="flex items-center">
                        <svg
                          className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Uploading...
                      </span>
                    ) : (
                      "Share"
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
          {/* Login Required Overlay */}
          {!isAuthenticated && (
            <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex items-center justify-center z-10">
              <div className="text-center max-w-md px-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Login Required</h2>
                <p className="text-gray-600 mb-8">
                  You need to be logged in to upload photos. Please sign in to continue.
                </p>
                <div className="space-y-3">
                  <Link
                    to="/login?redirect=/upload"
                    className="block w-full bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-900 transition-colors font-medium"
                  >
                    Login
                  </Link>
                  <Link
                    to="/signup?redirect=/upload"
                    className="block w-full border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    Create Account
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Upload;

