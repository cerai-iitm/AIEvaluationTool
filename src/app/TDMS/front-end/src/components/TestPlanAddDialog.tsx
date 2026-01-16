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

interface TestPlanAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export default function TestPlanAddDialog({
  open,
  onOpenChange,
  onSuccess,
}: TestPlanAddDialogProps) {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [metricOptions, setMetricOptions] = useState<string[]>([]);
  const [isFetchingMetrics, setIsFetchingMetrics] = useState(false);

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
      toast({
        title: "Error",
        description: "Failed to load metrics",
        variant: "destructive",
      });
    } finally {
      setIsFetchingMetrics(false);
    }
  }, [toast]);

  useEffect(() => {
    if (open) {
      fetchMetrics();
    } else {
      // Reset form when dialog closes
      setName("");
      setDescription("");
      setSelectedMetrics([]);
      setNotes("");
    }
  }, [open, fetchMetrics]);

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric) ? prev.filter((m) => m !== metric) : [...prev, metric]
    );
  };

  const isFormValid = name.trim() && selectedMetrics.length > 0 && notes.trim();

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast({
        title: "Validation Error",
        description: "Test plan name is required",
        variant: "destructive",
      });
      return;
    }

    if (!notes.trim()) {
      toast({
        title: "Validation Error",
        description: "Notes field is required",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const payload = {
        plan_name: name.trim(),
        plan_description: description.trim() || null,
        metric_names: selectedMetrics,
        notes: notes.trim() || null,
      };

      const response = await fetch(API_ENDPOINTS.TESTPLAN_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("Test plan created successfully:", data);

      toast({
        title: "Success",
        description: "Test plan created successfully",
      });

      // Reset form
      setName("");
      setDescription("");
      setSelectedMetrics([]);
      setNotes("");

      // Close dialog
      onOpenChange(false);

      // Trigger refresh in parent component
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error("Error creating test plan:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to create test plan",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="sr-only">Add Test Plan</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label className="text-base font-semibold">Test Plan :</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter test plan name"
              required
              className="bg-muted"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-base font-semibold">Description :</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-muted min-h-[80px]"
              placeholder="Enter description..."
              style={{
                maxHeight: "120px",
                minHeight: "70px",
                overflowY: "auto"
              }}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-base font-semibold">Metrics :</Label>
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
                        id={`metric-add-${metric}`}
                        checked={selectedMetrics.includes(metric)}
                        onCheckedChange={() => handleMetricToggle(metric)}
                      />
                      <label
                        htmlFor={`metric-add-${metric}`}
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

          <div className="flex justify-center items-center p-4 ">
            <Label className="text-base font-semibold mr-2">Notes :</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Enter notes"
              className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
              required
            />

            <Button
              className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleSubmit}
              disabled={!isFormValid || isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Submit"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

