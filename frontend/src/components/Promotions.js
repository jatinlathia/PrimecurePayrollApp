import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Promotions = () => {
  const [promotions, setPromotions] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    new_designation: '',
    promotion_date: '',
    new_salary_components: {
      basic: 0,
      house_rent_allowance: 0,
      transport_allowance: 0,
      fixed_allowance: 0,
      professional_tax: 0
    }
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [promotionsRes, employeesRes] = await Promise.all([
        axios.get(`${API}/promotions`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/employees`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setPromotions(promotionsRes.data);
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
      await axios.post(`${API}/promotions`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Promotion created successfully');
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create promotion');
    }
  };

  const resetForm = () => {
    setFormData({
      employee_id: '',
      new_designation: '',
      promotion_date: '',
      new_salary_components: {
        basic: 0,
        house_rent_allowance: 0,
        transport_allowance: 0,
        fixed_allowance: 0,
        professional_tax: 0
      }
    });
  };

  const handleEmployeeChange = (employeeId) => {
    const employee = employees.find(e => e.id === employeeId);
    if (employee) {
      setFormData(prev => ({
        ...prev,
        employee_id: employeeId,
        new_designation: employee.designation,
        new_salary_components: { ...employee.salary_components }
      }));
    }
  };

  const handleSalaryChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      new_salary_components: {
        ...prev.new_salary_components,
        [name]: parseFloat(value) || 0
      }
    }));
  };

  if (loading) {
    return <div className="text-center py-8">Loading promotions...</div>;
  }

  return (
    <div data-testid="promotions-container">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-slate-800">Promotions</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button data-testid="add-promotion-button" className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Add Promotion</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle data-testid="promotion-dialog-title">Create Promotion</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="employee">Select Employee</Label>
                <Select value={formData.employee_id} onValueChange={handleEmployeeChange}>
                  <SelectTrigger data-testid="employee-select">
                    <SelectValue placeholder="Select an employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>
                        {employee.name} - {employee.designation}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="new_designation">New Designation</Label>
                  <Input
                    id="new_designation"
                    data-testid="new-designation-input"
                    value={formData.new_designation}
                    onChange={(e) => setFormData(prev => ({ ...prev, new_designation: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="promotion_date">Promotion Date</Label>
                  <Input
                    id="promotion_date"
                    data-testid="promotion-date-input"
                    type="date"
                    value={formData.promotion_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, promotion_date: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="border-t pt-4 mt-4">
                <h3 className="font-semibold mb-3 text-slate-700">New Salary Components (₹)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="basic">Basic</Label>
                    <Input
                      id="basic"
                      data-testid="basic-salary-input"
                      name="basic"
                      type="number"
                      step="0.01"
                      value={formData.new_salary_components.basic}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="house_rent_allowance">House Rent Allowance</Label>
                    <Input
                      id="house_rent_allowance"
                      data-testid="hra-salary-input"
                      name="house_rent_allowance"
                      type="number"
                      step="0.01"
                      value={formData.new_salary_components.house_rent_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="transport_allowance">Transport Allowance</Label>
                    <Input
                      id="transport_allowance"
                      data-testid="transport-salary-input"
                      name="transport_allowance"
                      type="number"
                      step="0.01"
                      value={formData.new_salary_components.transport_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fixed_allowance">Fixed Allowance</Label>
                    <Input
                      id="fixed_allowance"
                      data-testid="fixed-salary-input"
                      name="fixed_allowance"
                      type="number"
                      step="0.01"
                      value={formData.new_salary_components.fixed_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="professional_tax">Professional Tax</Label>
                    <Input
                      id="professional_tax"
                      data-testid="professional-tax-salary-input"
                      name="professional_tax"
                      type="number"
                      step="0.01"
                      value={formData.new_salary_components.professional_tax}
                      onChange={handleSalaryChange}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                  data-testid="cancel-promotion-button"
                >
                  Cancel
                </Button>
                <Button type="submit" data-testid="submit-promotion-button">
                  Create Promotion
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
              <TableHead>Old Designation</TableHead>
              <TableHead>New Designation</TableHead>
              <TableHead>Old Salary</TableHead>
              <TableHead>New Salary</TableHead>
              <TableHead>Promotion Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {promotions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                  No promotions recorded yet.
                </TableCell>
              </TableRow>
            ) : (
              promotions.map((promotion) => (
                <TableRow key={promotion.id} data-testid={`promotion-row-${promotion.id}`}>
                  <TableCell className="font-medium">{promotion.employee_name}</TableCell>
                  <TableCell>{promotion.old_designation}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center space-x-1">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span>{promotion.new_designation}</span>
                    </span>
                  </TableCell>
                  <TableCell>₹{promotion.old_salary.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</TableCell>
                  <TableCell className="text-green-600 font-semibold">₹{promotion.new_salary.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</TableCell>
                  <TableCell>{promotion.promotion_date}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default Promotions;
