import axios, { AxiosInstance } from "axios";

const axiosInstance: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.example.com",
  timeout: 10000, // 10 seconds timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error("Unauthorized! Redirecting to login...");
      // Handle logout or redirection if needed
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
