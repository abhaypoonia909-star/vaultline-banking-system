import { Route, Routes } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import AccountDetails from "./pages/AccountDetails";
import Accounts from "./pages/Accounts";
import Admin from "./pages/Admin";
import Dashboard from "./pages/Dashboard";
import Deposit from "./pages/Deposit";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Security from "./pages/Security";
import Simulation from "./pages/Simulation";
import Transactions from "./pages/Transactions";
import Withdraw from "./pages/Withdraw";

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="accounts" element={<Accounts />} />
            <Route path="accounts/:id" element={<AccountDetails />} />
            <Route path="deposit" element={<Deposit />} />
            <Route path="withdraw" element={<Withdraw />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="security" element={<Security />} />
            <Route path="simulation" element={<Simulation />} />
            <Route path="profile" element={<Profile />} />
            <Route element={<ProtectedRoute role="admin" />}>
              <Route path="admin" element={<Admin />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  );
}
