import { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { KeyRound } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Settings = () => {
  const [formData, setFormData] = useState({
    current_password: '',
    new_username: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.new_password !== formData.confirm_password) {
      toast.error('New password and confirm password do not match');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/credentials`, {
        current_password: formData.current_password,
        new_username: formData.new_username || undefined,
        new_password: formData.new_password || undefined
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Admin credentials updated successfully');
      
      // Update stored username if changed
      if (formData.new_username) {
        localStorage.setItem('username', formData.new_username);
      }

      // Reset form
      setFormData({
        current_password: '',
        new_username: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="settings-container">
      <h2 className="text-3xl font-bold text-slate-800 mb-8">Settings</h2>

      <div className="max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <KeyRound className="h-5 w-5 text-slate-600" />
              <CardTitle>Change Admin Credentials</CardTitle>
            </div>
            <CardDescription>
              Update your username and/or password. Enter your current password to confirm changes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">Current Password *</Label>
                <Input
                  id="current_password"
                  data-testid="current-password-input"
                  type="password"
                  value={formData.current_password}
                  onChange={(e) => setFormData(prev => ({ ...prev, current_password: e.target.value }))}
                  required
                  placeholder="Enter current password"
                />
              </div>

              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-3">New Credentials (Optional)</h3>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new_username">New Username</Label>
                    <Input
                      id="new_username"
                      data-testid="new-username-input"
                      type="text"
                      value={formData.new_username}
                      onChange={(e) => setFormData(prev => ({ ...prev, new_username: e.target.value }))}
                      placeholder="Leave blank to keep current username"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password</Label>
                    <Input
                      id="new_password"
                      data-testid="new-password-input"
                      type="password"
                      value={formData.new_password}
                      onChange={(e) => setFormData(prev => ({ ...prev, new_password: e.target.value }))}
                      placeholder="Leave blank to keep current password"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm New Password</Label>
                    <Input
                      id="confirm_password"
                      data-testid="confirm-password-input"
                      type="password"
                      value={formData.confirm_password}
                      onChange={(e) => setFormData(prev => ({ ...prev, confirm_password: e.target.value }))}
                      placeholder="Re-enter new password"
                      disabled={!formData.new_password}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button 
                  type="submit" 
                  disabled={loading}
                  data-testid="update-credentials-button"
                >
                  {loading ? 'Updating...' : 'Update Credentials'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
