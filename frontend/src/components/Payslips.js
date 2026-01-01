import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Download } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Payslips = () => {
  const [payslips, setPayslips] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    month: '',
    year: new Date().getFullYear().toString(),
    paid_days: 30,
    lop_days: 0
  });

  const months = [
    { value: '1', label: 'January' },
    { value: '2', label: 'February' },
    { value: '3', label: 'March' },
    { value: '4', label: 'April' },
    { value: '5', label: 'May' },
    { value: '6', label: 'June' },
    { value: '7', label: 'July' },
    { value: '8', label: 'August' },
    { value: '9', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' }
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [payslipsRes, employeesRes] = await Promise.all([
        axios.get(`${API}/payslips`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/employees`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setPayslips(payslipsRes.data);
      setEmployees(employeesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const payload = {
        ...formData,
        month: parseInt(formData.month),
        year: parseInt(formData.year),
        paid_days: parseInt(formData.paid_days),
        lop_days: parseInt(formData.lop_days)
      };
      await axios.post(`${API}/payslips/generate`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Payslip generated successfully');
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate payslip');
    }
  };

  const handleDownload = async (payslipId, employeeNo, month, year) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/payslips/download/${payslipId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payslip_${employeeNo}_${months[month - 1].label}_${year}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Payslip downloaded successfully');
    } catch (error) {
      toast.error('Failed to download payslip');
    }
  };

  const resetForm = () => {
    setFormData({
      employee_id: '',
      month: '',
      year: new Date().getFullYear().toString(),
      paid_days: 30,
      lop_days: 0
    });
  };

  if (loading) {
    return <div className="text-center py-8">Loading payslips...</div>;
  }

  return (
    <div data-testid="payslips-container">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-slate-800">Payslips</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button data-testid="generate-payslip-button" className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Generate Payslip</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle data-testid="payslip-dialog-title">Generate Payslip</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="employee">Select Employee</Label>
                <Select value={formData.employee_id} onValueChange={(value) => setFormData(prev => ({ ...prev, employee_id: value }))}>
                  <SelectTrigger data-testid="payslip-employee-select">
                    <SelectValue placeholder="Select an employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>
                        {employee.name} ({employee.employee_no})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="month">Month</Label>
                  <Select value={formData.month} onValueChange={(value) => setFormData(prev => ({ ...prev, month: value }))}>
                    <SelectTrigger data-testid="month-select">
                      <SelectValue placeholder="Select month" />
                    </SelectTrigger>
                    <SelectContent>
                      {months.map((month) => (
                        <SelectItem key={month.value} value={month.value}>
                          {month.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="year">Year</Label>
                  <Input
                    id="year"
                    data-testid="year-input"
                    type="number"
                    value={formData.year}
                    onChange={(e) => setFormData(prev => ({ ...prev, year: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="paid_days">Paid Days</Label>
                  <Input
                    id="paid_days"
                    data-testid="paid-days-input"
                    type="number"
                    value={formData.paid_days}
                    onChange={(e) => setFormData(prev => ({ ...prev, paid_days: e.target.value }))}
                    required
                    min="0"
                    max="31"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lop_days">LOP Days</Label>
                  <Input
                    id="lop_days"
                    data-testid="lop-days-input"
                    type="number"
                    value={formData.lop_days}
                    onChange={(e) => setFormData(prev => ({ ...prev, lop_days: e.target.value }))}
                    required
                    min="0"
                    max="31"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                  data-testid="cancel-payslip-button"
                >
                  Cancel
                </Button>
                <Button type="submit" data-testid="submit-payslip-button">
                  Generate
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Employee Name</TableHead>
              <TableHead>Employee No</TableHead>
              <TableHead>Month/Year</TableHead>
              <TableHead>Paid Days</TableHead>
              <TableHead>LOP Days</TableHead>
              <TableHead>Net Payable</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payslips.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                  No payslips generated yet.
                </TableCell>
              </TableRow>
            ) : (
              payslips.map((payslip) => (
                <TableRow key={payslip.id} data-testid={`payslip-row-${payslip.id}`}>
                  <TableCell className="font-medium">{payslip.employee_name}</TableCell>
                  <TableCell>{payslip.employee_no}</TableCell>
                  <TableCell>{months[payslip.month - 1].label} {payslip.year}</TableCell>
                  <TableCell>{payslip.paid_days}</TableCell>
                  <TableCell>{payslip.lop_days}</TableCell>
                  <TableCell className="font-semibold text-green-600">
                    ₹{payslip.net_payable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      data-testid={`download-payslip-${payslip.employee_no}`}
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(payslip.id, payslip.employee_no, payslip.month, payslip.year)}
                      className="flex items-center space-x-2"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download</span>
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default Payslips;
