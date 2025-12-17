import { useCallback, useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Input } from "@/components/ui/input";
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
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  LlmPromptUpdateDialog,
  LlmPromptItem,
} from "@/components/LlmPromptUpdateDialog";
import { LlmPromptAddDialog } from "@/components/LlmPromptAddDialog";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";

const LlmPrompts = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPrompt, setSelectedPrompt] = useState<LlmPromptItem | null>(
    null,
  );
  const [updatePrompt, setUpdatePrompt] = useState<LlmPromptItem | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [llmPrompts, setLlmPrompts] = useState<LlmPromptItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [promptToDelete, setPromptToDelete] = useState<LlmPromptItem | null>(
    null,
  );
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  const fetchLlmPrompts = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(API_ENDPOINTS.LLMPROMPTS_V2, {
        method: "GET",
        headers,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to fetch LLM prompts");
      }
      const data = await response.json();
      setLlmPrompts(data);
    } catch (error: any) {
      console.error("Failed to load LLM prompts:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load LLM prompts",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

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
    fetchLlmPrompts();
  }, [fetchLlmPrompts]);

  const filteredPrompts = useMemo(
    () =>
      llmPrompts.filter((p) => {
        const query = searchQuery.toLowerCase();
        return (
          p.prompt.toLowerCase().includes(query) ||
          (p.language?.toLowerCase() ?? "").includes(query)
        );
      }),
    [llmPrompts, searchQuery],
  );

  const totalItems = filteredPrompts.length;
  const itemsPerPage = 15;
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));

  const paginatedPrompts = filteredPrompts.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  const handleDeletePrompt = async () => {
    if (!promptToDelete) return;
    setIsDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(
        API_ENDPOINTS.LLMPROMPT_DELETE_V2(promptToDelete.llmPromptId),
        {
          method: "DELETE",
          headers,
        },
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete LLM prompt");
      }
      toast({
        title: "LLM Prompt deleted",
        description: `LLM Prompt ${promptToDelete.llmPromptId} was deleted successfully.`,
      });
      setDeleteDialogOpen(false);
      setPromptToDelete(null);
      fetchLlmPrompts();
    } catch (error: any) {
      console.error("Delete LLM prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to delete LLM prompt",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const openDeleteDialog = (prompt: LlmPromptItem) => {
    setSelectedPrompt(null);
    setPromptToDelete(prompt);
    setDeleteDialogOpen(true);
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">LLM Prompts</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="llmprompts">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="llmprompts">LLM Prompts</SelectItem>
                <SelectItem value="language">Language</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />
            <div className="ml-auto flex items-center gap-4">
              <HistoryButton
                entityType="LLM Prompt"
                title="LLM Prompts"
                idField="llmPromptId"
                idLabel="Prompt ID"
              />
              <span className="text-sm text-muted-foreground">
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
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <span className="ml-2 text-sm text-muted-foreground">
                    Loading LLM prompts...
                  </span>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">
                        Prompt ID
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                        LLM Prompts
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                        Language
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedPrompts.length === 0 ? (
                      <tr>
                        <td
                          colSpan={3}
                          className="p-6 text-center text-muted-foreground"
                        >
                          No LLM prompts found
                        </td>
                      </tr>
                    ) : (
                      paginatedPrompts.map((row) => (
                        <tr
                          key={row.llmPromptId}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => setSelectedPrompt(row)}
                        >
                          <td className="p-2 text-center">{row.llmPromptId}</td>
                          <td className="p-2 truncate max-w-[650px] pr-8 mr-2">
                            {row.prompt}
                          </td>
                          <td className="p-2">{row.language ?? "—"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {(hasPermission(currentUserRole, "canCreateTables") ||
            hasPermission(currentUserRole, "canCreateRecords")) && (
            <div className="mt-6 sticky bottom-5">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setAddDialogOpen(true)}
              >
                + Add Prompts
              </Button>
            </div>
          )}
        </div>
      </main>

      <Dialog
        open={!!selectedPrompt}
        onOpenChange={() => setSelectedPrompt(null)}
      >
        <DialogContent
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">LLM Prompt Details</DialogTitle>
          </DialogHeader>

          {selectedPrompt && (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="space-y-1">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <Textarea
                  value={selectedPrompt.prompt}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Language</Label>
                <Input
                  value={selectedPrompt.language ?? "—"}
                  readOnly
                  className="bg-muted"
                />
              </div>
            </div>
          )}

          <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center gap-4 border-gray-200 z-10">
            {hasPermission(currentUserRole, "canDeleteTables") && (
              <Button
                variant="destructive"
                onClick={() => openDeleteDialog(selectedPrompt!)}
              >
                Delete
              </Button>
            )}
            {(hasPermission(currentUserRole, "canUpdateTables") ||
              hasPermission(currentUserRole, "canUpdateRecords")) && (
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => {
                  setUpdatePrompt(selectedPrompt);
                  setSelectedPrompt(null);
                }}
              >
                <p className="text-white px-2.5">Edit</p>
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <LlmPromptUpdateDialog
        prompt={updatePrompt}
        open={!!updatePrompt}
        onOpenChange={(open) => {
          if (!open) {
            setUpdatePrompt(null);
          }
        }}
        onSuccess={() => {
          setUpdatePrompt(null);
          fetchLlmPrompts();
        }}
      />

      <LlmPromptAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={() => {
          setAddDialogOpen(false);
          fetchLlmPrompts();
        }}
      />

      <Dialog
        open={deleteDialogOpen}
        onOpenChange={(open) => {
          setDeleteDialogOpen(open);
          if (!open) {
            setPromptToDelete(null);
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete LLM Prompt</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Are you sure you want to delete the following LLM Prompt? This
              action cannot be undone.
            </p>
            {promptToDelete && (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p>
                  <span className="font-semibold">Prompt ID:</span>{" "}
                  {promptToDelete.llmPromptId}
                </p>
                <p className="mt-2 line-clamp-3">
                  <span className="font-semibold">Prompt:</span>{" "}
                  {promptToDelete.prompt}
                </p>
              </div>
            )}
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setPromptToDelete(null);
              }}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeletePrompt}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LlmPrompts;
