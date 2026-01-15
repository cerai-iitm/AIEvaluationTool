import { useCallback, useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import TestPlanUpdateDialog from "@/components/TestPlanUpdateDialog";
import TestPlanAddDialog from "@/components/TestPlanAddDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";

interface TestPlan {
  plan_id: number;
  plan_name: string;
  plan_description: string;
  metric_names: string[];
  notes?: string;
}

const TestPlans = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [selectedTestPlan, setSelectedTestPlan] = useState<TestPlan | null>(null);
  const [updateTestPlan, setUpdateTestPlan] = useState<TestPlan | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [testPlans, setTestPlans] = useState<TestPlan[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingTestPlans, setIsLoadingTestPlans] = useState(false);
  const [testPlansError, setTestPlansError] = useState<string | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testPlanToDelete, setTestPlanToDelete] = useState<TestPlan | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);

  const authHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }, []);

  const fetchTestPlans = useCallback(async () => {
    setIsLoadingTestPlans(true);
    setTestPlansError(null);
    try {
      const response = await fetch(API_ENDPOINTS.TESTPLANS_V2, {
        headers: authHeaders(),
      });

      if (!response.ok) {
        let message = `Unable to fetch test plans (status ${response.status})`;
        try {
          const data = await response.json();
          message = data?.detail ?? data?.message ?? message;
        } catch {
          // ignore json parse errors
        }
        throw new Error(message);
      }

      const data = await response.json();
      if (!Array.isArray(data)) {
        throw new Error("Unexpected response format while fetching test plans");
      }

      setTestPlans(data);
    } catch (error) {
      console.error("Failed to load test plans", error);
      setTestPlans([]);
      setTestPlansError(
        error instanceof Error ? error.message : "Failed to load test plans",
      );
    } finally {
      setIsLoadingTestPlans(false);
    }
  }, [authHeaders]);

  const fetchTestPlanDetails = useCallback(
    async (planId: number) => {
      setIsDetailLoading(true);
      setDetailError(null);
      setSelectedTestPlan(null);
      try {
        const response = await fetch(API_ENDPOINTS.TESTPLAN_BY_ID_V2(planId), {
          headers: authHeaders(),
        });

        if (!response.ok) {
          let message = `Unable to fetch test plan ${planId} (status ${response.status})`;
          try {
            const data = await response.json();
            message = data?.detail ?? data?.message ?? message;
          } catch {
            // ignore parse errors
          }
          throw new Error(message);
        }

        const data = await response.json();
        setSelectedTestPlan(data);
      } catch (error) {
        console.error("Failed to load test plan details", error);
        setDetailError(
          error instanceof Error
            ? error.message
            : "Failed to load test plan details",
        );
      } finally {
        setIsDetailLoading(false);
      }
    },
    [authHeaders],
  );

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
    fetchUserRole();
    fetchTestPlans();
  }, [fetchTestPlans, refreshKey]);

  const handleUpdateSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleDeleteClick = (testPlan: TestPlan) => {
    setTestPlanToDelete(testPlan);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!testPlanToDelete) return;

    setIsDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        API_ENDPOINTS.TESTPLAN_DELETE_V2(testPlanToDelete.plan_id),
        {
          method: "DELETE",
          headers,
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`,
        );
      }

      toast({
        title: "Success",
        description: "Test plan deleted successfully",
      });

      setDeleteDialogOpen(false);
      setTestPlanToDelete(null);
      setSelectedTestPlan(null);
      setIsDetailDialogOpen(false);
      handleUpdateSuccess();
      setHighlightedRowId(null);
    } catch (error) {
      console.error("Error deleting test plan:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete test plan",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredTestPlans = testPlans.filter(
    (tp) =>
      tp.plan_name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const totalItems = filteredTestPlans.length;
  const itemsPerPage = 15;
  const TotalPages = Math.ceil(totalItems / itemsPerPage);
  const paginatedTestPlans = useMemo(
    () =>
      filteredTestPlans.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage,
      ),
    [filteredTestPlans, currentPage],
  );

  const handleSelectTestPlan = (planId: number) => {
    setIsDetailDialogOpen(true);
    fetchTestPlanDetails(planId);
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-224px bg-[#5252c2] z-20">
        <Sidebar />
      </aside>
      <main className="flex-1 bg-background ml-[224px] ">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Test Plans</h1>
          <div className="flex gap-4 mb-6">
            <Select defaultValue="plan">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="plan">Plan Name</SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-64"
            />
            <div className="ml-auto flex items-center gap-4">
              <HistoryButton
                entityType="TestPlan"
                title="Test Plans"
                idField="testCaseId"
                idLabel="Plan ID"
                entityId={selectedTestPlan?.plan_id}
              />
              <span className="test-sm text-muted-foreground">
                {totalItems === 0
                  ? "0"
                  : `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(
                      currentPage * itemsPerPage,
                      totalItems,
                    )} of ${totalItems}`}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(TotalPages, p + 1))
                  }
                  disabled={currentPage === TotalPages}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-w-7xl mx-left max-h-[67vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      ID
                    </th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      Plan Name
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingTestPlans ? (
                    <tr>
                      <td className="p-4 text-center" colSpan={2}>
                        Loading test plans...
                      </td>
                    </tr>
                  ) : testPlansError ? (
                    <tr>
                      <td
                        className="p-4 text-center text-destructive"
                        colSpan={2}
                      >
                        {testPlansError}
                      </td>
                    </tr>
                  ) : paginatedTestPlans.length === 0 ? (
                    <tr>
                      <td className="p-4 text-center" colSpan={2}>
                        No test plans found.
                      </td>
                    </tr>
                  ) : (
                    paginatedTestPlans.map((testPlan) => (
                      <tr
                        key={testPlan.plan_id}
                        className={`border-b cursor-pointer transition-colors duration-200 ${highlightedRowId === testPlan.plan_id ? "bg-primary/10 hover:bg-primary/15 border-primary//30" : "hover:bg-muted/50"}`}
                        onClick={() => {
                          handleSelectTestPlan(testPlan.plan_id);
                          setHighlightedRowId(testPlan.plan_id);
                        }}
                      >
                        <td className="p-2 pl-12">{testPlan.plan_id}</td>
                        <td className="p-2 pl-6 capitalize">{testPlan.plan_name}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          {(hasPermission(currentUserRole, "canCreateTables") ||
            hasPermission(currentUserRole, "canCreateRecords")) && (
            <div className="mt-1 sticky bottom-5">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setAddDialogOpen(true)}
              >
                + Add Plan
              </Button>
            </div>
          )}
        </div>
      </main>

      {/* Details/Edit Dialog */}
      <Dialog
        open={isDetailDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setIsDetailDialogOpen(false);
            setSelectedTestPlan(null);
            setDetailError(null);
          }
        }}
      >
        <DialogContent
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">Test Plan Details</DialogTitle>
          </DialogHeader>
          {isDetailLoading ? (
            <div className="p-4 text-center">Loading test plan details...</div>
          ) : detailError ? (
            <div className="p-4 text-center text-destructive">
              {detailError}
            </div>
          ) : selectedTestPlan ? (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="flex items-center justify-center gap-2">
                <Label className="text-base font-semibold">Test Plan -  </Label>
                <Label className="text-xl font-semibold text-primary hover:text-primary/90">
                  {selectedTestPlan.plan_name}
                </Label>
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Description</Label>
                <Textarea
                  value={selectedTestPlan.plan_description || ""}
                  readOnly
                  className="bg-muted min-h-[80px]"
                ></Textarea>
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Metrics</Label>
                <div className="bg-muted p-4 rounded-md min-h-[80px]">
                  {selectedTestPlan.metric_names && selectedTestPlan.metric_names.length > 0 ? (
                    <div className="space-y-2">
                      {selectedTestPlan.metric_names.map((metric) => (
                        <div key={metric} className="text-sm">
                          {metric}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">No metrics assigned</div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 text-center">No test plan selected.</div>
          )}
          <div className="sticky bottom-0 pt-4 flex justify-center gap-4 border-gray-200 z-10">
            {hasPermission(currentUserRole, "canDeleteTables") && (
              <Button
                variant="destructive"
                onClick={() =>
                  selectedTestPlan && handleDeleteClick(selectedTestPlan)
                }
              >
                Delete
              </Button>
            )}
            {hasPermission(currentUserRole, "canUpdateTables") && (
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => {
                  if (selectedTestPlan) {
                    setUpdateTestPlan(selectedTestPlan);
                  }
                  setIsDetailDialogOpen(false);
                }}
              >
                <p className="text-white px-2.5">Update</p>
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Update Test Plan Dialog */}
      <TestPlanUpdateDialog
        testPlan={updateTestPlan}
        open={!!updateTestPlan}
        onOpenChange={(open) => !open && setUpdateTestPlan(null)}
        onUpdateSuccess={handleUpdateSuccess}
      />

      {/* Add Test Plan Dialog */}
      <TestPlanAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={handleUpdateSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the following test plan? This action
              cannot be undone.
              {testPlanToDelete && (
                <div className="mt-4 p-4 bg-muted rounded-md">
                  <p className="font-semibold">
                    Plan ID: {testPlanToDelete.plan_id}
                  </p>
                  <p className="font-semibold">
                    Plan Name: {testPlanToDelete.plan_name}
                  </p>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TestPlans;

