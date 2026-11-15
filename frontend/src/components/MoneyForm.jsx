import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { getErrorMessage } from "../services/api";
import { formatMoney } from "../services/format";
import AlertBanner from "./AlertBanner";
import LoadingSpinner from "./LoadingSpinner";
import PageHeader from "./PageHeader";

export default function MoneyForm({ mode }) {
  const deposit = mode === "deposit";
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;
    api
      .get("/api/accounts")
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
  }, []);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const response = await api.post(deposit ? "/api/transactions/deposit" : "/api/transactions/withdraw", {
        account_id: Number(accountId),
        amount,
        pin,
      });
      setSuccess(`New balance ${formatMoney(response.data.balance)}.`);
      setAmount("");
      setPin("");
      const refreshed = await api.get("/api/accounts");
      setAccounts(refreshed.data.accounts || []);
    } catch (err) {
      setError(getErrorMessage(err, "The transaction was declined."));
    } finally {
      setSubmitting(false);
    }
  }

  const selected = accounts.find((account) => String(account.id) === accountId);

  return (
    <>
      <PageHeader
        eyebrow={deposit ? "Money in" : "Money out"}
        title={deposit ? "Deposit" : "Withdraw"}
        text="A 4-digit PIN confirms the movement. The ledger updates only after the database transaction commits."
      />
      <AlertBanner tone="error" onClose={() => setError("")}>{error}</AlertBanner>
      <AlertBanner tone="success" onClose={() => setSuccess("")}>{success}</AlertBanner>
      {loading ? <LoadingSpinner label="Loading accounts" /> : null}
      {!loading && accounts.length === 0 ? (
        <div className="empty">
          <p>Open an account before moving money.</p>
          <Link className="btn btn-primary" to="/accounts">Create an account</Link>
        </div>
      ) : null}
      {accounts.length > 0 ? (
        <form className="card form narrow" onSubmit={onSubmit}>
          <label className="field">
            Account
            <select value={accountId} onChange={(event) => setAccountId(event.target.value)} required>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_number} · {account.holder_name} · {formatMoney(account.balance)}
                </option>
              ))}
            </select>
          </label>
          {selected ? <p className="stat-hint">Available {formatMoney(selected.balance)}</p> : null}
          <label className="field">
            Amount
            <input
              inputMode="decimal"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder="0.00"
              required
            />
          </label>
          <label className="field">
            PIN
            <input
              value={pin}
              onChange={(event) => setPin(event.target.value)}
              inputMode="numeric"
              autoComplete="off"
              maxLength={4}
              required
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting" : deposit ? "Deposit funds" : "Withdraw funds"}
          </button>
        </form>
      ) : null}
    </>
  );
}
