import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { FileStack, LayoutDashboard, MessageSquare, Settings, LogOut, Network } from "lucide-react";
import { OfflinePulse } from "../components/OfflinePulse";
import { useAuth } from "../hooks/useAuth";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/documents", label: "Documents", icon: FileStack },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/knowledge-graph", label: "Knowledge Graph", icon: Network },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="flex h-screen bg-ink-900">
      <aside className="flex w-60 flex-shrink-0 flex-col border-r border-ink-700 bg-ink-950/50">
        <Link to="/" className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-rose-400 to-rose-600 font-mono text-sm font-bold text-ink-950 shadow-lg shadow-rose-500/20">
            D
          </div>
          <span className="text-sm font-semibold tracking-wide">DOCBOT 2.0</span>
        </Link>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-rose-500/10 text-rose-400 font-medium"
                    : "text-paper-200 hover:bg-ink-800 hover:text-paper-100"
                }`
              }
            >
              <Icon size={16} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-ink-700 p-3">
          <div className="mb-3 px-2">
            <p className="truncate text-sm font-medium text-paper-100">{user?.full_name}</p>
            <p className="truncate text-xs text-paper-300">{user?.email}</p>
          </div>
          <button
            onClick={handleSignOut}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-paper-300 transition-colors hover:bg-ink-800 hover:text-crimson-400"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-end border-b border-ink-700 px-6 py-3.5">
          <OfflinePulse />
        </header>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
