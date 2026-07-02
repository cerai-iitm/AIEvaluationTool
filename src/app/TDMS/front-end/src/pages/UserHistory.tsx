import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
import { Eye, EyeOff, Loader2 } from "lucide-react";

interface Activity {
  description: string;
  type: string;
  testCaseId: string;
  status: "Created" | "Updated" | "Deleted";
  timestamp: string;
}

interface User {
  user_id: string;
  user_name: string;
  email: string;
  role: string;
}

const normalizeRole = (role: string) => role.trim().toLowerCase();

const formatLocalTimestamp = (timestamp: string) => {
  const trimmedTimestamp = timestamp.trim();
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(trimmedTimestamp);
  const normalizedTimestamp = trimmedTimestamp.replace(" ", "T");
  const date = new Date(hasTimezone ? normalizedTimestamp : `${normalizedTimestamp}Z`);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  const parts = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const getPart = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? "";

  return `${getPart("year")}-${getPart("month")}-${getPart("day")} ${getPart("hour")}:${getPart("minute")}`;
};




const UserHistory = () => {
  const { username } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  
  // Dialog states
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [resetPassword, setResetPassword] = useState(false);
  // Update form state
  const [updateForm, setUpdateForm] = useState({
    user_name: "",
    email: "",
    role: "",
    password: "",
  });

  function getBasePath(): string {
    return window.location.pathname.startsWith("/tdms") ? "/tdms" : "";
  }
  const validateUserName = (value: string): string | null => {
  const v = value.trim();
    if (v.length < 3) return "Username must be at least 3 characters long";
    if (v.length > 30) return "Username must be 30 characters or fewer";
    
    if (!/^[a-zA-Z0-9._-]+$/.test(v)) return "Special characters are not allowed";
    if (!/^[a-zA-Z0-9]/.test(v)) return "Username must start with a letter or number";
    if (!/[a-zA-Z0-9]$/.test(v)) return "Username must end with a letter or number";
    if (/[._-]{2,}/.test(v)) return "No consecutive special characters (e.g. .. __ --)";
    return null;
  };

  // Fetch current logged-in user data
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.CURRENT_USER, { headers });
        
        if (response.ok) {
          const userData: User = await response.json();
          setCurrentUser(userData);
        }
      } catch (error) {
        console.error("Error fetching current user data:", error);
      }
    };

    fetchCurrentUser();
  }, []);

  // Fetch user data
  useEffect(() => {
    const fetchUserData = async () => {
      if (!username) return;

      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        // Fetch all users to find the one matching the username
        const response = await fetch(API_ENDPOINTS.USERS, { headers });
        
        if (response.ok) {
          const users: User[] = await response.json();
          const decodedUsername = decodeURIComponent(username);
          const foundUser = users.find(u => u.user_name === decodedUsername);
          
          if (foundUser) {
            setUser(foundUser);
            setUpdateForm({
              user_name: foundUser.user_name,
              email: foundUser.email,
              role: normalizeRole(foundUser.role),
              password: "",
            });
          } else {
            toast({
              title: "Error",
              description: "User not found",
              variant: "destructive",
            });
          }
        }
      } catch (error) {
        console.error("Error fetching user data:", error);
        toast({
          title: "Error",
          description: "Failed to fetch user data",
          variant: "destructive",
        });
      } finally {
        setIsLoadingUser(false);
      }
    };

    fetchUserData();
  }, [username, toast]);

  // Fetch user activity
  useEffect(() => {
    const fetchUserActivity = async () => {
      if (!username) return;

      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        // Decode username from URL and encode for API call
        const decodedUsername = decodeURIComponent(username);
        const response = await fetch(API_ENDPOINTS.USER_ACTIVITY(encodeURIComponent(decodedUsername)), { headers });
        
        if (response.ok) {
          const data: Activity[] = await response.json();
          setActivities(data);
        } else {
          toast({
            title: "Error",
            description: "Failed to load user activity",
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

    fetchUserActivity();
  }, [username, toast]);

  const handleUpdate = async () => {
    if (!user || !user.user_id) {
      toast({
        title: "Error",
        description: "User information not available",
        variant: "destructive",
      });
      return;
    }

    // Validation
    if (!updateForm.user_name || !updateForm.email || !updateForm.role) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    const userNameError = validateUserName(updateForm.user_name);
      if (userNameError) {
        toast({ title: "Invalid Username", description: userNameError, variant: "destructive" });
        return;
      }
      
    setIsUpdating(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const payload: any = {
        user_name: updateForm.user_name,
        email: updateForm.email,
        role: updateForm.role.toLowerCase(),
      };

      // Only include password if it's provided
      if (updateForm.password.trim()) {
        payload.password = updateForm.password;
      }

      const response = await fetch(API_ENDPOINTS.USER_UPDATE(user.user_id), {
        method: "PUT",
        headers,
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: "User updated successfully",
        });
        setUpdateDialogOpen(false);
        // Refresh user data and activities
        if (updateForm.user_name !== user.user_name) {
          window.location.href = `${getBasePath()}/user-history/${updateForm.user_name}`;
        } else {
          window.location.reload();
        }

      } else {
        const errorData = await response.json().catch(() => ({}));
        toast({
          title: "Error",
          description: errorData.detail || "Failed to update user",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error updating user:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUpdateDialogOpenChange = (open: boolean) => {
    if (open && user) {
      setUpdateForm({
        user_name: user.user_name,
        email: user.email,
        role: normalizeRole(user.role),
        password: "",
      });
      setShowPassword(false);
    }

    setUpdateDialogOpen(open);
  };

  const handleDelete = async () => {
    if (!user || !user.user_id) {
      toast({
        title: "Error",
        description: "User information not available",
        variant: "destructive",
      });
      return;
    }

    // Prevent admin from deleting their own account
    if (
      currentUser?.role?.toLowerCase() === "admin" &&
      currentUser?.user_name === user?.user_name
    ) {
      toast({
        title: "Error",
        description: "Admin users cannot delete their own account",
        variant: "destructive",
      });
      setDeleteDialogOpen(false);
      return;
    }

    setIsDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // First delete user activity
      try {
        const activityResponse = await fetch(API_ENDPOINTS.USER_ACTIVITY_DELETE(user.user_id), {
          method: "DELETE",
          headers,
        });
        
        if (!activityResponse.ok) {
          console.warn("Failed to delete user activity, continuing with user deletion");
        }
      } catch (error) {
        console.warn("Error deleting user activity:", error);
      }

      // Then delete the user
      const response = await fetch(API_ENDPOINTS.USER_DELETE(user.user_id), {
        method: "DELETE",
        headers,
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: "User and their activity history deleted successfully",
        });
        setDeleteDialogOpen(false);
        // Navigate back to users list
        navigate("/users");
      } else {
        const errorData = await response.json().catch(() => ({}));
        toast({
          title: "Error",
          description: errorData.detail || "Failed to delete user",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error deleting user:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusColor = (status: Activity["status"]) => {
    switch (status) {
      case "Created":
        return "text-blue-600";
      case "Updated":
        return "text-accent";
      case "Deleted":
        return "text-destructive";
      default:
        return "text-foreground";
    }
  };

  return (
    <div className="flex min-h-screen">

      <main className="flex-1 p-28 min-h-screen items-center justify-center ">
        <div className="sticky top-0 bg-white rounded-lg px-4 py-4 shadow-md max-w-5xl z-10 mb-12">
          <div className="flex items-center justify-between">
            <h1 className="text-4xl font-bold">
              Activity of {username ? decodeURIComponent(username) : "User"}
            </h1>

            {/* if current user is admin and the user is the same as the current user, hide the update and delete buttons */}
            <div className="flex gap-2">
              {currentUser?.role?.toLowerCase() !== "admin" || currentUser?.user_name !== user?.user_name && (
                <>
                  <Button
                    className="bg-primary hover:bg-primary/90"
                    onClick={() => handleUpdateDialogOpenChange(true)}
                    disabled={isLoadingUser || !user}
                  >
                    Update
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => setDeleteDialogOpen(true)}
                    disabled={isLoadingUser || !user}
                  >
                    Delete
                  </Button>
                </>
              )}
              {/* <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setUpdateDialogOpen(true)}
                disabled={isLoadingUser || !user ||
                  (currentUser?.role?.toLowerCase() === "admin" && 
                   currentUser?.user_name === user?.user_name)
                }
                title={
                  currentUser?.role?.toLowerCase() === "admin" && 
                  currentUser?.user_name === user?.user_name
                    ? "Admin users cannot update their own account"
                    : ""
                }
              >
                Update
              </Button>
              <Button
                variant="destructive"
                onClick={() => setDeleteDialogOpen(true)}
                disabled={
                  isLoadingUser || 
                  !user || 
                  (currentUser?.role?.toLowerCase() === "admin" && 
                   currentUser?.user_name === user?.user_name)
                }
                title={
                  currentUser?.role?.toLowerCase() === "admin" && 
                  currentUser?.user_name === user?.user_name
                    ? "Admin users cannot delete their own account"
                    : ""
                }
              >
                Delete
              </Button> */}
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-lg text-muted-foreground">Loading activities...</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-lg text-muted-foreground">No activities found for this user.</p>
          </div>
        ) : (
          <div className="space-y-4 max-w-5xl">
            {activities.map((activity, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-lg mb-2">{activity.description}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2 justify-end mb-1">
                    {activity.type !== "User" && (
                      <>
                        <span className="font-medium">{activity.testCaseId}</span>
                        <span className="text-xl">-</span>
                      </>
                    )}
                    <span className={`font-semibold ${getStatusColor(activity.status)}`}>
                      {activity.status}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {formatLocalTimestamp(activity.timestamp)}
                  </p>
                </div>
              </div>
            </div>
            ))}
          </div>
        )}
      </main>

      {/* Update User Dialog */}
      <Dialog open={updateDialogOpen} onOpenChange={handleUpdateDialogOpenChange}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-3xl font-bold text-center">Update User</DialogTitle>
          </DialogHeader>

          <div className="space-y-6 pt-8">
            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="update-username" className="text-right font-semibold">
                User Name :
              </Label>
              <Input
                id="update-username"
                className="bg-muted"
                value={updateForm.user_name}
                onChange={(e) => setUpdateForm({ ...updateForm, user_name: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="update-email" className="text-right font-semibold">
                Email Address :
              </Label>
              <Input
                id="update-email"
                type="email"
                className="bg-muted"
                value={updateForm.email}
                onChange={(e) => setUpdateForm({ ...updateForm, email: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="update-role" className="text-right font-semibold">
                User Role :
              </Label>
              <Select
                value={updateForm.role}
                onValueChange={(value) => setUpdateForm({ ...updateForm, role: value })}
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
            {resetPassword && (
              <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="update-password" className="text-right font-semibold">
                Password :
              </Label>
              <div className="relative">
                <Input
                  id="update-password"
                  type={showPassword ? "text" : "password"}
                  className="bg-muted pr-10"
                  value={updateForm.password}
                  onChange={(e) => setUpdateForm({ ...updateForm, password: e.target.value })}
                  placeholder="Leave empty to keep current password"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
            )}
            
                    
            <div className="flex justify-center gap-4 pt-6">
              <Button
                variant="outline"
                onClick={() => setUpdateDialogOpen(false)}
                disabled={isUpdating}
              >
                Cancel
              </Button>
               <Button
                variant="outline"
                className="border-yellow-500 text-yellow-600 "
                type="button"
                onClick={() => setResetPassword(!resetPassword)}
                disabled={isUpdating}
              >
                {resetPassword ? "Cancel Reset" : "Reset Password"}
              </Button>
              <Button
                className="bg-primary hover:bg-primary/90 px-6"
                onClick={handleUpdate}
                disabled={isUpdating}
              >
                {isUpdating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating
                  </>
                ) : (
                  <>save</>
                  
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this user and their entire activity history?
              This action cannot be undone.
              {user && (
                <div className="mt-4 p-4 bg-muted rounded-md">
                  <p className="font-semibold">User Name: {user.user_name}</p>
                  <p className="font-semibold">Email: {user.email}</p>
                  <p className="font-semibold">Role: {user.role}</p>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default UserHistory;
