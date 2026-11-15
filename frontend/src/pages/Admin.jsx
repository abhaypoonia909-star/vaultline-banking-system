import { useEffect, useState } from "react";
import AlertBanner from "../components/AlertBanner";
import { FlowChart } from "../components/Charts";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import api, { getErrorMessage } from "../services/api";
import { formatMoney, formatWhen, severityTone } from "../services/format";

export default function Admin() {
  const [dashboard, setDashboard] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(null);
  const [working, setWorking] = useState(false);

  function load() {
    return Promise.all([api.get("/api/admin/dashboard"), api.get("/api/admin/accounts")]).then(([dash, rows]) => {
      setDashboard(dash.data);
      setAccounts(rows.data.accounts || []);
    });
  }

  useEffect(() => {
    let active = true;
    load().catch((err) => {
      if (active) setError(getErrorMessage(err, "Admin data could not be loaded."));
    });
    return () => {
      active = false;
    };
  }, []);

  async function deactivate(accountId) {
    setWorking(true);
    setError("");
    try {
      await api.delete(`/api/admin/accounts/${accountId}`);
      setPending(null);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "The account could not be deactivated."));
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Administration" title="Admin dashboard" text="Active accounts can be deactivated. History stays on the ledger, and account numbers are not recycled." />
      <AlertBanner>{error}</AlertBanner>
      {!dashboard && !error ? <LoadingSpinner label="Loading admin data" /> : null}
      {dashboard ? (
        <>
          <section className="stats">
            <StatCard label="Customers" value={dashboard.users} />
            <StatCard label="Active accounts" value={dashboard.accounts} tone="gold" />
            <StatCard label="Balances" value={formatMoney(dashboard.total_balance)} tone="ok" />
            <StatCard label="Failed logins, 24h" value={dashboard.failed_logins_24h} tone="danger" hint={`${dashboard.open_alerts} elevated events`} />
          </section>
          <section className="split">
            <article className="card">
              <div className="card-head"><h2>Bank-wide flow</h2></div>
              <FlowChart deposits={dashboard.deposits_total} withdrawals={dashboard.withdrawals_total} />
            </article>
            <article className="card">
              <div className="card-head"><h2>Elevated events</h2></div>
              {dashboard.recent_alerts.length === 0 ? <p className="empty">No warnings.</p> : (
                <ul className="stack-list">
                  {dashboard.recent_alerts.map((item) => (
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
            </article>
          </section>
          <article className="card">
            <div className="card-head"><h2>Account management</h2></div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Number</th>
                    <th>Name</th>
                    <th>Owner</th>
                    <th>Balance</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.length === 0 ? (
                    <tr><td colSpan="5">No active accounts.</td></tr>
                  ) : accounts.map((account) => (
                    <tr key={account.id}>
                      <td>{account.account_number}</td>
                      <td>{account.holder_name}</td>
                      <td>{account.owner}</td>
                      <td>{formatMoney(account.balance)}</td>
                      <td>
                        {pending === account.id ? (
                          <span className="row-actions">
                            <button type="button" className="btn btn-danger" disabled={working} onClick={() => deactivate(account.id)}>Confirm</button>
                            <button type="button" className="btn btn-ghost" onClick={() => setPending(null)}>Cancel</button>
                          </span>
                        ) : (
                          <button type="button" className="btn btn-ghost" onClick={() => setPending(account.id)}>Deactivate</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        </>
      ) : null}
    </>
  );
}
