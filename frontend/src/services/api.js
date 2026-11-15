import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "vaultline_token";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || "";
    const signingIn = url.includes("/api/auth/login") || url.includes("/api/auth/register");
    if (status === 401 && !signingIn) {
      sessionStorage.removeItem(TOKEN_KEY);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error, fallback = "Something went wrong.") {
  if (!API_BASE_URL) {
    return "Set VITE_API_BASE_URL to the backend address before using the app.";
  }
  if (!error?.response) {
    return "Cannot reach the banking API. Check that the backend is running.";
  }
  return error.response.data?.error || fallback;
}

export { TOKEN_KEY };
export default api;
