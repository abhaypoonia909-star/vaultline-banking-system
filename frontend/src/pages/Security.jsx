import { useEffect, useState } from "react";
import AlertBanner from "../components/AlertBanner";
import { LoginChart } from "../components/Charts";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import api, { getErrorMessage } from "../services/api";
import { formatWhen, severityTone } from "../services/format";
import { Doughnut } from "react-chartjs-2";
import { doughnutOptions, palette } from "../services/charts";

export default function Security() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api
      .get("/api/security/logs")
      .then((response) => {
        if (active) setData(response.data);
      })
      .catch((err) => {
        if (active) setError(getErrorMessage(err, "Security data could not be loaded."));
      });
    return () => {
      active = false;
    };
  }, []);

  const summary = data?.summary;

  return (
    <>
      <PageHeader
        eyebrow="Defence"
        title="Security monitoring"
        text="Login attempts, repeated failures, and local simulation history. Passwords are never shown."
      />
      <AlertBanner>{error}</AlertBanner>
      {!data && !error ? <LoadingSpinner label="Loading security data" /> : null}
      {summary ? (
        <>
          <section className="stats">
            <StatCard label="Login attempts" value={summary.total_attempts} />
            <StatCard label="Failed" value={summary.failed_attempts} tone="danger" />
            <StatCard label="Successful" value={summary.successful_attempts} tone="ok" />
            <StatCard label="Brute-force alerts" value={summary.brute_force_alerts} tone="gold" hint={`${summary.simulated_attempts} simulated guesses`} />
          </section>
          <section className="split">
            <article className="card">
              <div className="card-head"><h2>Attempts by day</h2></div>
              <LoginChart days={data.daily_logins} />
            </article>
            <article className="card">
              <div className="card-head"><h2>Outcome mix</h2></div>
              <div className="chart-box">
                <Doughnut
                  data={{
                    labels: ["Successful", "Failed"],
                    datasets: [{
                      data: [summary.successful_attempts, summary.failed_attempts],
                      backgroundColor: [palette.ok, palette.danger],
                      borderWidth: 0,
                    }],
                  }}
                  options={doughnutOptions}
                />
              </div>
            </article>
          </section>
          <section className="split">
            <article className="card">
              <div className="card-head"><h2>Security events</h2></div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>When</th>
                      <th>Severity</th>
                      <th>Event</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.logs.length === 0 ? (
                      <tr><td colSpan="3">No events yet.</td></tr>
                    ) : data.logs.map((item) => (
                      <tr key={item.id}>
                        <td>{formatWhen(item.created_at)}</td>
                        <td><span className={`badge badge-${severityTone(item.severity)}`}>{item.severity}</span></td>
                        <td>{item.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
            <article className="card">
              <div className="card-head"><h2>Simulation history</h2></div>
              {data.simulations.length === 0 ? <p className="empty">No local simulations yet.</p> : (
                <ul className="stack-list">
                  {data.simulations.map((item) => (
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
        </>
      ) : null}
    </>
  );
}
