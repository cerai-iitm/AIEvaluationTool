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
import { PromptUpdateDialog } from "@/components/PromptUpdateDialog";
import { PromptAddDialog } from "@/components/PromptAddDialog";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";
import { hasPermission } from "@/utils/permissions";

interface PromptItem {
  prompt_id: number;
  user_prompt: string;
  system_prompt: string;
  language: string | null;
  domain: string | null;
}

const Prompts = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPrompt, setSelectedPrompt] = useState<PromptItem | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState<PromptItem | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [promptToDelete, setPromptToDelete] = useState<PromptItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  const fetchPrompts = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(API_ENDPOINTS.PROMPTS_V2, {
        method: "GET",
        headers,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to fetch prompts");
      }
      const data = await response.json();
      setPrompts(data);
    } catch (error: any) {
      console.error("Failed to load prompts:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load prompts",
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
    fetchPrompts();
  }, [fetchPrompts]);

  const filteredPrompts = useMemo(
    () =>
      prompts.filter((p) => {
        const query = searchQuery.toLowerCase();
        return (
          p.user_prompt.toLowerCase().includes(query) ||
          (p.language?.toLowerCase() ?? "").includes(query) ||
          (p.domain?.toLowerCase() ?? "").includes(query)
        );
      }),
    [prompts, searchQuery],
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
        API_ENDPOINTS.PROMPT_DELETE_V2(promptToDelete.prompt_id),
        {
          method: "DELETE",
          headers,
        },
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete prompt");
      }
      toast({
        title: "Prompt deleted",
        description: `Prompt ${promptToDelete.prompt_id} was deleted successfully.`,
      });
      setDeleteDialogOpen(false);
      setPromptToDelete(null);
      fetchPrompts();
    } catch (error: any) {
      console.error("Delete prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to delete prompt",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const openDeleteDialog = (prompt: PromptItem) => {
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
          <h1 className="text-4xl font-bold mb-8 text-center">Prompts</h1>

          <div className="flex gap-4 mb-6 ">
            <Select defaultValue="promptname">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="promptname">Prompt Name</SelectItem>
                <SelectItem value="domain">Domain</SelectItem>
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
                    Loading prompts...
                  </span>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">
                        Prompt ID
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">
                        User Prompt
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                        Language
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">
                        Domain
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedPrompts.length === 0 ? (
                      <tr>
                        <td
                          colSpan={4}
                          className="p-6 text-center text-muted-foreground"
                        >
                          No prompts found
                        </td>
                      </tr>
                    ) : (
                      paginatedPrompts.map((row) => (
                        <tr
                          key={row.prompt_id}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => setSelectedPrompt(row)}
                        >
                          <td className="p-2 text-center">{row.prompt_id}</td>
                          <td className="p-2 truncate max-w-[650px] pr-8 mr-2">
                            {row.user_prompt}
                          </td>
                          <td className="p-2 ">{row.language ?? "—"}</td>
                          <td className="p-2 ">{row.domain ?? "—"}</td>
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
                + Add Prompt
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
            <DialogTitle className="sr-only">Prompt Details</DialogTitle>
          </DialogHeader>

          {selectedPrompt && (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="space-y-1">
                <Label className="text-base font-semibold">User Prompt</Label>
                <Textarea
                  value={selectedPrompt.user_prompt}
                
                  className="bg-muted min-h-[80px]"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">System Prompt</Label>
                <Textarea
                  value={selectedPrompt.system_prompt}
                  
                  className="bg-muted min-h-[80px]"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">language Name</Label>
                <Input
                  value={selectedPrompt.language ?? ""}
                  readOnly
                  className="bg-muted"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Domain Name</Label>
                <Input
                  value={selectedPrompt.domain ?? ""}
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
                onClick={() =>
                  selectedPrompt && openDeleteDialog(selectedPrompt)
                }
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

      <PromptUpdateDialog
        prompt={updatePrompt}
        open={!!updatePrompt}
        onOpenChange={(open) => {
          if (!open) {
            setUpdatePrompt(null);
          }
        }}
        onSuccess={() => {
          setUpdatePrompt(null);
          fetchPrompts();
        }}
      />

      <PromptAddDialog
        open={addDialogOpen}
        onOpenChange={(open) => setAddDialogOpen(open)}
        onSuccess={() => {
          setAddDialogOpen(false);
          fetchPrompts();
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
            <DialogTitle>Delete Prompt</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Are you sure you want to delete the following Prompt? This action
              cannot be undone.
            </p>
            {promptToDelete && (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p>
                  <span className="font-semibold">Prompt ID:</span>{" "}
                  {promptToDelete.prompt_id}
                </p>
                <p className="mt-2 line-clamp-3">
                  <span className="font-semibold">User Prompt:</span>{" "}
                  {promptToDelete.user_prompt}
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

export default Prompts;
