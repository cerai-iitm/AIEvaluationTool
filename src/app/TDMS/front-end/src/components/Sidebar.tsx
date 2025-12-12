import { Home, Users, LogOut } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import ceraiLogo from "@/assets/cerai-logo.png";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";

interface UserInfo {
  user_name: string;
  email: string;
  role: string;
}

interface NavItem {
  icon: typeof Home;
  label: string;
  path: string;
  requiredPermission?: keyof import("@/utils/permissions").RolePermissions;
}

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [userInfo, setUserInfo] = useState<UserInfo>({ user_name: "UserName", email: "", role: "Admin" });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUserInfo = async () => {
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
          const data: UserInfo = await response.json();
          setUserInfo(data);
        } else if (response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_name");
          navigate("/");
          toast({
            title: "Session Expired",
            description: "Please login again",
            variant: "destructive",
          });
        } else {
          // Use fallback values from localStorage if API fails
          const storedUsername = localStorage.getItem("user_name");
          if (storedUsername) {
            setUserInfo({ user_name: storedUsername, email: "", role: "User" });
          }
        }
      } catch (error) {
        // Use fallback values from localStorage if API fails
        const storedUsername = localStorage.getItem("user_name");
        if (storedUsername) {
          setUserInfo({ user_name: storedUsername, email: "", role: "User" });
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserInfo();
  }, [navigate, toast]);

  const navItems: NavItem[] = [
    { icon: Home, label: "Home", path: "/dashboard" },
    { 
      icon: Users, 
      label: "User's List", 
      path: "/users",
      requiredPermission: "canManageUsers" // Only visible to Admin role
    },
  ];

  return (
    <aside className="w-56 bg-primary min-h-screen flex flex-col text-primary-foreground">
      <div className="p-6 flex items-center gap-3">
        <div className="w-40 h-15 rounded-full bg-white/100 flex items-center justify-center ">
          <img src={ceraiLogo} alt="CeRAI" className="w-40 h-15 object-contain p-5" />
        </div>
        {/* <h1 className="text-xl font-bold tracking-wider">CeRAI</h1> */}
      </div>

      <nav className="flex-1 px-3 mt-8">
        {navItems
          .filter((item) => {
            // If no permission required, show to all users
            if (!item.requiredPermission) {
              return true;
            }
            // Check if user has the required permission
            return hasPermission(userInfo.role, item.requiredPermission);
          })
          .map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                  isActive
                    ? "bg-white text-primary font-medium"
                    : "text-primary-foreground/80 hover:bg-white/10"
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-3 mb-2">
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium">{isLoading ? "Loading..." : userInfo.user_name}</div>
            <div className="text-xs text-primary-foreground/60">
              {isLoading ? "" : userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1)}
            </div>
          </div>
        </div>
        <Link
          to="/"
          onClick={() => {
            localStorage.removeItem("access_token");
            localStorage.removeItem("user_name");
          }}
          className="flex items-center gap-3 px-4 py-3 text-primary-foreground/80 hover:bg-white/10 rounded-lg transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>Log out</span>
        </Link>
      </div>
    </aside>
  );
};

export default Sidebar;
