
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types
export interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
  bio?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SignupRequest {
  full_name: string;
  username: string;
  email: string;
  password: string;
  bio?: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  username?: string;
  bio?: string;
}

export interface Post {
  id: number;
  user_id: number;
  image_url: string;
  title?: string;
  caption?: string;
  tags?: string;
  views?: number;
  downloads?: number;
  created_at: string;
  updated_at: string;
  username?: string;
  user_full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

// API Service Functions
export const authAPI = {
  // Login user
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    return response.json();
  },

  // Signup user
  async signup(userData: SignupRequest): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    return response.json();
  },

  // Get current user
  async getCurrentUser(token: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to get user info');
    }

    return response.json();
  },

  // Update user profile
  async updateProfile(token: string, profileData: UpdateProfileRequest): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to update profile');
    }

    return response.json();
  },
};

// Posts API
export const postsAPI = {
  // Get presigned URL for direct S3 upload (for large files)
  async getPresignedUrl(filename: string, contentType: string, token: string): Promise<{
    upload_url: string;
    key: string;
    public_url: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/posts/presigned-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ filename, content_type: contentType }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to get upload URL');
    }

    return response.json();
  },

  // Upload file directly to S3 using presigned URL
  async uploadToS3(presignedUrl: string, file: File): Promise<void> {
    const response = await fetch(presignedUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: file,
    });

    if (!response.ok) {
      throw new Error(`S3 upload failed: ${response.status} ${response.statusText}`);
    }
  },

  // Confirm upload and create post record
  async confirmUpload(imageUrl: string, caption: string, token: string): Promise<Post> {
    const response = await fetch(`${API_BASE_URL}/posts/confirm-upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ image_url: imageUrl, caption }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to confirm upload');
    }

    return response.json();
  },

  // Get all posts (feed)
  async getAllPosts(): Promise<Post[]> {
    const response = await fetch(`${API_BASE_URL}/api/posts`);

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to fetch posts');
    }

    return response.json();
  },

  // Get posts by user
  async getUserPosts(userId: number): Promise<Post[]> {
    const response = await fetch(`${API_BASE_URL}/api/posts/user/${userId}`);

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to fetch user posts');
    }

    return response.json();
  },

  // Get a single post by id
  async getPostById(postId: number): Promise<Post> {
    const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`);

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to fetch post');
    }

    return response.json();
  },

  // Track a view for a post
  async trackView(postId: number): Promise<{ views: number }> {
    const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/view`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to track view');
    }

    return response.json();
  },

  // Track a download for a post
  async trackDownload(postId: number): Promise<{ downloads: number }> {
    const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/download`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to track download');
    }

    return response.json();
  },

  // Delete post
  async deletePost(postId: number, token: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/posts/${postId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to delete post');
    }
  },
};

// Token management
export const tokenManager = {
  // Save token to localStorage
  saveToken(token: string): void {
    localStorage.setItem('access_token', token);
  },

  // Get token from localStorage
  getToken(): string | null {
    return localStorage.getItem('access_token');
  },

  // Remove token from localStorage
  removeToken(): void {
    localStorage.removeItem('access_token');
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
