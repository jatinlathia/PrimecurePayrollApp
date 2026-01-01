import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Plus, Download, ChevronDown, Edit2, Save, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Payslips = () => {
  const [payslips, setPayslips] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPayslip, setEditingPayslip] = useState(null);
  const [editFormData, setEditFormData] = useState({
    paid_days: 30,
    lop_days: 0
  });
  const [formData, setFormData] = useState({
    employee_id: '',
    month: '',
    year: new Date().getFullYear().toString(),
    paid_days: 30,
    lop_days: 0,
    home_collection_visit: 0
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
        lop_days: parseInt(formData.lop_days),
        home_collection_visit: parseFloat(formData.home_collection_visit) || 0
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
      
      // Create blob from response
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      // Create temporary link and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `payslip_${employeeNo}_${months[month - 1].label}_${year}.pdf`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
      
      toast.success('Payslip downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error(error.response?.data?.detail || 'Failed to download payslip');
    }
  };

  const resetForm = () => {
    setFormData({
      employee_id: '',
      month: '',
      year: new Date().getFullYear().toString(),
      paid_days: 30,
      lop_days: 0,
      home_collection_visit: 0
    });
  };

  const handleEditPayslip = (payslip) => {
    setEditingPayslip(payslip.id);
    setEditFormData({
      paid_days: payslip.paid_days,
      lop_days: payslip.lop_days
    });
  };

  const handleCancelEdit = () => {
    setEditingPayslip(null);
    setEditFormData({ paid_days: 30, lop_days: 0 });
  };

  const handleSaveEdit = async (payslip) => {
    try {
      const token = localStorage.getItem('token');
      
      // Delete old payslip
      await axios.delete(`${API}/payslips/${payslip.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Generate new payslip with updated values
      const payload = {
        employee_id: payslip.employee_id,
        month: payslip.month,
        year: payslip.year,
        paid_days: parseInt(editFormData.paid_days),
        lop_days: parseInt(editFormData.lop_days)
      };
      
      await axios.post(`${API}/payslips/generate`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Payslip updated successfully');
      setEditingPayslip(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update payslip');
    }
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

              <div className="space-y-2">
                <Label htmlFor="home_collection_visit">Home Collection - Visit (₹) <span className="text-slate-500 text-xs">(Optional)</span></Label>
                <Input
                  id="home_collection_visit"
                  data-testid="home-collection-visit-input"
                  type="number"
                  step="0.01"
                  value={formData.home_collection_visit}
                  onChange={(e) => setFormData(prev => ({ ...prev, home_collection_visit: e.target.value }))}
                  placeholder="Enter amount for this month"
                  min="0"
                />
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

      <div className="space-y-4">
        {payslips.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-slate-500">
            No payslips generated yet.
          </div>
        ) : (
          <Accordion type="single" collapsible className="space-y-3">
            {payslips.map((payslip) => (
              <AccordionItem 
                key={payslip.id} 
                value={payslip.id}
                className="bg-white rounded-lg shadow border-none"
                data-testid={`payslip-accordion-${payslip.id}`}
              >
                <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-slate-50 rounded-t-lg">
                  <div className="flex items-center justify-between w-full pr-4">
                    <div className="flex items-center space-x-8">
                      <div>
                        <div className="font-semibold text-slate-800">{payslip.employee_name}</div>
                        <div className="text-sm text-slate-500">{payslip.employee_no}</div>
                      </div>
                      <div className="text-sm">
                        <div className="font-medium text-slate-700">{months[payslip.month - 1].label} {payslip.year}</div>
                        <div className="text-slate-500">Paid: {payslip.paid_days} days | LOP: {payslip.lop_days} days</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-sm text-slate-500">Net Payable</div>
                        <div className="text-lg font-bold text-green-600">
                          ₹{payslip.net_payable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-6 pt-2">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Earnings Card */}
                    <Card>
                      <CardHeader className="bg-blue-50 pb-3">
                        <CardTitle className="text-base text-blue-900">Earnings</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-2">
                        {Object.entries(payslip.earnings).map(([key, value]) => (
                          <div key={key} className="flex justify-between items-center py-1">
                            <span className="text-sm text-slate-600">{key}</span>
                            <span className="font-medium text-slate-800">
                              ₹{value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                        ))}
                        <div className="border-t pt-2 mt-2">
                          <div className="flex justify-between items-center font-semibold">
                            <span className="text-slate-700">Gross Earnings</span>
                            <span className="text-blue-600">
                              ₹{payslip.gross_earnings.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Deductions Card */}
                    <Card>
                      <CardHeader className="bg-red-50 pb-3">
                        <CardTitle className="text-base text-red-900">Deductions</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-2">
                        {Object.entries(payslip.deductions).length > 0 ? (
                          Object.entries(payslip.deductions).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center py-1">
                              <span className="text-sm text-slate-600">{key}</span>
                              <span className="font-medium text-slate-800">
                                ₹{value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="text-sm text-slate-500 py-1">No deductions</div>
                        )}
                        <div className="border-t pt-2 mt-2">
                          <div className="flex justify-between items-center font-semibold">
                            <span className="text-slate-700">Total Deductions</span>
                            <span className="text-red-600">
                              ₹{payslip.total_deductions.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Attendance & Actions */}
                  <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-6">
                        {editingPayslip === payslip.id ? (
                          <>
                            <div className="flex items-center space-x-2">
                              <Label htmlFor={`paid-days-${payslip.id}`} className="text-sm">Paid Days:</Label>
                              <Input
                                id={`paid-days-${payslip.id}`}
                                data-testid={`edit-paid-days-${payslip.id}`}
                                type="number"
                                min="0"
                                max="31"
                                value={editFormData.paid_days}
                                onChange={(e) => setEditFormData(prev => ({ ...prev, paid_days: e.target.value }))}
                                className="w-20 h-8"
                              />
                            </div>
                            <div className="flex items-center space-x-2">
                              <Label htmlFor={`lop-days-${payslip.id}`} className="text-sm">LOP Days:</Label>
                              <Input
                                id={`lop-days-${payslip.id}`}
                                data-testid={`edit-lop-days-${payslip.id}`}
                                type="number"
                                min="0"
                                max="31"
                                value={editFormData.lop_days}
                                onChange={(e) => setEditFormData(prev => ({ ...prev, lop_days: e.target.value }))}
                                className="w-20 h-8"
                              />
                            </div>
                          </>
                        ) : (
                          <>
                            <div className="text-sm">
                              <span className="text-slate-600">Paid Days:</span>
                              <span className="ml-2 font-semibold text-slate-800">{payslip.paid_days}</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-slate-600">LOP Days:</span>
                              <span className="ml-2 font-semibold text-slate-800">{payslip.lop_days}</span>
                            </div>
                          </>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {editingPayslip === payslip.id ? (
                          <>
                            <Button
                              data-testid={`save-payslip-${payslip.id}`}
                              size="sm"
                              onClick={() => handleSaveEdit(payslip)}
                              className="flex items-center space-x-1"
                            >
                              <Save className="h-4 w-4" />
                              <span>Save</span>
                            </Button>
                            <Button
                              data-testid={`cancel-edit-${payslip.id}`}
                              variant="outline"
                              size="sm"
                              onClick={handleCancelEdit}
                              className="flex items-center space-x-1"
                            >
                              <X className="h-4 w-4" />
                              <span>Cancel</span>
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              data-testid={`edit-payslip-${payslip.id}`}
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditPayslip(payslip)}
                              className="flex items-center space-x-1"
                            >
                              <Edit2 className="h-4 w-4" />
                              <span>Edit</span>
                            </Button>
                            <Button
                              data-testid={`download-payslip-${payslip.employee_no}`}
                              variant="default"
                              size="sm"
                              onClick={() => handleDownload(payslip.id, payslip.employee_no, payslip.month, payslip.year)}
                              className="flex items-center space-x-1"
                            >
                              <Download className="h-4 w-4" />
                              <span>Download PDF</span>
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        )}
      </div>
    </div>
  );
};

export default Payslips;
