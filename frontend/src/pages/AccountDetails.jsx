import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import api, { getErrorMessage } from "../services/api";
import { formatMoney, formatWhen } from "../services/format";

export default function AccountDetails() {
  const { id } = useParams();
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setPayload(null);
    setError("");
    api
      .get(`/api/accounts/${id}`)
      .then((response) => {
        if (active) setPayload(response.data);
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "That account is not available."));
      });
    return () => {
      active = false;
    };
  }, [id]);

  const account = payload?.account;

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title={account ? account.account_number : "Account details"}
        text={account ? account.holder_name : "Only the account owner can view this record."}
        action={<Link className="btn btn-ghost" to="/accounts">All accounts</Link>}
      />
      <AlertBanner>{error}</AlertBanner>
      {!payload && !error ? <LoadingSpinner label="Loading account" /> : null}
      {account ? (
        <>
          <section className="stats">
            <article className="stat tone-blue">
              <p className="stat-label">Balance</p>
              <p className="stat-value">{formatMoney(account.balance)}</p>
            </article>
            <article className="stat tone-gold">
              <p className="stat-label">Opened</p>
              <p className="stat-value small">{formatWhen(account.created_at)}</p>
            </article>
            <article className="stat tone-ok">
              <p className="stat-label">PIN</p>
              <p className="stat-value small">Protected</p>
              <p className="stat-hint">Required for deposits and withdrawals</p>
            </article>
          </section>
          <article className="card">
            <div className="card-head">
              <h2>Latest activity</h2>
              <Link to={`/transactions?account=${account.id}`}>Full history</Link>
            </div>
            {payload.transactions.length === 0 ? <p className="empty">No transactions on this account.</p> : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>When</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Balance after</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payload.transactions.map((txn) => (
                      <tr key={txn.id}>
                        <td>{formatWhen(txn.created_at)}</td>
                        <td className="cap">{txn.txn_type}</td>
                        <td>{formatMoney(txn.amount)}</td>
                        <td>{formatMoney(txn.balance_after)}</td>
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
