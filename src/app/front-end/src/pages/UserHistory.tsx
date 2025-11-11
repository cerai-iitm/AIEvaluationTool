import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";

interface Activity {
  description: string;
  type: string;
  testCaseId: string;
  status: "Created" | "Updated" | "Deleted";
  timestamp: string;
}

const UserHistory = () => {
  const { username } = useParams();
  const { toast } = useToast();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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
      <aside className="fixed top-0 left-0 h-screen w-[220px] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 ml-[220px] p-28 min-h-screen items-center justify-center">
        <h1 className="text-4xl font-bold mb-12">
          Activity of {username ? decodeURIComponent(username) : "User"}
        </h1>

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
                  <p className="text-xl font-semibold">{activity.type}</p>
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
      </main>
    </div>
  );
};

export default UserHistory;
