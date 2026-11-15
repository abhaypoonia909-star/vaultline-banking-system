import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="screen-center">
      <div className="card narrow">
        <p className="eyebrow">404</p>
        <h1>That page is not on the books.</h1>
        <p className="lede">The address does not match a screen in this console.</p>
        <Link className="btn btn-primary" to="/">Return to the dashboard</Link>
      </div>
    </div>
  );
}
