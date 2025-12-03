import { useState, useEffect, useRef } from "react";
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
import { ChevronLeft, ChevronRight, X, Loader2 } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { TestCaseUpdateDialog } from "@/components/TestCaseUpdateDialog";
import { TestCaseAddDialog } from "@/components/TestCaseAddDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";

interface TestCase {
  id: number;
  name: string;
  strategyName: string;
  domainName: string;
  userPrompts: string;
  systemPrompts: string;
  responseText: string;
  llmPrompt: string;
}

const TestCases = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCase, setSelectedCase] = useState<TestCase | null>(null);
  const [updateCase, setUpdateCase] = useState<TestCase | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testCaseToDelete, setTestCaseToDelete] = useState<TestCase | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  
  // Refs for textareas to enable auto-scroll
  const userPromptsRef = useRef<HTMLTextAreaElement>(null);
  const systemPromptsRef = useRef<HTMLTextAreaElement>(null);
  const responseTextRef = useRef<HTMLTextAreaElement>(null);
  const llmPromptRef = useRef<HTMLTextAreaElement>(null);

  const fetchTestCases = async () => {
    setIsLoading(true);
    setTestCases([]); // Clear previous data while loading
    
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      // Add auth token if available
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      //const apiUrl = API_ENDPOINTS.TEST_CASES;
      const apiUrl = API_ENDPOINTS.TESTCASES_V2;
      console.log("Fetching test cases from:", apiUrl);
      console.log("Headers:", { ...headers, Authorization: token ? "Bearer ***" : "None" });
      
      const response = await fetch(apiUrl, { 
        method: "GET",
        headers,
      });
      
      console.log("Response status:", response.status);
      console.log("Response headers:", Object.fromEntries(response.headers.entries()));
      
      // Handle non-OK responses
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
          console.error("API Error Response (JSON):", errorData);
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
          console.error("API Error Response (Text):", errorText);
        }
        throw new Error(`${errorMessage} (Status: ${response.status})`);
      }
      
      // Parse JSON response
      let data;
      try {
        const text = await response.text();
        console.log("Raw response text:", text.substring(0, 500)); // Log first 500 chars
        data = text ? JSON.parse(text) : [];
      } catch (parseError) {
        console.error("JSON Parse Error:", parseError);
        throw new Error("Invalid JSON response from server");
      }
      
      console.log("Parsed API Response:", data);
      console.log("Is Array:", Array.isArray(data));
      console.log("Data type:", typeof data);
      console.log("Data length:", Array.isArray(data) ? data.length : "N/A");

      // Backend returns an array directly
      if (Array.isArray(data)) {
        // Handle empty array
        if (data.length === 0) {
          console.log("Received empty array from API");
          setTestCases([]);
          return;
        }
        
        // Map API response to frontend interface
        const mappedData: TestCase[] = data.map((item: any, index: number) => {
          console.log(`Mapping item ${index}:`, item);
          return {
            id: item.testcase_id ?? item.id ?? 0,
            name: item.testcase_name ?? "",
            strategyName: item.strategy_name ?? "",
            domainName: item.domain_name ?? item.domain ?? "",
            userPrompts: item.user_prompt ?? "",
            systemPrompts: item.system_prompt ?? "",
            responseText: item.response_text ?? "",
            llmPrompt: item.llm_judge_prompt ?? item.prompt ?? "",
          };
        });
        
        console.log("Mapped test cases:", mappedData);
        console.log("Total test cases mapped:", mappedData.length);
        setTestCases(mappedData);
      } else {
        // Fallback: check if it's wrapped in items (for backward compatibility)
        if (data && typeof data === 'object' && data.items && Array.isArray(data.items)) {
          const mappedData: TestCase[] = data.items.map((item: any) => ({
            id: item.testcase_id ?? item.id ?? 0,
            name: item.testcase_name ?? "",
            strategyName: item.strategy_name ?? "",
            domainName: item.domain_name ?? item.domain ?? "",
            userPrompts: item.user_prompt ?? "",
            systemPrompts: item.system_prompt ?? "",
            responseText: item.response_text ?? "",
            llmPrompt: item.llm_judge_prompt ?? item.prompt ?? "",
          }));
          setTestCases(mappedData);
        } else {
          console.error("Unexpected data format:", data);
          console.error("Data keys:", data && typeof data === 'object' ? Object.keys(data) : 'N/A');
          toast({
            title: "Error",
            description: `Invalid data format received from server. Expected array, got ${typeof data}`,
            variant: "destructive",
          });
          setTestCases([]);
        }
      }
    } catch (error) {
      console.error("Error fetching test cases:", error);
      const errorMessage = error instanceof Error 
        ? error.message 
        : "Failed to connect to server. Please check if the backend is running.";
      
      toast({
        title: "Failed to Load Test Cases",
        description: errorMessage,
        variant: "destructive",
      });
      setTestCases([]); // Set empty array on error to prevent showing stale data
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Fetch current user role
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
    fetchTestCases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const handleUpdateSuccess = () => {
    setRefreshKey((prev) => prev + 1); // Trigger refresh
  };

  const handleDeleteClick = (testCase: TestCase) => {
    setTestCaseToDelete(testCase);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!testCaseToDelete) return;

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
        //API_ENDPOINTS.TESTCASE_DELETE(testCaseToDelete.id),
        API_ENDPOINTS.TESTCASE_DELETE_V2(testCaseToDelete.id),
        {
          method: "DELETE",
          headers,
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      toast({
        title: "Success",
        description: "Test case deleted successfully",
      });

      setDeleteDialogOpen(false);
      setTestCaseToDelete(null);
      setSelectedCase(null);
      handleUpdateSuccess();
    } catch (error) {
      console.error("Error deleting test case:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to delete test case",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredCases = testCases.filter((tc) =>
    tc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.strategyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.domainName.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const totalItems = filteredCases.length;
  const itemsPerPage = 15;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  // Pagination logic: get items for current page
  const paginatedCases = filteredCases.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Calculate line count from text more accurately
  // Estimates based on typical textarea width (~700px) and average char width (~7px)
  // This gives us roughly 100 characters per line
  function getLineCount(text: string): number {
    if (!text || text.trim() === "") return 1;
    
    const lines = text.split('\n');
    let totalLines = 0;
    
    // Average characters per line for a textarea in a max-w-3xl dialog
    // Assuming ~700px width and ~7px per character = ~100 chars per line
    const charsPerLine = 100;
    
    lines.forEach(line => {
      if (line.length === 0) {
        // Empty line still counts as 1 line
        totalLines += 1;
      } else {
        // Calculate how many lines this line will wrap to
        const wrappedLines = Math.ceil(line.length / charsPerLine);
        totalLines += Math.max(1, wrappedLines);
      }
    });
    
    return Math.max(1, totalLines);
  }

  // Calculate height based on line count
  function getTextareaHeight(lineCount: number): number {
    if (lineCount <= 1) return 40; // minimum height for single line
    if (lineCount <= 3) return lineCount * 40; // 2 lines = 80px, 3 = 120px, 4 = 160px
    return 85; // max height with scroll for >4 lines
  }

  // Auto-scroll to line 3 if content has more than 3 lines
  useEffect(() => {
    if (!selectedCase) return;

    const scrollToLine3 = (ref: React.RefObject<HTMLTextAreaElement>, text: string) => {
      if (!ref.current) return;
      const lineCount = getLineCount(text);
      if (lineCount > 3) {
        // Scroll to show line 3: scroll past first 2 lines (2 * 40px = 80px)
        // This positions line 3 at the top of the visible area
        setTimeout(() => {
          if (ref.current) {
            ref.current.scrollTop = 80; // 2 lines * 40px per line
          }
        }, 100); // Small delay to ensure textarea is rendered
      }
    };
    if (selectedCase.userPrompts) {
      scrollToLine3(userPromptsRef, selectedCase.userPrompts);
    }
    if (selectedCase.systemPrompts) {
      scrollToLine3(systemPromptsRef, selectedCase.systemPrompts);
    }
    if (selectedCase.responseText) {
      scrollToLine3(responseTextRef, selectedCase.responseText);
    }
    if (selectedCase.llmPrompt) {
      scrollToLine3(llmPromptRef, selectedCase.llmPrompt);
    }
  
  }, [selectedCase]);

  return (
    <div className="flex min-h-screen">
          <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
            <Sidebar />
          </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Test Cases</h1>

          <div className="flex gap-4 mb-6 ">
            <Select defaultValue="testcase">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="testcase">Test Case Name</SelectItem>
                <SelectItem value="strategy">Strategy Name</SelectItem>
                <SelectItem value="domain">Domain Name</SelectItem>
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
                      totalItems
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
            {/* <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                1 - {itemsPerPage} of {totalItems}
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
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div> */}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="bg-white rounded-lg shadow overflow-hidden max-h-[70vh] overflow-y-auto">
            <table className="w-full table-fixed">
              <thead className="border-b-2">
                <tr>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Testcase ID</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Testcase Name</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Strategy Name</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold   text-left">Domain Name</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-muted-foreground">
                      Loading test cases...
                    </td>
                  </tr>
                ) : paginatedCases.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-muted-foreground">
                      No test cases found
                    </td>
                  </tr>
                ) : (
                  paginatedCases.map((testCase) => (
                    <tr
                      key={testCase.id}
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => setSelectedCase(testCase)}
                    >
                      <td className="p-2 pl-12">{testCase.id}</td>
                      <td className="p-2 pl-12">{testCase.name}</td>
                      <td className="p-2">{testCase.strategyName}</td>
                      <td className="p-2 pl-6 capitalize first-letter">{testCase.domainName}</td>
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
                + Add Test Case
              </Button>
            </div>
          )}
        </div>
      </main>

      <Dialog open={!!selectedCase} onOpenChange={() => setSelectedCase(null)}>
        <DialogContent 
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus = {(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">Test Case Details</DialogTitle>
            {/* <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-4"
              onClick={() => setSelectedCase(null)}
            >
              <X className="w-5 h-5" />
            </Button> */}
          </DialogHeader>

          {selectedCase && (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
            {/* <div className="space-y-4 pt-4"> */}
              <div className="space-y-1">
                <Label className="text-base font-semibold">Testcase Name</Label>
                <Input value={selectedCase.name} readOnly className="bg-muted" />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">User Prompts</Label>
                <Textarea
                  ref={userPromptsRef}
                  value={selectedCase.userPrompts}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.userPrompts))}px`,
                    maxHeight: "160px",
                    minHeight: "40px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">System prompts</Label>
                <Textarea
                  ref={systemPromptsRef}
                  value={selectedCase.systemPrompts}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.systemPrompts))}px`,
                    maxHeight: "160px",
                    minHeight: "40px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>

              { selectedCase.responseText && selectedCase.responseText.trim() !== "" && (
              <div className="space-y-1">
                <Label className="text-base font-semibold">Response Text</Label>
                <Textarea
                  ref={responseTextRef}
                  value={selectedCase.responseText}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.responseText))}px`,
                    maxHeight: "160px",
                    minHeight: "40px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>
              )}
              
              <div className="space-y-1">
                <Label className="text-base font-semibold">Strategy Name</Label>
                <Input value={selectedCase.strategyName} readOnly className="bg-muted" />
              </div>
              

              {/* Only show LLM Prompt if not empty */}
              {selectedCase.llmPrompt && selectedCase.llmPrompt.trim() !== "None" && (
              <div className="space-y-1">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <Textarea
                  ref={llmPromptRef}
                  value={selectedCase.llmPrompt}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.llmPrompt))}px`,
                    // maxHeight: "160px",
                    // minHeight: "40px",
                    // overflowY: "auto",
                  }}
                  className="bg-muted min-h-[80px]"
                />
              </div>
              )}

            </div>
          )}
          <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center gap-4 border-gray-200 z-10">
          {/* <div className="flex justify-center gap-4 pt-4"> */}
            {hasPermission(currentUserRole, "canDeleteTables") && (
              <Button 
                variant="destructive"
                onClick={() => handleDeleteClick(selectedCase)}
              >
                Delete
              </Button>
            )}
            {hasPermission(currentUserRole, "canUpdateTables") && (
              <Button 
                className="bg-primary hover:bg-primary/90"
                onClick={() => {
                  setUpdateCase(selectedCase);
                  setSelectedCase(null);
                }}
              >
                Update
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <TestCaseUpdateDialog
        testCase={updateCase}
        open={!!updateCase}
        onOpenChange={(open) => !open && setUpdateCase(null)}
        onUpdateSuccess={handleUpdateSuccess}
      />

      <TestCaseAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={handleUpdateSuccess}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the following testcase? This
              action cannot be undone.
              {testCaseToDelete && (
                <div className="mt-4 p-4 bg-muted rounded-md">
                  <p className="font-semibold">Test Case ID: {testCaseToDelete.id}</p>
                  <p className="font-semibold">Test Case Name: {testCaseToDelete.name}</p>
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

export default TestCases;
