export default function PageHeader({ eyebrow, title, text, action }) {
  return (
    <header className="page-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {text ? <p className="lede">{text}</p> : null}
      </div>
      {action || null}
    </header>
  );
}
