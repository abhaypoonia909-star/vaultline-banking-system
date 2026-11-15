import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import api, { getErrorMessage } from "../services/api";
import { formatMoney, formatWhen } from "../services/format";

export default function Transactions() {
  const [params, setParams] = useSearchParams();
  const accountId = params.get("account") || "";
  const [accounts, setAccounts] = useState([]);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api
      .get("/api/accounts")
      .then((response) => {
        if (active) setAccounts(response.data.accounts || []);
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "Accounts could not be loaded."));
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setHistory(null);
    const query = accountId ? `?account_id=${accountId}&limit=100` : "?limit=100";
    api
      .get(`/api/transactions/history${query}`)
      .then((response) => {
        if (active) setHistory(response.data);
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "History could not be loaded."));
      });
    return () => {
      active = false;
    };
  }, [accountId]);

  return (
    <>
      <PageHeader
        eyebrow="Ledger"
        title="Transaction history"
        text="Totals come from the database, not from the rows visible on this page."
        action={
          <select
            value={accountId}
            onChange={(event) => {
              const next = event.target.value;
              setParams(next ? { account: next } : {});
            }}
            aria-label="Filter by account"
          >
            <option value="">All accounts</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.account_number}
              </option>
            ))}
          </select>
        }
      />
      <AlertBanner>{error}</AlertBanner>
      {!history && !error ? <LoadingSpinner label="Loading history" /> : null}
      {history ? (
        <>
          <section className="stats">
            <article className="stat tone-ok">
              <p className="stat-label">Deposits</p>
              <p className="stat-value">{formatMoney(history.totals.deposits)}</p>
            </article>
            <article className="stat tone-gold">
              <p className="stat-label">Withdrawals</p>
              <p className="stat-value">{formatMoney(history.totals.withdrawals)}</p>
            </article>
            <article className="stat tone-blue">
              <p className="stat-label">Records</p>
              <p className="stat-value">{history.totals.count}</p>
            </article>
          </section>
          <article className="card">
            {history.transactions.length === 0 ? <p className="empty">Nothing posted yet.</p> : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>When</th>
                      <th>Account</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Balance</th>
                      <th>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.transactions.map((txn) => (
                      <tr key={txn.id}>
                        <td>{formatWhen(txn.created_at)}</td>
                        <td>{txn.account_number}</td>
                        <td className="cap">{txn.txn_type}</td>
                        <td className={txn.txn_type === "deposit" ? "amount-positive" : "amount-negative"}>{formatMoney(txn.amount)}</td>
                        <td>{formatMoney(txn.balance_after)}</td>
                        <td>{txn.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </>
      ) : null}
    </>
  );
}
