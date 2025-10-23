import { useParams } from "react-router-dom";
import Sidebar from "@/components/Sidebar";

interface Activity {
  description: string;
  type: string;
  testCaseId: string;
  status: "Created" | "Updated" | "Deleted";
  timestamp: string;
}

const UserHistory = () => {
  const { username } = useParams();

  const activities: Activity[] = [
    {
      description: "Column added language ID",
      type: "Test Case",
      testCaseId: "P312",
      status: "Deleted",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "File import and some other changes made",
      type: "Test Case",
      testCaseId: "P312",
      status: "Updated",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "Initial commit",
      type: "Target",
      testCaseId: "Gooye",
      status: "Created",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "Column added language ID",
      type: "Test Case",
      testCaseId: "P312",
      status: "Deleted",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "File import and some other changes made",
      type: "Target",
      testCaseId: "Vaidya",
      status: "Updated",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "Initial commit",
      type: "Test Case",
      testCaseId: "P312",
      status: "Created",
      timestamp: "2025-09-03 13:40",
    },
    {
      description: "Initial commit",
      type: "Test Case",
      testCaseId: "P312",
      status: "Created",
      timestamp: "2025-09-03 13:40",
    },
  ];

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
      <Sidebar />

      <main className="flex-1 bg-background p-8">
        <h1 className="text-4xl font-bold mb-12">Activity of {username}</h1>

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
      </main>
    </div>
  );
};

export default UserHistory;
