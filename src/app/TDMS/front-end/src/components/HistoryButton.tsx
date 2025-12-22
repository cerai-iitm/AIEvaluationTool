import React, { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { API_ENDPOINTS } from "@/config/api";

interface Activity {
  description: string;
  type: string;
  status: string;
  timestamp: string;
  user_name: string;
  [key: string]: any; // allows id fields like testCaseId, domainId, etc.
}

interface EntityHistoryProps {
  entityType: string; // e.g. "Test Case"
  title: string; // e.g. "Test Cases"
  idField: string; // e.g. "testCaseId"
  idLabel: string; // e.g. "Test Case ID"
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const getStatusColor = (status: string) => {
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

const EntityHistoryDialog: React.FC<EntityHistoryProps> = ({
  entityType,
  title,
  idField,
  idLabel,
  open,
  onOpenChange,
}) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    const fetchHistory = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const encodedEntityType = encodeURIComponent(entityType);
        const response = await fetch(API_ENDPOINTS.ENTITY_ACTIVITY(encodedEntityType), {
          headers,
        });

        if (response.ok) {
          const data: Activity[] = await response.json();
          setActivities(Array.isArray(data) ? data : []);
        } else {
          setActivities([]);
        }
      } catch {
        setActivities([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [open, entityType]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader className="mt-4 sticky top-0 mb-2 bg-white rounded-lg px-4 py-4 shadow-md">
          <DialogTitle className="sticky">History - {title}</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-lg text-muted-foreground">Loading history...</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-lg text-muted-foreground">
              No history found for {title}.
            </p>
          </div>
        ) : (
          <div className="space-y-4 mt-4">
            {activities.map((activity, index) => {
              const entityId =
                activity[idField] ??
                activity.entityId ??
                activity.entity_id ??
                "";

              return (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="w-4 h-4 rounded-full bg-primary" />
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">
                            {activity.user_name}
                          </p>
                        </div>
                      </div>
                      <p className="text-lg mb-2">{activity.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2 justify-end mb-1">
                        {entityId && (
                          <>
                            <span className="font-medium">
                               {entityId}
                            </span>
                            <span className="text-xl">-</span>
                          </>
                        )}
                        {activity.status && (
                          <span
                            className={`font-semibold ${getStatusColor(
                              activity.status,
                            )}`}
                          >
                            {activity.status}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {activity.timestamp}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

interface HistoryButtonProps {
  entityType: string;
  title: string;
  idField: string;
  idLabel: string;
}

export const HistoryButton: React.FC<HistoryButtonProps> = ({
  entityType,
  title,
  idField,
  idLabel,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="History"
        className="flex items-center justify-center rounded-full p-1 hover:bg-muted transition-colors mr-1"
      >
        <img
          src="src/assets/icons8-history-50.png"
          alt="History"
          className="w-5 h-5"
        />
      </button>
      <EntityHistoryDialog
        entityType={entityType}
        title={title}
        idField={idField}
        idLabel={idLabel}
        open={open}
        onOpenChange={setOpen}
      />
    </>
  );
};


