import { createContext, useEffect, useMemo, useState } from "react";
import api, { TOKEN_KEY } from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return undefined;
    }
    api
      .get("/api/auth/me")
      .then((response) => {
        if (active) setUser(response.data.user);
      })
      .catch(() => {
        sessionStorage.removeItem(TOKEN_KEY);
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      async login(username, password) {
        const { data } = await api.post("/api/auth/login", { username, password });
        sessionStorage.setItem(TOKEN_KEY, data.access_token);
        setUser(data.user);
        return data.user;
      },
      async register(payload) {
        const { data } = await api.post("/api/auth/register", payload);
        sessionStorage.setItem(TOKEN_KEY, data.access_token);
        setUser(data.user);
        return data.user;
      },
      async logout() {
        try {
          await api.post("/api/auth/logout");
        } catch {
          /* The local session is cleared even if the API is unreachable. */
        }
        sessionStorage.removeItem(TOKEN_KEY);
        setUser(null);
      },
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
