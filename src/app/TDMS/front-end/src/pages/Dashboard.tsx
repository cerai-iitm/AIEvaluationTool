import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from "@/components/Sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { MoreVertical, FileText, Target, Globe, Layers, Languages, MessageSquare, PenTool, Scale, ClipboardList, BarChart3, Users } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { canViewHistory, canViewActivity } from "@/utils/permissions";

// Menu options will be filtered based on user role
const MENU_OPTIONS = [
  { label: "Open", action: "open", className: "" },
  { label: "History", action: "history", className: "" },
] as const;

// Map table titles to entity types for API calls
const TABLE_TO_ENTITY_TYPE: Record<string, string> = {
  "Test cases": "Test Case",
  "Targets": "Target",
  "Domains": "Domain",
  "Strategies": "Strategy",
  "Languages": "Language",
  "Responses": "Response",
  "Prompts": "Prompt",
  "LLM Prompts": "LLM Prompt",
  "Test Plans": "Test Plan",
  "Metrics": "Metric",
};

interface Activity {
  description: string;
  type: string;
  testCaseId: string;
  status: "Created" | "Updated" | "Deleted";
  timestamp: string;
  user_name: string;
  role: string;
}

interface DashboardStats {
  test_cases: number;
  targets: number;
  domains: number;
  strategies: number;
  languages: number;
  responses: number;
  prompts: number;
  llm_prompts: number;
  test_plans: number;
  metrics: number;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [menuOpen, setMenuOpen] = useState<number | null>(null);
  const [stats, setStats] = useState([
    { title: "Test cases", count: 0, icon: FileText, onClick: () => navigate("/test-cases") },
    { title: "Targets", count: 0, icon: Target, onClick: () => navigate("/targets") },
    { title: "Domains", count: 0, icon: Globe, onClick: () => navigate("/domains") },
    { title: "Strategies", count: 0, icon: Layers, onClick: () => navigate("/strategies") },
    { title: "Languages", count: 0, icon: Languages, onClick: () => navigate("/languages") },
    { title: "Responses", count: 0, icon: MessageSquare, onClick: () => navigate("/responses") },
    { title: "Prompts", count: 0, icon: PenTool, onClick: () => navigate("/prompts") },
    { title: "LLM Prompts", count: 0, icon: Scale, onClick: () => navigate("/llm-prompts") },
    { title: "Test Plans", count: 0, icon: ClipboardList, onClick: () => navigate("/test-plans") },
    { title: "Metrics", count: 0, icon: BarChart3, onClick: () => navigate("/metrics") },
  ]);
  const [isLoading, setIsLoading] = useState(true);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyTitle, setHistoryTitle] = useState("");
  const [historyActivities, setHistoryActivities] = useState<Activity[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const response = await fetch(API_ENDPOINTS.CURRENT_USER, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCurrentUserRole(userData.role || "");
        }
      } catch (error) {
        console.error("Error fetching user role:", error);
      }
    };

    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.DASHBOARD, { headers });
        const data: DashboardStats = await response.json();

        if (response.ok) {
          setStats([
            { title: "Test cases", count: data.test_cases, icon: FileText, onClick: () => navigate("/test-cases") },
            { title: "Targets", count: data.targets, icon: Target, onClick: () => navigate("/targets") },
            { title: "Domains", count: data.domains, icon: Globe, onClick: () => navigate("/domains") },
            { title: "Strategies", count: data.strategies, icon: Layers, onClick: () => navigate("/strategies") },
            { title: "Languages", count: data.languages, icon: Languages, onClick: () => navigate("/languages") },
            { title: "Responses", count: data.responses, icon: MessageSquare, onClick: () => navigate("/responses") },
            { title: "Prompts", count: data.prompts, icon: PenTool, onClick: () => navigate("/prompts") },
            { title: "LLM Prompts", count: data.llm_prompts, icon: Scale, onClick: () => navigate("/llm-prompts") },
            { title: "Test Plans", count: data.test_plans, icon: ClipboardList, onClick: () => navigate("/test-plans") },
            { title: "Metrics", count: data.metrics, icon: BarChart3, onClick: () => navigate("/metrics") },
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

    fetchUserRole();
    fetchDashboardData();
  }, [navigate, toast]);

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

  const fetchHistory = async (tableTitle: string) => {
    const entityType = TABLE_TO_ENTITY_TYPE[tableTitle];
    if (!entityType) {
      toast({
        title: "Error",
        description: `No entity type found for "${tableTitle}"`,
        variant: "destructive",
      });
      return;
    }

    setHistoryLoading(true);
    setHistoryTitle(tableTitle);
    setHistoryDialogOpen(true);

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        toast({
          title: "Error",
          description: "Authentication required",
          variant: "destructive",
        });
        setHistoryActivities([]);
        setHistoryLoading(false);
        return;
      }

      const headers: HeadersInit = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      };

      let userRole = currentUserRole;
      if (!userRole) {
        try {
          const userResponse = await fetch(API_ENDPOINTS.CURRENT_USER, { headers });
          if (userResponse.ok) {
            const userData = await userResponse.json();
            userRole = userData.role || "";
            setCurrentUserRole(userRole);
          }
        } catch (error) {
          console.error("Error fetching user role:", error);
        }
      }

      const encodedEntityType = encodeURIComponent(entityType);
      const response = await fetch(API_ENDPOINTS.ENTITY_ACTIVITY(encodedEntityType), { headers });
      
      if (response.ok) {
        const data: Activity[] = await response.json();
        if (userRole) {
          const filteredData = data.filter(activity => 
            canViewActivity(userRole, activity.role || "")
          );
          setHistoryActivities(filteredData);
        } else {
          setHistoryActivities(data);
        }
      } else {
        toast({
          title: "Error",
          description: "Failed to load history",
          variant: "destructive",
        });
        setHistoryActivities([]);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
      setHistoryActivities([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const statCardHandlers = (stat: typeof stats[0]) => ({
    open: () => stat.onClick && stat.onClick(),
    history: () => fetchHistory(stat.title),
  });

  return (
    <>
      <div className="flex min-h-screen">
        <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
          <Sidebar />
        </aside>
        <main className="flex-1 ml-[220px] min-h-screen flex flex-col pt-28 pb-28">
          {/* Centered Title */}
          <div className="flex items-center justify-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-black">
              Test Data Management System
            </h1>
          </div>
          
          {/* Cards Grid - Centered */}
          <div className="flex-1 flex items-center justify-center w-full">
            <div className="w-full max-w-7xl px-10">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {stats.map((stat, idx) => (
                  <Card
                    key={stat.title}
                    className={`relative shadow-lg hover:shadow-xl transition-shadow hovershadow-md ${stat.onClick ? "cursor-pointer" : ""}`}
                    onClick={() => stat.onClick && stat.onClick()}
                  >
                    <button
                      className="absolute top-4 right-4 text-muted-foreground hover:text-foreground z-10"
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpen(menuOpen === idx ? null : idx);
                      }}
                    >
                      <MoreVertical className="w-5 h-5" />
                    </button>
                    {menuOpen === idx && (
                      <div className="absolute top-12 right-4 z-20 bg-white border rounded-lg shadow-lg flex flex-col min-w-[150px]">
                        {MENU_OPTIONS.filter(opt => {
                          if (opt.action === "history" && !canViewHistory(currentUserRole)) {
                            return false;
                          }
                          return true;
                        }).map(opt => (
                          <button
                            key={opt.label}
                            className={`px-4 py-2 text-left hover:bg-gray-100 ${(opt as any).className || ''}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              statCardHandlers(stat)[opt.action as keyof ReturnType<typeof statCardHandlers>]();
                              setMenuOpen(null);
                            }}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    )}

                    <CardContent className="flex flex-col items-center justify-center p-8 text-center">
                      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <stat.icon className="w-8 h-8 text-primary" />
                      </div>
                      <p className="text-base text-muted-foreground mb-2 px-2">{stat.title}</p>
                      <p className="text-4xl font-bold">
                        {isLoading ? "..." : stat.count.toString().padStart(3, '0')}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>

      <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader className='mt-4 sticky top-0 mb-2 bg-white rounded-lg px-4 py-4 shadow-md'>
            <DialogTitle>History - {historyTitle}</DialogTitle>
          </DialogHeader>
          
          {historyLoading ? (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">Loading history...</p>
            </div>
          ) : historyActivities.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">No history found for {historyTitle}.</p>
            </div>
          ) : (
            <div className="space-y-4 mt-4">
              {historyActivities.map((activity, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">{activity.user_name}</p>
                        </div>
                      </div>
                      <p className="text-lg mb-2">{activity.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2 justify-end mb-1">
                        <span className="font-medium">{activity.testCaseId}</span>
                        <span className="text-xl">-</span>
                        <span className={`font-semibold ${getStatusColor(activity.status)}`}>
                          {activity.status}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">{activity.timestamp}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Dashboard;