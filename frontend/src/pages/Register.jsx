import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import { useAuth } from "../hooks/useAuth";
import { getErrorMessage } from "../services/api";

const empty = { full_name: "", username: "", email: "", password: "", confirm: "" };

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await register({
        full_name: form.full_name.trim(),
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-aside">
        <p className="eyebrow">New customer</p>
        <h1>Create the profile first. The bank account comes next.</h1>
        <p className="lede">Passwords are hashed on the server. This form never stores them in the page.</p>
      </section>
      <section className="auth-main">
        <form className="auth-card" onSubmit={onSubmit}>
          <h2>Register</h2>
          <AlertBanner>{error}</AlertBanner>
          <label className="field">
            Full name
            <input name="full_name" value={form.full_name} onChange={update} required />
          </label>
          <label className="field">
            Username
            <input name="username" value={form.username} onChange={update} autoComplete="username" required />
          </label>
          <label className="field">
            Email
            <input name="email" type="email" value={form.email} onChange={update} autoComplete="email" required />
          </label>
          <label className="field">
            Password
            <input name="password" type="password" value={form.password} onChange={update} autoComplete="new-password" minLength={8} required />
          </label>
          <label className="field">
            Confirm password
            <input name="confirm" type="password" value={form.confirm} onChange={update} autoComplete="new-password" minLength={8} required />
          </label>
          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? "Creating profile" : "Create profile"}
          </button>
          <p className="footer-note">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </section>
    </div>
  );
}
