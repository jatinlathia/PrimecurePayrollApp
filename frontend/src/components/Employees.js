import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState(null);
  const [formData, setFormData] = useState({
    employee_no: '',
    name: '',
    designation: '',
    date_of_joining: '',
    work_location: '',
    department: '',
    bank_account_no: '',
    salary_components: {
      basic: 0,
      house_rent_allowance: 0,
      transport_allowance: 0,
      fixed_allowance: 0,
      professional_tax: 0
    }
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/employees`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmployees(response.data);
    } catch (error) {
      toast.error('Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      if (editingEmployee) {
        await axios.put(`${API}/employees/${editingEmployee.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Employee updated successfully');
      } else {
        await axios.post(`${API}/employees`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Employee created successfully');
      }
      
      setDialogOpen(false);
      resetForm();
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleEdit = (employee) => {
    setEditingEmployee(employee);
    setFormData(employee);
    setDialogOpen(true);
  };

  const handleDeleteClick = (employee) => {
    setEmployeeToDelete(employee);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/employees/${employeeToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Employee terminated successfully');
      setDeleteDialogOpen(false);
      fetchEmployees();
    } catch (error) {
      toast.error('Failed to terminate employee');
    }
  };

  const resetForm = () => {
    setFormData({
      employee_no: '',
      name: '',
      designation: '',
      date_of_joining: '',
      work_location: '',
      department: '',
      bank_account_no: '',
      salary_components: {
        basic: 0,
        house_rent_allowance: 0,
        transport_allowance: 0,
        fixed_allowance: 0,
        home_collection_visit: 0,
        professional_tax: 0
      }
    });
    setEditingEmployee(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSalaryChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      salary_components: {
        ...prev.salary_components,
        [name]: parseFloat(value) || 0
      }
    }));
  };

  if (loading) {
    return <div className="text-center py-8">Loading employees...</div>;
  }

  return (
    <div data-testid="employees-container">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-slate-800">Employees</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button data-testid="add-employee-button" className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Add Employee</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle data-testid="employee-dialog-title">
                {editingEmployee ? 'Edit Employee' : 'Add New Employee'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="employee_no">Employee No</Label>
                  <Input
                    id="employee_no"
                    data-testid="employee-no-input"
                    name="employee_no"
                    value={formData.employee_no}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    data-testid="employee-name-input"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="designation">Designation</Label>
                  <Input
                    id="designation"
                    data-testid="designation-input"
                    name="designation"
                    value={formData.designation}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date_of_joining">Date of Joining</Label>
                  <Input
                    id="date_of_joining"
                    data-testid="doj-input"
                    name="date_of_joining"
                    type="date"
                    value={formData.date_of_joining}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="work_location">Work Location</Label>
                  <Input
                    id="work_location"
                    data-testid="work-location-input"
                    name="work_location"
                    value={formData.work_location}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Input
                    id="department"
                    data-testid="department-input"
                    name="department"
                    value={formData.department}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="space-y-2 col-span-2">
                  <Label htmlFor="bank_account_no">Bank Account No</Label>
                  <Input
                    id="bank_account_no"
                    data-testid="bank-account-input"
                    name="bank_account_no"
                    value={formData.bank_account_no}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <div className="border-t pt-4 mt-4">
                <h3 className="font-semibold mb-3 text-slate-700">Salary Components (₹)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="basic">Basic</Label>
                    <Input
                      id="basic"
                      data-testid="basic-input"
                      name="basic"
                      type="number"
                      step="0.01"
                      value={formData.salary_components.basic}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="house_rent_allowance">House Rent Allowance</Label>
                    <Input
                      id="house_rent_allowance"
                      data-testid="hra-input"
                      name="house_rent_allowance"
                      type="number"
                      step="0.01"
                      value={formData.salary_components.house_rent_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="transport_allowance">Transport Allowance</Label>
                    <Input
                      id="transport_allowance"
                      data-testid="transport-allowance-input"
                      name="transport_allowance"
                      type="number"
                      step="0.01"
                      value={formData.salary_components.transport_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fixed_allowance">Fixed Allowance</Label>
                    <Input
                      id="fixed_allowance"
                      data-testid="fixed-allowance-input"
                      name="fixed_allowance"
                      type="number"
                      step="0.01"
                      value={formData.salary_components.fixed_allowance}
                      onChange={handleSalaryChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="professional_tax">Professional Tax</Label>
                    <Input
                      id="professional_tax"
                      data-testid="professional-tax-input"
                      name="professional_tax"
                      type="number"
                      step="0.01"
                      value={formData.salary_components.professional_tax}
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
                  data-testid="cancel-button"
                >
                  Cancel
                </Button>
                <Button type="submit" data-testid="submit-employee-button">
                  {editingEmployee ? 'Update' : 'Create'}
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
              <TableHead>Employee No</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Designation</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Date of Joining</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {employees.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                  No employees found. Add your first employee!
                </TableCell>
              </TableRow>
            ) : (
              employees.map((employee) => (
                <TableRow key={employee.id} data-testid={`employee-row-${employee.employee_no}`}>
                  <TableCell className="font-medium">{employee.employee_no}</TableCell>
                  <TableCell>{employee.name}</TableCell>
                  <TableCell>{employee.designation}</TableCell>
                  <TableCell>{employee.department}</TableCell>
                  <TableCell>{employee.date_of_joining}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        data-testid={`edit-employee-${employee.employee_no}`}
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(employee)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        data-testid={`delete-employee-${employee.employee_no}`}
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteClick(employee)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Terminate Employee</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to terminate {employeeToDelete?.name}? This action will soft delete the employee.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-button">Cancel</AlertDialogCancel>
            <AlertDialogAction data-testid="confirm-delete-button" onClick={handleDelete}>
              Terminate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Employees;
