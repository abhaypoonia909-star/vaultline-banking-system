import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../hooks/useAuth";
import api, { getErrorMessage } from "../services/api";
import { formatWhen } from "../services/format";

export default function Simulation() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [attempts, setAttempts] = useState(6);
  const [acknowledge, setAcknowledge] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    let active = true;
    const request = user?.role === "admin" ? api.get("/api/admin/accounts") : api.get("/api/accounts");
    request
      .then((response) => {
        if (!active) return;
        const rows = response.data.accounts || [];
        setAccounts(rows);
        if (rows[0]) setAccountId(String(rows[0].id));
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "Accounts could not be loaded."));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [user]);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    setSubmitting(true);
    try {
      const response = await api.post("/api/security/brute-force-simulation", {
        account_id: Number(accountId),
        attempts: Number(attempts),
        acknowledge,
      });
      setResult(response.data);
    } catch (err) {
      setError(getErrorMessage(err, "The simulation did not run."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Local only"
        title="Brute-force simulation"
        text="This checks one account in this application against six common weak passwords from the original program. It cannot accept a custom list, and it never reveals a password."
      />
      <p className="notice">The simulation stops at the first match, records each guess as a simulated attempt, and raises an alert when failures repeat or a weak password matches.</p>
      <AlertBanner>{error}</AlertBanner>
      {loading ? <LoadingSpinner label="Loading accounts" /> : null}
      {!loading && accounts.length === 0 ? (
        <div className="empty">
          <p>Create an account before running the demonstration.</p>
          <Link className="btn btn-primary" to="/accounts">Open an account</Link>
        </div>
      ) : null}
      {accounts.length > 0 ? (
        <section className="split">
          <form className="card form" onSubmit={onSubmit}>
            <label className="field">
              Local account
              <select value={accountId} onChange={(event) => setAccountId(event.target.value)} required>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.account_number} · {account.holder_name}
                    {account.owner ? ` · ${account.owner}` : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Attempts ({attempts})
              <input
                type="range"
                min="1"
                max="6"
                value={attempts}
                onChange={(event) => setAttempts(Number(event.target.value))}
              />
            </label>
            <label className="checkline">
              <input type="checkbox" checked={acknowledge} onChange={(event) => setAcknowledge(event.target.checked)} />
              <span>I understand this runs only against a local demo account in this application.</span>
            </label>
            <button className="btn btn-primary" type="submit" disabled={submitting || !acknowledge}>
              {submitting ? "Running" : "Run simulation"}
            </button>
          </form>
          <article className="card">
            <h2>Result</h2>
            {!result ? <p className="empty">No simulation in this session yet.</p> : (
              <dl className="kv">
                <div><dt>Account</dt><dd>{result.account_number}</dd></div>
                <div><dt>Attempts run</dt><dd>{result.attempts_run}</dd></div>
                <div><dt>Failures</dt><dd>{result.failed_guesses}</dd></div>
                <div><dt>Matches</dt><dd>{result.successful_guesses}</dd></div>
                <div><dt>Weak password</dt><dd>{result.weak_password_detected ? "Detected, not disclosed" : "Not in the demo list"}</dd></div>
                <div><dt>Repeated failures</dt><dd>{result.repeated_failure_alert ? "Alert recorded" : "Below threshold"}</dd></div>
                <div><dt>Started</dt><dd>{formatWhen(result.started_at)}</dd></div>
                <div><dt>Finished</dt><dd>{formatWhen(result.finished_at)}</dd></div>
              </dl>
            )}
            {result ? <p className="footer-note">{result.message}</p> : null}
          </article>
        </section>
      ) : null}
    </>
  );
}
