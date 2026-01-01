import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Wallet, FileText } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_active_employees: 0,
    total_monthly_payroll: 0,
    total_payslips_generated: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Active Employees',
      value: stats.total_active_employees,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      testId: 'active-employees-card'
    },
    {
      title: 'Total Monthly Payroll',
      value: `₹${stats.total_monthly_payroll.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      icon: Wallet,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      testId: 'total-payroll-card'
    },
    {
      title: 'Payslips Generated',
      value: stats.total_payslips_generated,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      testId: 'payslips-generated-card'
    }
  ];

  if (loading) {
    return <div className="text-center py-8">Loading dashboard...</div>;
  }

  return (
    <div data-testid="dashboard-container">
      <h2 className="text-3xl font-bold text-slate-800 mb-8">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statCards.map((card) => (
          <Card key={card.title} data-testid={card.testId} className="hover:shadow-lg transition">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">
                {card.title}
              </CardTitle>
              <div className={`${card.bgColor} ${card.color} p-2 rounded-lg`}>
                <card.icon className="h-5 w-5" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-800" data-testid={`${card.testId}-value`}>
                {card.value}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
