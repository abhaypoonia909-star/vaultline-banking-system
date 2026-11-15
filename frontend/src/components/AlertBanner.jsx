export default function AlertBanner({ tone = "error", children, onClose }) {
  if (!children) return null;
  return (
    <div className={`banner banner-${tone}`} role="alert">
      <span>{children}</span>
      {onClose ? (
        <button type="button" onClick={onClose} aria-label="Dismiss">
          ×
        </button>
      ) : null}
    </div>
  );
}
