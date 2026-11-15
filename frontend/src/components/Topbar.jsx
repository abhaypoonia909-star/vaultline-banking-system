import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Topbar({ onMenu }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function signOut() {
    await logout();
    navigate("/login");
  }

  return (
    <header className="topbar">
      <button type="button" className="menu-toggle" onClick={onMenu} aria-label="Open navigation">
        Menu
      </button>
      <p className="demo-pill">Demo environment</p>
      <div className="who">
        <div>
          <strong>{user?.full_name}</strong>
          <span className={`badge badge-${user?.role === "admin" ? "warn" : "info"}`}>{user?.role}</span>
        </div>
        <button type="button" className="btn btn-ghost" onClick={signOut}>
          Sign out
        </button>
      </div>
    </header>
  );
}
