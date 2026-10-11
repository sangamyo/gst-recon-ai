import { NavLink } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/clients", label: "Clients" },
  { to: "/upload", label: "Upload" },
  { to: "/jobs", label: "Jobs" },
  { to: "/reports", label: "Reports" },
];

export const AppShell: React.FC<React.PropsWithChildren> = ({ children }) => {
  const { user, logout } = useAuthContext();
  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="w-64 bg-secondary text-white">
        <div className="p-6 text-2xl font-semibold">GSTRecon AI</div>
        <nav className="flex flex-col gap-2 p-4">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm font-medium ${isActive ? "bg-primary text-white" : "text-slate-200"}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1">
        <header className="flex items-center justify-between border-b bg-white px-6 py-4">
          <div>
            <p className="text-sm text-slate-500">Welcome back,</p>
            <p className="text-lg font-semibold text-slate-900">{user?.name}</p>
          </div>
          <button
            onClick={logout}
            className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Logout
          </button>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
};
