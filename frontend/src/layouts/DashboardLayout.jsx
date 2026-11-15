import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export default function DashboardLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="shell">
      <Sidebar open={open} onNavigate={() => setOpen(false)} />
      {open ? <button type="button" className="backdrop" aria-label="Close menu" onClick={() => setOpen(false)} /> : null}
      <div className="main">
        <Topbar onMenu={() => setOpen((value) => !value)} />
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
