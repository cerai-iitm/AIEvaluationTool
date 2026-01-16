import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";

interface TestPlan {
  plan_id: number;
  plan_name: string;
  plan_description: string;
  metric_names: string[];
  notes?: string;
}

interface TestPlanUpdateDialogProps {
  testPlan: TestPlan | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateSuccess?: () => void;
}

export default function TestPlanUpdateDialog({
  testPlan,
  open,
  onOpenChange,
  onUpdateSuccess,
}: TestPlanUpdateDialogProps) {
  const { toast } = useToast();
  const [description, setDescription] = useState("");
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [metricOptions, setMetricOptions] = useState<string[]>([]);
  const [isFetchingMetrics, setIsFetchingMetrics] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  // Fetch metrics from API
  const fetchMetrics = useCallback(async () => {
    setIsFetchingMetrics(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.TESTPLAN_METRICS_ALL, { headers });

      if (response.ok) {
        const metricsData = await response.json();
        setMetricOptions(Array.isArray(metricsData) ? metricsData : []);
      }
    } catch (error) {
      console.error("Error fetching metrics:", error);
    } finally {
      setIsFetchingMetrics(false);
    }
  }, []);

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
    if (open) {
      fetchMetrics();
      fetchUserRole();
    }
  }, [open, fetchMetrics]);

  useEffect(() => {
    if (testPlan) {
      setDescription(testPlan.plan_description || "");
      setSelectedMetrics(testPlan.metric_names || []);
      setNotes(testPlan.notes || "");
    }
  }, [testPlan]);

  const testPlanInitial: TestPlan = testPlan || {
    plan_id: 0,
    plan_name: "",
    plan_description: "",
    metric_names: [],
    notes: "",
  };

  const isChanged =
    description !== (testPlanInitial.plan_description || "") ||
    selectedMetrics.join(",") !== (testPlanInitial.metric_names || []).join(",") 

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric) ? prev.filter((m) => m !== metric) : [...prev, metric],
    );
  };

  const handleSubmit = async () => {
    if (!hasPermission(currentUserRole, "canUpdateTables") && !hasPermission(currentUserRole, "canUpdateRecords")) {
      toast({
        title: "Access Denied",
        description: "You don't have permission to update test plans",
        variant: "destructive",
      });
      return;
    }

    if (!testPlan?.plan_id) {
      toast({
        title: "Error",
        description: "Test plan ID is missing",
        variant: "destructive",
      });
      return;
    }

    if (!notes || !notes.trim()) {
      toast({
        title: "Validation Error",
        description: "Notes field is required",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const updatePayload: any = {
        plan_name: testPlan.plan_name,
        plan_description: description || null,
        metric_names: selectedMetrics.length > 0 ? selectedMetrics : [],
        notes: notes.trim() || null,
      };

      console.log("Updating test plan with payload:", updatePayload);
      console.log("Test Plan ID:", testPlan.plan_id);

      const response = await fetch(
        API_ENDPOINTS.TESTPLAN_UPDATE_V2(testPlan.plan_id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify(updatePayload),
        },
      );

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail
                .map((err: any) => {
                  if (typeof err === "string") return err;
                  if (err.msg)
                    return `${err.loc?.join(".") || "field"}: ${err.msg}`;
                  return JSON.stringify(err);
                })
                .join(", ");
            } else if (typeof errorData.detail === "string") {
              errorMessage = errorData.detail;
            } else {
              errorMessage = JSON.stringify(errorData.detail);
            }
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (parseError) {
          try {
            const errorText = await response.text();
            errorMessage = errorText || errorMessage;
          } catch {
            // Keep default error message
          }
        }
        throw new Error(errorMessage);
      }

      toast({
        title: "Success",
        description: "Test plan updated successfully",
      });

      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      onOpenChange(false);
    } catch (error) {
      console.error("Error updating test plan:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to update test plan",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!testPlan) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[90vh] overflow-y-auto"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="sr-only">Update Test Plan</DialogTitle>
        </DialogHeader>
        <div className="overflow-y-auto flex-1 space-y-2 pb-5 p-1">
          <div className="flex items-center justify-center gap-2 pb-4">
            <Label className="text-base font-semibold">Test Plan -</Label>
            <Label className="text-xl font-semibold text-primary hover:text-primary/90">
              {testPlan.plan_name}
            </Label>
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Description</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-muted min-h-[80px]"
              style={{
                maxHeight: "120px",
                minHeight: "70px",
                overflowY: "auto"
              }}
            />
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Metrics</Label>
            <div className="bg-muted p-4 rounded-md max-h-[200px] overflow-y-auto">
              {isFetchingMetrics ? (
                <div className="text-sm text-muted-foreground">
                  Loading metrics...
                </div>
              ) : metricOptions.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  No metrics available
                </div>
              ) : (
                <div className="space-y-2">
                  {metricOptions.map((metric) => (
                    <div key={metric} className="flex items-center space-x-2">
                      <Checkbox
                        id={`metric-${metric}`}
                        checked={selectedMetrics.includes(metric)}
                        onCheckedChange={() => handleMetricToggle(metric)}
                      />
                      <label
                        htmlFor={`metric-${metric}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                      >
                        {metric}
                      </label>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
          <Label className="text-base font-semibold mr-2">Notes :</Label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
            required
            placeholder="Enter notes"
            disabled={
              !hasPermission(currentUserRole, "canUpdateTables") &&
              !hasPermission(currentUserRole, "canUpdateRecords")
            }
          />
          <Button
            onClick={handleSubmit}
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!isChanged || !notes.trim() || isLoading ||
              (!hasPermission(currentUserRole, "canUpdateTables") &&
                !hasPermission(currentUserRole, "canUpdateRecords"))
            }
          >
            {isLoading ? "Submitting..." : "Submit"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { TestPlanUpdateDialog };

