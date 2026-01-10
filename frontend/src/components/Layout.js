import { Outlet, NavLink } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Users, TrendingUp, FileText, LayoutDashboard, LogOut, Settings as SettingsIcon } from 'lucide-react';

const Layout = ({ onLogout }) => {
  const username = localStorage.getItem('username');

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/employees', icon: Users, label: 'Employees' },
    { to: '/promotions', icon: TrendingUp, label: 'Promotions' },
    { to: '/payslips', icon: FileText, label: 'Payslips' },
    { to: '/settings', icon: SettingsIcon, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-slate-800" data-testid="app-title">PayHub</h1>
              <div className="hidden md:flex space-x-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    data-testid={`nav-${item.label.toLowerCase()}`}
                    className={({ isActive }) =>
                      `flex items-center space-x-2 px-4 py-2 rounded-md transition ${
                        isActive
                          ? 'bg-slate-100 text-slate-900'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`
                    }
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600" data-testid="username-display">Welcome, {username}</span>
              <Button
                data-testid="logout-button"
                variant="outline"
                size="sm"
                onClick={onLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
