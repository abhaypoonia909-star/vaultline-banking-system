import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import api, { getErrorMessage } from "../services/api";
import { formatMoney, formatWhen } from "../services/format";

const empty = { holder_name: "", initial_balance: "0.00", pin: "" };

export default function Accounts() {
  const [accounts, setAccounts] = useState(null);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function load() {
    return api.get("/api/accounts").then((response) => setAccounts(response.data));
  }

  useEffect(() => {
    let active = true;
    load()
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "Accounts could not be loaded."));
      });
    return () => {
      active = false;
    };
  }, []);

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const response = await api.post("/api/accounts", {
        holder_name: form.holder_name.trim(),
        initial_balance: form.initial_balance || "0",
        pin: form.pin,
      });
      setSuccess(`Opened ${response.data.account.account_number}.`);
      setForm(empty);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "The account could not be opened."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Ledger" title="My accounts" text="Each customer can hold up to 10 active accounts. Numbers are issued once and are not reused." />
      <AlertBanner tone="error" onClose={() => setError("")}>{error}</AlertBanner>
      <AlertBanner tone="success" onClose={() => setSuccess("")}>{success}</AlertBanner>
      {!accounts && !error ? <LoadingSpinner label="Loading accounts" /> : null}
      {accounts ? (
        <section className="split">
          <article className="card">
            <div className="card-head">
              <h2>{accounts.count} active · {formatMoney(accounts.total_balance)}</h2>
            </div>
            {accounts.accounts.length === 0 ? <p className="empty">No accounts yet.</p> : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Number</th>
                      <th>Name</th>
                      <th>Balance</th>
                      <th>Opened</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.accounts.map((account) => (
                      <tr key={account.id}>
                        <td><Link to={`/accounts/${account.id}`}>{account.account_number}</Link></td>
                        <td>{account.holder_name}</td>
                        <td>{formatMoney(account.balance)}</td>
                        <td>{formatWhen(account.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
          <form className="card form" onSubmit={onSubmit}>
            <h2>Open an account</h2>
            <label className="field">
              Account name
              <input name="holder_name" value={form.holder_name} onChange={update} required />
            </label>
            <label className="field">
              Opening balance
              <input name="initial_balance" value={form.initial_balance} onChange={update} inputMode="decimal" required />
            </label>
            <label className="field">
              4-digit PIN
              <input name="pin" value={form.pin} onChange={update} inputMode="numeric" autoComplete="off" maxLength={4} required />
            </label>
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Opening" : "Open account"}
            </button>
          </form>
        </section>
      ) : null}
    </>
  );
}
