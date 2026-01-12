import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";

interface User {
  user_name: string;
  email: string;
  role: string;
}

const Users = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  
  // Form state
  const [formData, setFormData] = useState({
    user_name: "",
    email: "",
    role: "",
    password: "",
    confirm_password: "",
  });

  useEffect(() => {
    // Check current user role and permissions
    const checkUserPermissions = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          navigate("/");
          return;
        }

        const response = await fetch(API_ENDPOINTS.CURRENT_USER, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCurrentUserRole(userData.role || "");
          
          // Check if user has permission to manage users
          if (!hasPermission(userData.role, "canManageUsers")) {
            toast({
              title: "Access Denied",
              description: "You don't have permission to access this page",
              variant: "destructive",
            });
            navigate("/dashboard");
            return;
          }
          
          // If user has permission, fetch users list
          fetchUsers();
        } else if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_name");
          navigate("/");
        }
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to verify permissions",
          variant: "destructive",
        });
        navigate("/dashboard");
      }
    };

    checkUserPermissions();
  }, [navigate, toast]);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.USERS, { headers });
      
      if (response.ok) {
        const data: User[] = await response.json();
        setUsers(data);
      } else {
        toast({
          title: "Error",
          description: "Failed to load users",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.user_name || !formData.email || !formData.role || !formData.password) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    if (formData.password !== formData.confirm_password) {
      toast({
        title: "Error",
        description: "Passwords do not match",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.USERS, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_name: formData.user_name,
          email: formData.email,
          role: formData.role.toLowerCase(),
          password: formData.password,
          confirm_password: formData.confirm_password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "User created successfully",
        });
        setShowCreateUser(false);
        setFormData({
          user_name: "",
          email: "",
          role: "",
          password: "",
          confirm_password: "",
        });
        fetchUsers(); // Refresh the list
      } else {
        toast({
          title: "Error",
          description: data.detail || "Failed to create user",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const capitalizeRole = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen bg-background w-[220px] ">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8">
          <h1 className="text-4xl font-bold mb-12 text-center">User's List</h1>
          {hasPermission(currentUserRole, "canCreateUser") && (
            <div className="mt-8 max-w-5xl mx-auto mb-4">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setShowCreateUser(true)}
              >
                + Add User
              </Button>
            </div>
          )}
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">Loading users...</p>
            </div>
          ) : (
            <div className="max-w-5xl mx-auto bg-white rounded-lg shadow overflow-hidden">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 z-10 bg-white text-left p-6 font-semibold text-lg">User Name</th>
                    <th className="sticky top-0 z-10 bg-white text-left p-6 font-semibold text-lg">Email Address</th>
                    <th className="sticky top-0 z-10 bg-white text-left p-6 font-semibold text-lg">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="p-6 text-center text-muted-foreground">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    users.map((user, index) => (
                      <tr
                        key={index}
                        className="border-b hover:bg-muted/50 cursor-pointer"
                        onClick={() => navigate(`/user-history/${encodeURIComponent(user.user_name)}`)}
                      >
                        <td className="p-6">{user.user_name}</td>
                        <td className="p-6">{user.email}</td>
                        <td className="p-6">{capitalizeRole(user.role)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
          

          {/* {hasPermission(currentUserRole, "canCreateUser") && (
            <div className="mt-8 max-w-5xl mx-auto">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setShowCreateUser(true)}
              >
                + Add User
              </Button>
            </div>
          )} */}
        </div>
      </main>

      <Dialog 
        open={showCreateUser} 
        onOpenChange={(open) => {
          setShowCreateUser(open);
          if (!open) {
            // Reset form when dialog is closed
            setFormData({
              user_name: "",
              email: "",
              role: "",
              password: "",
              confirm_password: "",
            });
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-3xl font-bold text-center">Create User</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-6 pt-8">
            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="username" className="text-right font-semibold">
                User Name :
              </Label>
              <Input
                id="username"
                className="bg-muted"
                value={formData.user_name}
                onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="email" className="text-right font-semibold">
                Email Address :
              </Label>
              <Input
                id="email"
                type="email"
                className="bg-muted"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="role" className="text-right font-semibold">
                User Role :
              </Label>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData({ ...formData, role: value })}
                required
              >
                <SelectTrigger className="bg-muted">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="curator">Curator</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="password" className="text-right font-semibold">
                Password :
              </Label>
              <Input
                id="password"
                type="password"
                className="bg-muted"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="confirm-password" className="text-right font-semibold">
                Confirm Password :
              </Label>
              <Input
                id="confirm-password"
                type="password"
                className="bg-muted"
                value={formData.confirm_password}
                onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                required
              />
            </div>

            <div className="flex justify-center pt-6">
              <Button
                type="submit"
                className="bg-primary hover:bg-primary/90 px-12"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Creating..." : "Submit"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Users;
