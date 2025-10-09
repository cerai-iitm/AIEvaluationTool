import { Home, Users, LogOut } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import ceraiLogo from "@/assets/cerai-logo.png";

interface SidebarProps {
  username?: string;
  role?: string;
}

const Sidebar = ({ username = "UserName", role = "Admin" }: SidebarProps) => {
  const location = useLocation();

  const navItems = [
    { icon: Home, label: "Home", path: "/dashboard" },
    { icon: Users, label: "User's List", path: "/users" },
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
        {navItems.map((item) => {
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
            <div className="text-sm font-medium">{username}</div>
            <div className="text-xs text-primary-foreground/60">{role}</div>
          </div>
        </div>
        <Link
          to="/"
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
