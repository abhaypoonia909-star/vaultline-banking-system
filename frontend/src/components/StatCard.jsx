export default function StatCard({ label, value, hint, tone = "blue" }) {
  return (
    <article className={`stat tone-${tone}`}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {hint ? <p className="stat-hint">{hint}</p> : null}
    </article>
  );
}
