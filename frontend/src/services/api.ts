import axios from "axios";
import { useAppStore } from "../store/useAppStore";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach JWT Token
api.interceptors.request.use(
  (config) => {
    const token = useAppStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Auto Refresh JWT Token on 401
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      const refreshToken = useAppStore.getState().refreshToken;
      if (!refreshToken) {
        useAppStore.getState().logout();
        isRefreshing = false;
        return Promise.reject(error);
      }
      
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`);
        const { access_token, refresh_token } = response.data;
        
        useAppStore.getState().setAuth(access_token, refresh_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);
        isRefreshing = false;
        
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAppStore.getState().logout();
        isRefreshing = false;
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
