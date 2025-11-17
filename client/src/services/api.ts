
// Get API base URL - for API Gateway, keep the stage prefix (e.g., /Prod)
// API Gateway will strip the stage prefix before sending to Lambda
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

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
  async getCurrentUser(): Promise<User> {
    const response = await authenticatedFetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
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
  async updateProfile(profileData: UpdateProfileRequest): Promise<User> {
    const response = await authenticatedFetch(`${API_BASE_URL}/auth/me`, {
      method: 'PATCH',
      headers: {
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

  // Google OAuth login/signup
  // Frontend verifies with Google API and sends verified user info to backend
  async googleAuth(userInfo: { google_id: string; email: string; name: string; picture?: string }): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userInfo),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Google authentication failed');
    }

    return response.json();
  },
};

// Posts API
export const postsAPI = {
  // Get presigned URL for direct S3 upload (for large files)
  async getPresignedUrl(filename: string, contentType: string): Promise<{
    upload_url: string;
    key: string;
    public_url: string;
  }> {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/posts/presigned-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
  async confirmUpload(imageUrl: string, caption: string, title?: string, tags?: string): Promise<Post> {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/posts/confirm-upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image_url: imageUrl, caption, title, tags }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to confirm upload');
    }

    return response.json();
  },

  // Get all posts (feed)
  async getAllPosts(): Promise<Post[]> {
    // Ensure no trailing slash to avoid API Gateway redirects
    const url = `${API_BASE_URL}/api/posts`.replace(/\/+$/, '');
    const response = await fetch(url);

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

  // Delete post
  async deletePost(postId: number): Promise<void> {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/posts/${postId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to delete post');
    }
  },

  // Track view
  async trackView(postId: number): Promise<{ views: number }> {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/posts/${postId}/view`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to track view');
    }

    return response.json();
  },

  // Track download
  async trackDownload(postId: number): Promise<{ downloads: number }> {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/posts/${postId}/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to track download');
    }

    return response.json();
  },
};

// JWT Token Utilities
function decodeJWT(token: string): { exp?: number; sub?: string } | null {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) return true;
  
  // Check if token is expired (exp is in seconds, Date.now() is in milliseconds)
  const expirationTime = decoded.exp * 1000;
  return Date.now() >= expirationTime;
}

// Global error handler for authentication
let onAuthError: (() => void) | null = null;

export function setAuthErrorHandler(handler: () => void): void {
  onAuthError = handler;
}

// Token management (defined before authenticatedFetch)
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

  // Check if user is authenticated and token is valid
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;
    return !isTokenExpired(token);
  },

  // Check if token is expired (useful for warnings)
  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) return true;
    return isTokenExpired(token);
  },

  // Get token expiration time (for display)
  getTokenExpiration(): Date | null {
    const token = this.getToken();
    if (!token) return null;
    const decoded = decodeJWT(token);
    if (!decoded || !decoded.exp) return null;
    return new Date(decoded.exp * 1000);
  },
};

// Enhanced fetch wrapper with 401 handling
async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = tokenManager.getToken();
  
  // Check if token exists and is not expired
  if (token && isTokenExpired(token)) {
    tokenManager.removeToken();
    if (onAuthError) {
      onAuthError();
    }
    throw new Error('Session expired. Please login again.');
  }

  // Add Authorization header if token exists
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized globally
  if (response.status === 401) {
    tokenManager.removeToken();
    if (onAuthError) {
      onAuthError();
    }
    throw new Error('Session expired. Please login again.');
  }

  return response;
}
