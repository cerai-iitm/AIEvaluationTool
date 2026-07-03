import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { MoreVertical, FileText, Target, Globe, Layers, Languages, MessageSquare, PenTool, Scale, ClipboardList, BarChart3, Users, Upload, Loader } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { canViewHistory, canViewActivity } from "@/utils/permissions";
import { getValidAccessToken } from "@/utils/auth";

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

interface ImporterWsEvent {
  event: "idle" | "accepted" | "running" | "log" | "success" | "error";
  status: "idle" | "running" | "success" | "error";
  message: string;
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
  const [importerDialogOpen, setImporterDialogOpen] = useState(false);
  const [importerLoading, setImporterLoading] = useState(false);
  const [importerStatus, setImporterStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [importerMessage, setImporterMessage] = useState("");
  const [importerLogs, setImporterLogs] = useState<string[]>([]);
  const importerSocketRef = useRef<WebSocket | null>(null);
  const importerSocketClosingRef = useRef(false);
  const importerLoadingRef = useRef(false);
  const importerReloadTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = await getValidAccessToken(API_ENDPOINTS.REFRESH);
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
        }
      } catch (error) {
        console.error("Error fetching user role:", error);
      }
    };

    const fetchDashboardData = async () => {
      try {
        const token = await getValidAccessToken(API_ENDPOINTS.REFRESH);
        if (!token) {
          navigate("/");
          return;
        }

        const response = await fetch(API_ENDPOINTS.DASHBOARD, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
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
          if (response.status === 401) {
            navigate("/");
            return;
          }

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

  useEffect(() => {
    importerLoadingRef.current = importerLoading;
  }, [importerLoading]);

  useEffect(() => {
    return () => {
      importerSocketClosingRef.current = true;
      importerSocketRef.current?.close();
      if (importerReloadTimerRef.current !== null) {
        window.clearTimeout(importerReloadTimerRef.current);
      }
    };
  }, []);

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

  const closeImporterSocket = () => {
    importerSocketClosingRef.current = true;
    importerSocketRef.current?.close();
    importerSocketRef.current = null;
  };

  const connectImporterSocket = (token: string) =>
    new Promise<void>((resolve, reject) => {
      importerSocketClosingRef.current = false;
      const socket = new WebSocket(
        `${API_ENDPOINTS.IMPORTER_STATUS_WS}?token=${encodeURIComponent(token)}`
      );

      socket.onopen = () => {
        importerSocketRef.current = socket;
        resolve();
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as ImporterWsEvent;

        if (payload.event === "idle") {
          return;
        }

        setImporterDialogOpen(true);
        setImporterMessage(payload.message);

        if (payload.event === "log") {
          setImporterLogs((current) => [...current.slice(-7), payload.message]);
          return;
        }

        if (payload.status === "running") {
          setImporterLoading(true);
          setImporterStatus("loading");
          return;
        }

        if (payload.status === "success") {
          setImporterLoading(false);
          setImporterStatus("success");
          closeImporterSocket();
          importerReloadTimerRef.current = window.setTimeout(() => {
            window.location.reload();
          }, 2000);
          return;
        }

        if (payload.status === "error") {
          setImporterLoading(false);
          setImporterStatus("error");
          closeImporterSocket();
        }
      };

      socket.onerror = () => {
        reject(new Error("Unable to connect to importer status websocket"));
      };

      socket.onclose = () => {
        importerSocketRef.current = null;
        if (!importerSocketClosingRef.current && importerLoadingRef.current) {
          setImporterLoading(false);
          setImporterStatus("error");
          setImporterMessage("Importer status connection was closed unexpectedly.");
        }
      };
    });

  const runImporter = async () => {
    setImporterLoading(true);
    setImporterStatus("loading");
    setImporterMessage("Running importer... This may take a few minutes.");
    setImporterLogs([]);
    setImporterDialogOpen(true);

    try {
      const token = await getValidAccessToken(API_ENDPOINTS.REFRESH);
      if (!token) {
        setImporterStatus("error");
        setImporterMessage("Authentication failed");
        setImporterLoading(false);
        return;
      }

      await connectImporterSocket(token);

      const response = await fetch(API_ENDPOINTS.IMPORTER_RUN, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok && data.status !== "running") {
        closeImporterSocket();
        setImporterStatus("error");
        setImporterMessage(data.message || "Failed to import data. Please check the server logs.");
        setImporterLoading(false);
        return;
      }

      setImporterStatus("loading");
      setImporterLoading(true);
      setImporterMessage(data.message || "Importer started. Waiting for live updates...");
    } catch (error) {
      closeImporterSocket();
      setImporterStatus("error");
      setImporterMessage(`Error: ${error instanceof Error ? error.message : "An unexpected error occurred"}`);
      setImporterLoading(false);
    }
  };

  const statCardHandlers = (stat: typeof stats[0]) => ({
    open: () => stat.onClick && stat.onClick(),
    history: () => fetchHistory(stat.title),
  });

  return (
    <>
      <div className="flex min-h-screen">
        <main className="flex-1 min-h-screen flex flex-col pt-28 pb-28">
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
                    {/* <button
                      className="absolute top-4 right-4 text-muted-foreground hover:text-foreground z-10"
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpen(menuOpen === idx ? null : idx);
                      }}
                    >
                      <MoreVertical className="w-5 h-5" />
                    </button> */}
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

        {/* Importer Button - Fixed in Bottom Right */}
        <button
          onClick={() => {
            setImporterStatus("idle");
            setImporterMessage("");
            setImporterLogs([]);
            setImporterDialogOpen(true);
          }}
          disabled={importerLoading}
          className="fixed bottom-8 right-8 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2 z-30"
        >
          {importerLoading ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Importing...</span>
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              <span>Import Data</span>
            </>
          )}
        </button>
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

      {/* Importer Dialog */}
      <Dialog open={importerDialogOpen} onOpenChange={setImporterDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {importerStatus === "loading" && "Importing Data..."}
              {importerStatus === "success" && "Import Successful"}
              {importerStatus === "error" && "Import Failed"}
              {importerStatus === "idle" && "Confirm Import"}
            </DialogTitle>
          </DialogHeader>

          <div className="py-6 text-center">
            {importerStatus === "loading" && (
              <div className="flex flex-col items-center gap-4">
                <Loader className="w-12 h-12 text-blue-600 animate-spin" />
                <p className="text-foreground font-medium">The data is being imported. it will take a few seconds</p>
                {/* <p className="text-muted-foreground">{importerMessage}</p> */}
                {/* {importerLogs.length > 0 && (
                  <div className="w-full max-h-48 overflow-y-auto rounded-md bg-slate-950 p-3 text-left">
                    {importerLogs.map((log, index) => (
                      <p key={`${log}-${index}`} className="font-mono text-xs text-slate-100">
                        {log}
                      </p>
                    ))}
                  </div>
                )} */}
              </div>
            )}

            {importerStatus === "success" && (
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <span className="text-green-600 text-2xl">✓</span>
                </div>
                <p className="text-foreground font-medium">{importerMessage}</p>
                <p className="text-sm text-muted-foreground">The page will refresh automatically.</p>
              </div>
            )}

            {importerStatus === "error" && (
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <span className="text-red-600 text-2xl">✕</span>
                </div>
                <p className="text-foreground font-medium">{importerMessage}</p>
              </div>
            )}

            {importerStatus === "idle" && (
              <div className="flex flex-col items-center gap-4">
                <Upload className="w-12 h-12 text-blue-600" />
                <p className="text-foreground">
                  This will import all test data into the database. Continue?
                </p>
              </div>
            )}
          </div>

          {importerStatus === "idle" && (
            <div className="flex gap-4 justify-end pt-4">
              <button
                onClick={() => setImporterDialogOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={runImporter}
                disabled={importerLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400"
              >
                Import
              </button>
            </div>
          )}

          {(importerStatus === "error" || importerStatus === "success") && (
            <div className="flex gap-4 justify-end pt-4">
              <button
                onClick={() => {
                  setImporterDialogOpen(false);
                  setImporterStatus("idle");
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Dashboard;
