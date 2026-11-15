import { useState } from "react";
import AlertBanner from "../components/AlertBanner";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../hooks/useAuth";
import api, { getErrorMessage } from "../services/api";
import { formatWhen } from "../services/format";

export default function Profile() {
  const { user } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (next !== confirm) {
      setError("New passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/auth/change-password", {
        current_password: current,
        new_password: next,
      });
      setSuccess("Password updated. This session stays signed in.");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setError(getErrorMessage(err, "Password was not changed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Customer" title="Profile" text="Identity comes from the signed-in session. The password hash never leaves the server." />
      <section className="split">
        <article className="card">
          <dl className="kv">
            <div><dt>Name</dt><dd>{user.full_name}</dd></div>
            <div><dt>Username</dt><dd>{user.username}</dd></div>
            <div><dt>Email</dt><dd>{user.email}</dd></div>
            <div><dt>Role</dt><dd className="cap">{user.role}</dd></div>
            <div><dt>Joined</dt><dd>{formatWhen(user.created_at)}</dd></div>
          </dl>
        </article>
        <form className="card form" onSubmit={onSubmit}>
          <h2>Change password</h2>
          <AlertBanner tone="error" onClose={() => setError("")}>{error}</AlertBanner>
          <AlertBanner tone="success" onClose={() => setSuccess("")}>{success}</AlertBanner>
          <label className="field">
            Current password
            <input type="password" value={current} onChange={(event) => setCurrent(event.target.value)} autoComplete="current-password" required />
          </label>
          <label className="field">
            New password
            <input type="password" value={next} onChange={(event) => setNext(event.target.value)} autoComplete="new-password" minLength={8} required />
          </label>
          <label className="field">
            Confirm new password
            <input type="password" value={confirm} onChange={(event) => setConfirm(event.target.value)} autoComplete="new-password" minLength={8} required />
          </label>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Updating" : "Update password"}
          </button>
        </form>
      </section>
    </>
  );
}
