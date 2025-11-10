import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from "@/components/Sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { MoreVertical } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";

const MENU_OPTIONS = [
  { label: "Open", action: "open" },
  // { label: "Add test case", action: "addTestCase" },
  // { label: "Export", action: "export" },
  { label: "History", action: "history" },
  // { label: "Delete", action: "delete", className: "text-red-600" }
];

const statCardHandlers = (navigate, stat) => ({
  open: () => stat.onClick && stat.onClick(),
  // addTestCase: () => alert(`Add test case for ${stat.title}`),
  // export: () => alert(`Export ${stat.title}`),
  history: () => alert(`Show history for ${stat.title}`),
  // delete: () => alert(`Delete ${stat.title}`),
});

interface DashboardStats {
  test_cases: number;
  targets: number;
  domains: number;
  strategies: number;
  languages: number;
  responses: number;
  prompts: number;
  llm_prompts: number;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [menuOpen, setMenuOpen] = useState(null);
  const [stats, setStats] = useState([
    { title: "Test cases", count: 0, onClick: () => navigate("/test-cases") },
    { title: "Targets", count: 0, onClick: () => navigate("/targets") },
    { title: "Domains", count: 0, onClick: () => navigate("/domains") },
    { title: "Strategies", count: 0, onClick: () => navigate("/strategies") },
    { title: "Languages", count: 0, onClick: () => navigate("/languages") },
    { title: "Responses", count: 0, onClick: () => navigate("/responses") },
    { title: "Prompts", count: 0, onClick: () => navigate("/prompts") },
    { title: "LLM Prompts", count: 0, onClick: () => navigate("/llm-prompts") },
  ]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        // Add auth token if available (even though middleware is disabled, it's good practice)
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.DASHBOARD, { headers });
        const data: DashboardStats = await response.json();

        if (response.ok) {
          setStats([
            { title: "Test cases", count: data.test_cases, onClick: () => navigate("/test-cases") },
            { title: "Targets", count: data.targets, onClick: () => navigate("/targets") },
            { title: "Domains", count: data.domains, onClick: () => navigate("/domains") },
            { title: "Strategies", count: data.strategies, onClick: () => navigate("/strategies") },
            { title: "Languages", count: data.languages, onClick: () => navigate("/languages") },
            { title: "Responses", count: data.responses, onClick: () => navigate("/responses") },
            { title: "Prompts", count: data.prompts, onClick: () => navigate("/prompts") },
            { title: "LLM Prompts", count: data.llm_prompts, onClick: () => navigate("/llm-prompts") },
          ]);
        } else {
          toast({
            title: "Error",
            description: "Failed to load dashboard data",
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

    fetchDashboardData();
  }, [navigate, toast]);

  return (
    <>
      <div className="flex min-h-screen">
          {/* Sidebar: fixed width and position */}
          <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
            <Sidebar />
          </aside>
        <main className="flex-1 p-28 ml-[220px] min-h-screen items-center justify-center">
          <div className="grid grid-cols-3 gap-14 max-w-7xl mx-auto">
            {stats.map((stat, idx) => (
              <Card
                key={stat.title}
                className={`relative shadow-lg hover:shadow-xl transition-shadow ${stat.onClick ? "cursor-pointer" : ""}`}
                onClick={() => stat.onClick && stat.onClick()}
              >
                <button
                  className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent triggering card click
                    setMenuOpen(menuOpen === idx ? null : idx); // Toggle menu for this card
                  }}
                >
                  <MoreVertical className="w-5 h-5" />
                </button>
                {menuOpen === idx && (
                  <div className="absolute top-12 right-4 z-10 bg-white border rounded shadow-lg flex flex-col min-w-[150px]">
                    {MENU_OPTIONS.map(opt => (
                      <button
                        key={opt.label}
                        className={`px-4 py-2 text-left hover:bg-gray-100 ${opt.className || ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          statCardHandlers(navigate, stat)[opt.action]();
                          setMenuOpen(null);
                        }}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                <CardContent className="pt-8 pb-8 text-center">
                  <h3 className="text-xl font-semibold mb-4">{stat.title}</h3>
                  <p className="text-5xl font-bold">
                    {isLoading ? "..." : stat.count.toString().padStart(3, '0')}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    </>
  );
};

export default Dashboard;
