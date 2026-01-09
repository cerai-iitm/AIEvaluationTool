import { useState, useEffect, useCallback } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ResponseUpdateDialog } from "@/components/ResponseUpdateDialog";
import { ResponseAddDialog } from "@/components/ResponseAddDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";

interface Response {
  response_id: number;
  response_text: string;
  response_type: string;
  language: string;
  user_prompt: string;
  system_prompt: string;
}

const Responses = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedResponse, setSelectedResponse] = useState<Response | null>(
    null,
  );
  const [updateResponse, setUpdateResponse] = useState<Response | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [responseToDelete, setResponseToDelete] = useState<Response | null>(
    null,
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [responses, setResponses] = useState<Response[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const itemsPerPage = 15;

  const [searchField, setSearchField] = useState<"responsetext" | "language" | "responsetype">("responsetext");
  const [currentUserRole, setCurrentUserRole] = useState<string>("");

  const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);

  const fetchResponses = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.RESPONSES_V2, { headers });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setResponses(data);
      } else {
        console.error("Unexpected responses data format:", data);
        toast({
          title: "Error",
          description: "Failed to load responses",
          variant: "destructive",
        });
        setResponses([]);
      }
    } catch (error) {
      console.error("Error fetching responses:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to load responses from server",
        variant: "destructive",
      });
      setResponses([]);
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
    fetchResponses();
  }, [fetchResponses, refreshKey]);

  const handleUpdateSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleDeleteClick = (response: Response) => {
    setResponseToDelete(response);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!responseToDelete) return;

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
        API_ENDPOINTS.RESPONSE_DELETE_V2(responseToDelete.response_id),
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
        description: "Response deleted successfully",
      });

      setDeleteDialogOpen(false);
      setResponseToDelete(null);
      setSelectedResponse(null);
      handleUpdateSuccess();
    } catch (error) {
      console.error("Error deleting response:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete response",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredResponses = responses.filter(
    (response) => { 
      const  q = searchQuery.toLowerCase();
      if (!q) return true;

      if (searchField === "responsetext") {
        return response.response_text.toLowerCase().includes(q);
      } else if (searchField === "language") {
        return response.language.toLowerCase().includes(q);
      } else if (searchField === "responsetype") {
        return response.response_type.toLowerCase().includes(q);
      } 

      // response.response_text
      //   .toLowerCase()
      //   .includes(searchQuery.toLowerCase()) ||
      // response.language.toLowerCase().includes(searchQuery.toLowerCase()) ||
      // response.response_type
      //   .toLowerCase()
      //   .includes(searchQuery.toLowerCase()) ||
      // response.response_id.toString().includes(searchQuery.toLowerCase()),
  });

  const totalItems = filteredResponses.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const paginatedResponses = filteredResponses.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8">
          <h1 className="text-4xl font-bold mb-8 text-center">Responses</h1>

          <div className="flex gap-4 mb-6 flex-wrap">
            <Select 
              defaultValue="responsetext"
              onValueChange={(value: "responsetext" | "language" | "responsetype") => setSearchField(value)}
            >
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {/* <SelectItem value="responseid">Response ID</SelectItem> */}
                <SelectItem value="responsetext">Response Text</SelectItem>
                <SelectItem value="language">Language</SelectItem>
                <SelectItem value="responsetype">Response Type</SelectItem>
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
                entityType="Response"
                title="Responses"
                idField="testCaseId"
                idLabel="Response ID"
              />
              <span className="text-sm text-muted-foreground">
                {isLoading
                  ? "Loading..."
                  : totalItems === 0
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
                  disabled={currentPage === 1 || isLoading}
                >
                  <ChevronLeft className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage === totalPages || isLoading}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden max-h-[72vh] w-full max-w-[100%] mx-left overflow-y-auto">
            <table className="w-full">
              <thead className="border-b-2">
                <tr>
                  <th className="sticky top-0 bg-white text-left p-4 font-semibold">Response ID</th>
                  <th className="sticky top-0 bg-white text-left p-4 font-semibold">Response Text</th>
                  <th className="sticky top-0 bg-white text-left p-4 font-semibold">Language</th>
                  <th className="sticky top-0 bg-white text-left p-4 font-semibold">Response Type</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span className="text-muted-foreground">
                          Loading responses...
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : paginatedResponses.length === 0 ? (
                  <tr>
                    <td
                      colSpan={4}
                      className="p-8 text-center text-muted-foreground"
                    >
                      No responses found
                    </td>
                  </tr>
                ) : (
                  paginatedResponses.map((response) => (
                    <tr
                      key={response.response_id}
                      className={`border-b cursor-pointer transition-colors duration-200 ${
                        highlightedRowId === response.response_id ? "bg-primary/10 hover:bg-primary/15 border-primary/30" : "hover:bg-muted/60"
                      }`}
                      onClick={() => {
                        setSelectedResponse(response);
                        setHighlightedRowId(response.response_id);
                      }}
                    >
                      <td className="p-2 pl-12">{response.response_id}</td>
                      <td className="p-2 max-w-md truncate">
                        {response.response_text}
                      </td>
                      <td className="p-2 pl-8 capitalize">{response.language}</td>
                      <td className="p-2 pl-12">{response.response_type}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* {(hasPermission(currentUserRole, "canCreateTables") ||
            hasPermission(currentUserRole, "canCreateRecords")) && (
            <div className="mt-1 sticky bottom-5">
              <Button
                className="bg-primary hover:bg-primary/90"
                onClick={() => setAddDialogOpen(true)}
              >
                + Add Response
              </Button>
            </div>
          )} */}
        </div>
      </main>

      <Dialog
        open={!!selectedResponse}
        onOpenChange={() => setSelectedResponse(null)}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Response Details</DialogTitle>
          </DialogHeader>

          {selectedResponse && (
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label className="text-base font-semibold">Responses</Label>
                <Textarea
                  value={selectedResponse.response_text}
                  readOnly
                  className="bg-muted min-h-[100px]"
                  style={{
                    height: '${height}px',
                    maxHeight: "120px",
                    minHeight: "75px",
                    overflowY: "auto"
                  }}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-base font-semibold">Type</Label>
                  <Input
                    value={selectedResponse.response_type}
                    readOnly
                    className="bg-muted"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-base font-semibold">Language</Label>
                  <Input
                    value={selectedResponse.language}
                    readOnly
                    className="bg-muted capitalize"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">User Prompt</Label>
                <Textarea
                  value={selectedResponse.user_prompt}
                  readOnly
                  className="bg-muted min-h-[80px]"
                  style={{
                    height: '${height}px',
                    maxHeight: "120px",
                    minHeight: "75px",
                    overflowY: "auto"
                  }}
                />
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">System Prompt</Label>
                <Textarea
                  value={selectedResponse.system_prompt}
                  readOnly
                  className="bg-muted min-h-[80px]"
                  style={{
                    height: '${height}px',
                    maxHeight: "120px",
                    minHeight: "75px",
                    overflowY: "auto"
                  }}
                />
              </div>

              <div className="flex justify-center gap-4 pt-4">
                {hasPermission(currentUserRole, "canDeleteTables") && (
                  <Button
                    variant="destructive"
                    onClick={() => handleDeleteClick(selectedResponse)}
                  >
                    Delete
                  </Button>
                )}
                {(hasPermission(currentUserRole, "canUpdateTables") ||
                  hasPermission(currentUserRole, "canUpdateRecords")) && (
                  <Button
                    className="bg-primary hover:bg-primary/90"
                    onClick={() => {
                      setUpdateResponse(selectedResponse);
                      setSelectedResponse(null);
                    }}
                  >
                    <p className="text-white px-2.5">Edit</p>
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the following Response? This
              action cannot be undone.
              {responseToDelete && (
                <div className="mt-4 p-4 bg-muted rounded-md">
                  <p className="font-semibold">
                    Response ID: {responseToDelete.response_id}
                  </p>
                  <p className="text-sm mt-2 line-clamp-3">
                    {responseToDelete.response_text}
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

      <ResponseUpdateDialog
        response={updateResponse}
        open={!!updateResponse}
        onOpenChange={(open) => !open && setUpdateResponse(null)}
        onUpdateSuccess={handleUpdateSuccess}
      />

      <ResponseAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={handleUpdateSuccess}
      />
    </div>
  );
};

export default Responses;
