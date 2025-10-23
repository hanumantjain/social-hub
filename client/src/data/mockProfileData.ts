export interface ProfileData {
  id: number;
  full_name: string;
  username: string;
  bio: string;
  website: string;
  location: string;
  profile_picture: string;
  posts_count: number;
  followers_count: number;
  following_count: number;
  created_at: string;
  updated_at: string;
}

export const mockProfileData: ProfileData = {
  id: 1,
  full_name: "John Doe",
  username: "johndoe",
  bio: "Welcome to my Instagram profile! 📸\nPhotography enthusiast | Travel lover | Coffee addict ☕\nFollow me for daily adventures!",
  website: "https://johndoe.photography",
  location: "New York, NY",
  profile_picture: "",
  posts_count: 127,
  followers_count: 1250,
  following_count: 89,
  created_at: "2023-01-15T10:30:00Z",
  updated_at: "2024-01-15T14:22:00Z"
};

export const mockStories = [
  {
    id: 1,
    title: "Morning Coffee",
    thumbnail: "",
    isViewed: false
  },
  {
    id: 2,
    title: "Sunset View",
    thumbnail: "",
    isViewed: true
  },
  {
    id: 3,
    title: "City Walk",
    thumbnail: "",
    isViewed: false
  },
  {
    id: 4,
    title: "Weekend Vibes",
    thumbnail: "",
    isViewed: true
  },
  {
    id: 5,
    title: "New Adventure",
    thumbnail: "",
    isViewed: false
  }
];

export const mockPosts = [
  {
    id: 1,
    image_url: "",
    caption: "Beautiful sunset today! 🌅 #sunset #photography",
    likes_count: 42,
    comments_count: 8,
    created_at: "2024-01-10T18:30:00Z"
  },
  {
    id: 2,
    image_url: "",
    caption: "Coffee and code ☕️ #developer #coffee",
    likes_count: 28,
    comments_count: 5,
    created_at: "2024-01-09T09:15:00Z"
  },
  {
    id: 3,
    image_url: "",
    caption: "Weekend vibes 🏖️ #weekend #beach",
    likes_count: 67,
    comments_count: 12,
    created_at: "2024-01-08T16:45:00Z"
  },
  {
    id: 4,
    image_url: "",
    caption: "New project coming soon! 🚀 #project #coding",
    likes_count: 89,
    comments_count: 23,
    created_at: "2024-01-07T11:20:00Z"
  },
  {
    id: 5,
    image_url: "",
    caption: "City lights at night 🌃 #city #night",
    likes_count: 156,
    comments_count: 34,
    created_at: "2024-01-06T20:10:00Z"
  },
  {
    id: 6,
    image_url: "",
    caption: "Morning workout 💪 #fitness #morning",
    likes_count: 73,
    comments_count: 15,
    created_at: "2024-01-05T07:30:00Z"
  },
  {
    id: 7,
    image_url: "",
    caption: "Delicious dinner 🍝 #food #dinner",
    likes_count: 45,
    comments_count: 9,
    created_at: "2024-01-04T19:45:00Z"
  },
  {
    id: 8,
    image_url: "",
    caption: "Reading time 📚 #books #reading",
    likes_count: 31,
    comments_count: 6,
    created_at: "2024-01-03T15:20:00Z"
  },
  {
    id: 9,
    image_url: "",
    caption: "Nature walk 🌿 #nature #walk",
    likes_count: 58,
    comments_count: 11,
    created_at: "2024-01-02T13:15:00Z"
  }
];

// Mock API functions
export const mockProfileAPI = {
  async getProfile(): Promise<ProfileData> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockProfileData;
  },

  async updateProfile(updates: Partial<ProfileData>): Promise<ProfileData> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Merge updates with existing data
    const updatedProfile = { ...mockProfileData, ...updates };
    
    // Update the mock data
    Object.assign(mockProfileData, updatedProfile);
    
    return updatedProfile;
  },

  async getStories() {
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockStories;
  },

  async getPosts() {
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockPosts;
  }
};
