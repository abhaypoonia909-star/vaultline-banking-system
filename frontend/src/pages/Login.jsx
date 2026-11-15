import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import mark from "../assets/mark.svg";
import AlertBanner from "../components/AlertBanner";
import { useAuth } from "../hooks/useAuth";
import { API_BASE_URL, getErrorMessage } from "../services/api";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err, "Sign-in failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-aside">
        <img src={mark} alt="" width="56" height="56" />
        <p className="eyebrow">Vaultline</p>
        <h1>A quieter place to watch the ledger.</h1>
        <p className="lede">
          Accounts, deposits, withdrawals, and a local brute-force simulation that never leaves this application.
        </p>
      </section>
      <section className="auth-main">
        <form className="auth-card" onSubmit={onSubmit}>
          <p className="eyebrow">Customer sign in</p>
          <h2>Welcome back</h2>
          <AlertBanner>{error}</AlertBanner>
          <label className="field">
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </label>
          <label className="field">
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? "Signing in" : "Sign in"}
          </button>
          <p className="footer-note">
            New here? <Link to="/register">Open an account profile</Link>
          </p>
          <p className="footer-note">API {API_BASE_URL || "not configured"}</p>
        </form>
      </section>
    </div>
  );
}
