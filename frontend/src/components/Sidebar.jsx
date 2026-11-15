import { NavLink } from "react-router-dom";
import mark from "../assets/mark.svg";
import { useAuth } from "../hooks/useAuth";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/accounts", label: "My accounts" },
  { to: "/deposit", label: "Deposit" },
  { to: "/withdraw", label: "Withdraw" },
  { to: "/transactions", label: "Transactions" },
  { to: "/security", label: "Security" },
  { to: "/simulation", label: "Simulation" },
  { to: "/profile", label: "Profile" },
];

export default function Sidebar({ open, onNavigate }) {
  const { user } = useAuth();
  const items = user?.role === "admin" ? [...links.slice(0, 7), { to: "/admin", label: "Admin" }, links[7]] : links;

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="brand-lockup">
        <img src={mark} alt="" width="42" height="42" />
        <div>
          <strong>Vaultline</strong>
          <span>Banking console</span>
        </div>
      </div>
      <p className="nav-section">Customer</p>
      <nav>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            onClick={onNavigate}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <p className="sidebar-note">Local demonstration. Simulations never leave this application.</p>
    </aside>
  );
}
