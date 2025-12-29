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
import TargetUpdateDialog from "@/components/TargetUpdateDialog";
import TargetAddDialog from "@/components/TargetAddDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";

interface Target {
  target_id: number;
  target_name: string;
  target_type: string;
  target_description: string;
  target_url: string;
  domain_name: string;
  lang_list: string[];
  notes?: string;
}

const Targets = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);
  const [updateTarget, setUpdateTarget] = useState<Target | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [targets, setTargets] = useState<Target[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingTargets, setIsLoadingTargets] = useState(false);
  const [targetsError, setTargetsError] = useState<string | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [targetToDelete, setTargetToDelete] = useState<Target | null>(null);
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

  const fetchTargets = useCallback(async () => {
    setIsLoadingTargets(true);
    setTargetsError(null);
    try {
      const response = await fetch(API_ENDPOINTS.TARGETS_V2, {
        headers: authHeaders(),
      });

      if (!response.ok) {
        let message = `Unable to fetch targets (status ${response.status})`;
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
        throw new Error("Unexpected response format while fetching targets");
      }

      setTargets(data);
    } catch (error) {
      console.error("Failed to load targets", error);
      setTargets([]);
      setTargetsError(
        error instanceof Error ? error.message : "Failed to load targets",
      );
    } finally {
      setIsLoadingTargets(false);
    }
  }, [authHeaders]);

  const fetchTargetDetails = useCallback(
    async (targetId: number) => {
      setIsDetailLoading(true);
      setDetailError(null);
      setSelectedTarget(null);
      try {
        const response = await fetch(API_ENDPOINTS.TARGET_BY_ID_V2(targetId), {
          headers: authHeaders(),
        });

        if (!response.ok) {
          let message = `Unable to fetch target ${targetId} (status ${response.status})`;
          try {
            const data = await response.json();
            message = data?.detail ?? data?.message ?? message;
          } catch {
            // ignore parse errors
          }
          throw new Error(message);
        }

        const data = await response.json();
        setSelectedTarget(data);
      } catch (error) {
        console.error("Failed to load target details", error);
        setDetailError(
          error instanceof Error
            ? error.message
            : "Failed to load target details",
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
    if (open) {
      fetchUserRole();
      fetchTargets();
    }
  
  }, [open, refreshKey]);

  const handleUpdateSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleDeleteClick = (target: Target) => {
    setTargetToDelete(target);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!targetToDelete) return;

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
        API_ENDPOINTS.TARGET_DELETE_V2(targetToDelete.target_id),
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
        description: "Target deleted successfully",
      });

      setDeleteDialogOpen(false);
      setTargetToDelete(null);
      setSelectedTarget(null);
      setIsDetailDialogOpen(false);
      handleUpdateSuccess();
      setHighlightedRowId(null);
    } catch (error) {
      console.error("Error deleting target:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete target",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredTargets = targets.filter(
    (t) =>
      t.target_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.target_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.domain_name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const totalItems = filteredTargets.length;
  const itemsPerPage = 15;
  const TotalPages = Math.ceil(totalItems / itemsPerPage);
  const paginatedTargets = useMemo(
    () =>
      filteredTargets.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage,
      ),
    [filteredTargets, currentPage],
  );

  const handleUrlClick = (url: string) => {
    window.open(url, "_blank");
  };

  const handleSelectTarget = (targetId: number) => {
    setIsDetailDialogOpen(true);
    fetchTargetDetails(targetId);
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-224px bg-[#5252c2] z-20">
        <Sidebar />
      </aside>
      <main className="flex-1 bg-background ml-[224px] ">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Targets</h1>
          <div className="flex gap-4 mb-6">
            <Select defaultValue="target">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="target">Target Name</SelectItem>
                <SelectItem value="type">Target Type</SelectItem>
                <SelectItem value="domain">Domain Name</SelectItem>
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
            {/* <Button className="ml-auto" onClick={() => setAddDialogOpen(true)}>+ Add Target</Button> */}
            <div className="ml-auto flex items-center gap-4">
              <HistoryButton
                entityType="Target"
                title="Targets"
                idField="testCaseId"
                idLabel="Target ID"
                entityId={selectedTarget?.target_id}
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
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] max-w-[120vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      Target ID
                    </th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      Target Name
                    </th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      Target Type & URL
                    </th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                      Domain Name
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingTargets ? (
                    <tr>
                      <td className="p-4 text-center" colSpan={4}>
                        Loading targets...
                      </td>
                    </tr>
                  ) : targetsError ? (
                    <tr>
                      <td
                        className="p-4 text-center text-destructive"
                        colSpan={4}
                      >
                        {targetsError}
                      </td>
                    </tr>
                  ) : paginatedTargets.length === 0 ? (
                    <tr>
                      <td className="p-4 text-center" colSpan={4}>
                        No targets found.
                      </td>
                    </tr>
                  ) : (
                    paginatedTargets.map((target) => (
                      <tr
                        key={target.target_id}
                        className={`border-b cursor-pointer transition-colors duration-200 ${highlightedRowId === target.target_id ? "bg-primary/10 hover:bg-primary/15 border-primary//30" : "hover:bg-muted/50"}`}
                        onClick={() => {
                          handleSelectTarget(target.target_id);
                          setHighlightedRowId(target.target_id);
                        }}
                      >
                        <td className="p-2 pl-12">{target.target_id}</td>
                        <td className="p-2 pl-6 capitalize">{target.target_name}</td>
                        <td className="p-2 pl-12">
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              handleUrlClick(target.target_url);
                            }}
                            style={{
                              color: "#3b82f6",
                              textDecoration: "underline",
                              cursor: "pointer",
                            }}
                          >
                            {target.target_type}
                          </span>
                        </td>
                        <td className="p-2 pl-8 capitalize">{target.domain_name}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          {(hasPermission(currentUserRole, "canCreateTables") ||
            hasPermission(currentUserRole, "canCreateRecords")) && (
            <div className="mt-6 sticky bottom-5">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setAddDialogOpen(true)}
              >
                + Add Target
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
            setSelectedTarget(null);
            setDetailError(null);
          }
        }}
      >
        <DialogContent
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">Target Details</DialogTitle>
          </DialogHeader>
          {/* ...show target details... */}
          {isDetailLoading ? (
            <div className="p-4 text-center">Loading target details...</div>
          ) : detailError ? (
            <div className="p-4 text-center text-destructive">
              {detailError}
            </div>
          ) : selectedTarget ? (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="flex items-center justify-center gap-2">
                <Label className="text-base font-semibold">Target Name -  </Label>
                <Label className="text-xl font-semibold text-primary hover:text-primary/90">
                  {selectedTarget.target_name}
                </Label>
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Description</Label>
                <Textarea
                  value={selectedTarget.target_description}
                  readOnly
                  className="bg-muted min-h-[80px]"
                ></Textarea>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-base font-semibold">Type</Label>
                  <Input
                    value={selectedTarget.target_type}
                    readOnly
                    className="bg-muted capitalize"
                  ></Input>
                </div>
                <div className="space-y-1">
                  <Label className="text-base font-semibold">Domain</Label>
                  <Input
                    value={selectedTarget.domain_name}
                    readOnly
                    className="bg-muted capitalize "
                  ></Input>
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">URL</Label>
                <Input
                  value={selectedTarget.target_url}
                  readOnly
                  className="bg-muted"
                ></Input>
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">Languages</Label>
                <Input
                  value={selectedTarget.lang_list.join(" , ")}
                  readOnly
                  className="bg-muted capitalize"
                ></Input>
              </div>

            </div>
          ) : (
            <div className="p-4 text-center">No target selected.</div>
          )}
          <div className="sticky bottom-0 pt-4 flex justify-center gap-4 border-gray-200 z-10">
            {hasPermission(currentUserRole, "canDeleteTables") && (
              <Button
                variant="destructive"
                onClick={() =>
                  selectedTarget && handleDeleteClick(selectedTarget)
                }
              >
                Delete
              </Button>
            )}
            {hasPermission(currentUserRole, "canUpdateTables") && (
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => {
                  if (selectedTarget) {
                    setUpdateTarget(selectedTarget);
                  }
                  setIsDetailDialogOpen(false);
                }}
              >
                <p className="text-white px-2.5">Edit</p>
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Update Target Dialog */}
      <TargetUpdateDialog
        target={updateTarget}
        open={!!updateTarget}
        onOpenChange={(open) => !open && setUpdateTarget(null)}
        onUpdateSuccess={handleUpdateSuccess}
      />

      {/* Add Target Dialog */}
      <TargetAddDialog
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
              Are you sure you want to delete the following target? This action
              cannot be undone.
              {targetToDelete && (
                <div className="mt-4 p-4 bg-muted rounded-md">
                  <p className="font-semibold">
                    Target ID: {targetToDelete.target_id}
                  </p>
                  <p className="font-semibold">
                    Target Name: {targetToDelete.target_name}
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

export default Targets;
