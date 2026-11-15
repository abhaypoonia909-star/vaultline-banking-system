import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import { FlowChart, LoginChart } from "../components/Charts";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import api, { getErrorMessage } from "../services/api";
import { formatMoney, formatWhen, severityTone } from "../services/format";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([api.get("/api/accounts"), api.get("/api/transactions/history?limit=6"), api.get("/api/security/logs")])
      .then(([accounts, history, security]) => {
        if (!active) return;
        setData({
          accounts: accounts.data,
          history: history.data,
          security: security.data,
        });
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "Dashboard data could not be loaded."));
      });
    return () => {
      active = false;
    };
  }, []);

  const alerts = (data?.security.logs || []).filter((item) => item.severity === "warning" || item.severity === "critical").slice(0, 4);
  const attempts = (data?.security.attempts || []).filter((item) => !item.is_simulation).slice(0, 5);

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        text="Balances, recent ledger activity, and security signals from this application."
      />
      <AlertBanner>{error}</AlertBanner>
      {!data && !error ? <LoadingSpinner label="Loading dashboard" /> : null}
      {data ? (
        <>
          <section className="stats">
            <StatCard label="Total balance" value={formatMoney(data.accounts.total_balance)} hint="Across your active accounts" />
            <StatCard label="Accounts" value={data.accounts.count} tone="gold" hint="Limit of 10 per customer" />
            <StatCard label="Deposits" value={formatMoney(data.history.totals.deposits)} tone="ok" hint={`${data.history.totals.count} ledger rows`} />
            <StatCard label="Security alerts" value={data.security.summary.brute_force_alerts} tone="danger" hint="Repeated failures and weak passwords" />
          </section>
          <section className="split">
            <article className="card">
              <div className="card-head">
                <h2>Money movement</h2>
                <Link to="/transactions">History</Link>
              </div>
              <FlowChart deposits={data.history.totals.deposits} withdrawals={data.history.totals.withdrawals} />
            </article>
            <article className="card">
              <div className="card-head">
                <h2>Login activity</h2>
                <Link to="/security">Monitoring</Link>
              </div>
              <LoginChart days={data.security.daily_logins} />
            </article>
          </section>
          <section className="split">
            <article className="card">
              <div className="card-head">
                <h2>Recent transactions</h2>
              </div>
              {data.history.transactions.length === 0 ? <p className="empty">No transactions yet.</p> : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>When</th>
                        <th>Type</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.history.transactions.map((txn) => (
                        <tr key={txn.id}>
                          <td>{formatWhen(txn.created_at)}</td>
                          <td className="cap">{txn.txn_type}</td>
                          <td className={txn.txn_type === "deposit" ? "amount-positive" : "amount-negative"}>
                            {formatMoney(txn.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
            <article className="card">
              <div className="card-head">
                <h2>Security alerts</h2>
              </div>
              {alerts.length === 0 ? <p className="empty">No warnings right now.</p> : (
                <ul className="stack-list">
                  {alerts.map((item) => (
                    <li key={item.id}>
                      <span className={`badge badge-${severityTone(item.severity)}`}>{item.severity}</span>
                      <div>
                        <strong>{item.message}</strong>
                        <p>{formatWhen(item.created_at)}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <h3>Recent sign-ins</h3>
              {attempts.length === 0 ? <p className="empty">No login attempts yet.</p> : (
                <ul className="stack-list compact">
                  {attempts.map((item) => (
                    <li key={item.id}>
                      <span className={`badge badge-${item.success ? "ok" : "danger"}`}>{item.success ? "success" : "failed"}</span>
                      <div>
                        <strong>{item.username}</strong>
                        <p>{formatWhen(item.created_at)}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </section>
        </>
      ) : null}
    </>
  );
}
