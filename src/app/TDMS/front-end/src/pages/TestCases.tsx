import { type ChangeEvent, type DragEvent, useState, useEffect, useRef } from "react";
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
import { ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight, X, Loader2, Upload, CircleCheck, CircleX } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { TestCaseUpdateDialog } from "@/components/TestCaseUpdateDialog";
import { TestCaseAddDialog } from "@/components/TestCaseAddDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";
import { PageHeaderWithBack } from "@/components/PageHeaderWithBack";
import { getValidAccessToken } from "@/utils/auth";

interface TestCase {
  id: number;
  name: string;
  strategyName: string;
  domainName: string;
  userPrompts: string;
  systemPrompts: string;
  responseText: string;
  llmPrompt: string;
  language: string;
  metricName: string;  // For backward compatibility (comma-separated)
  metricNameList?: string[];  // List of metric names
}

const TestCases = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchField, setSearchField] = useState<"testcase" | "strategy" | "domain">("testcase");
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
  const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);
  const [importerDialogOpen, setImporterDialogOpen] = useState(false);
  const [importerLoading, setImporterLoading] = useState(false);
  const [importerStatus, setImporterStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [importerMessage, setImporterMessage] = useState("");
  const [selectedJsonFile, setSelectedJsonFile] = useState<File | null>(null);
  const [isJsonDragActive, setIsJsonDragActive] = useState(false);
  const importerFileInputRef = useRef<HTMLInputElement | null>(null);
  const importerRefreshTimerRef = useRef<number | null>(null);
  
  // Refs for textareas to enable auto-scroll
  const userPromptsRef = useRef<HTMLTextAreaElement>(null);
  const systemPromptsRef = useRef<HTMLTextAreaElement>(null);
  const responseTextRef = useRef<HTMLTextAreaElement>(null);
  const llmPromptRef = useRef<HTMLTextAreaElement>(null);

  const fetchTestCases = async () => {
    setIsLoading(true);
    setTestCases([]); // Clear previous data while loading
    
    // Helper function to map API response items to TestCase interface
    const mapItem = (item: any, index?: number): TestCase => {
      if (index !== undefined) {
        console.log(`Mapping item ${index}:`, item);
      }
      return {
        id: item.testcase_id ?? item.id ?? 0,
        name: item.testcase_name ?? "",
        strategyName: item.strategy_name ?? "",
        domainName: item.domain_name ?? item.domain ?? "",
        userPrompts: item.user_prompt ?? "",
        systemPrompts: item.system_prompt ?? "",
        responseText: item.response_text ?? "",
        llmPrompt: item.llm_judge_prompt ?? item.prompt ?? "",
        language: item.lang_name ?? item.lang ?? "",
        metricName: item.metric_name ?? item.metric?.name ?? item.metric ?? "",
        metricNameList: item.metric_name_list ?? (item.metric_name ? item.metric_name.split(", ").filter(Boolean) : []),
      };
    };

    // // Helper function to parse and map response data
    // const parseAndMapData = (data: any, source: string): TestCase[] => {
    //   console.log(`Parsed ${source} API Response:`, data);
    //   console.log(`Is Array:`, Array.isArray(data));
    //   console.log(`Data type:`, typeof data);
    //   console.log(`Data length:`, Array.isArray(data) ? data.length : "N/A");

    //   if (Array.isArray(data)) {
    //     if (data.length === 0) {
    //       console.log(`Received empty array from ${source} API`);
    //       return [];
    //     }
    //     return data.map((item: any, index: number) => mapItem(item, index));
    //   } else if (data && typeof data === 'object' && data.items && Array.isArray(data.items)) {
    //     // Fallback: check if it's wrapped in items (for backward compatibility)
    //     return data.items.map((item: any) => mapItem(item));
    //   } else {
    //     console.error(`Unexpected data format from ${source}:`, data);
    //     console.error("Data keys:", data && typeof data === 'object' ? Object.keys(data) : 'N/A');
    //     return [];
    //   }
    // };

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      // Add auth token if available
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // FIRST: Fetch first 45 test cases
      const apiUrl = `${API_ENDPOINTS.TESTCASES_V2}`;
      console.log("Fetching first test cases from:", apiUrl);
      console.log("Headers:", { ...headers, Authorization: token ? "Bearer ***" : "None" });
      
      const response = await fetch(apiUrl, { 
        method: "GET",
        headers,
      });
      
      console.log("Response status:", response.status);
      console.log("Response headers:", Object.fromEntries(response.headers.entries()));
      
      // Handle non-OK responses for first endpoint
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
      
      // Parse response
      let data;
      try {
        const text = await response.text();
        console.log("Raw first response text:", text.substring(0, 500)); // Log first 500 chars
        data = text ? JSON.parse(text) : [];
      } catch (parseError) {
        console.error("JSON Parse Error:", parseError);
        throw new Error("Invalid JSON response from server");
      }

      if (Array.isArray(data)){
        // Handle empty array
        if (data.length === 0 ) {
          console.log("|Received empty array from API");
          setTestCases([]);
          return;
        }
      

        // Map data
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
            language: item.lang_name ?? item.lang ?? "",
            metricName: item.metric_name ?? item.metric?.name ?? item.metric ?? "",
            metricNameList: item.metric_name_list ?? (item.metric_name ? item.metric_name.split(", ").filter(Boolean) : []),
          }
        })

      console.log("Mapped test cases:", mappedData);
      console.log("Total first test cases mapped:", mappedData.length);
      setTestCases(mappedData);
      }else {
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
            language: item.lang_name ?? item.lang ?? "",
            metricName: item.metric_name ?? item.metric?.name ?? item.metric ?? "",
            metricNameList: item.metric_name_list ?? (item.metric_name ? item.metric_name.split(", ").filter(Boolean) : []),
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
    // Preserve the highlighted row ID after update
    const currentHighlightedId = highlightedRowId;
    setRefreshKey((prev) => prev + 1); // Trigger refresh
    // Restore highlight after data refresh
    setTimeout(() => {
      if (currentHighlightedId !== null) {
        setHighlightedRowId(currentHighlightedId);
      }
    }, 100);
  };

  useEffect(() => {
    return () => {
      if (importerRefreshTimerRef.current !== null) {
        window.clearTimeout(importerRefreshTimerRef.current);
      }
    };
  }, []);

  const resetImporter = () => {
    setImporterStatus("idle");
    setImporterMessage("");
    setSelectedJsonFile(null);
    setIsJsonDragActive(false);

    if (importerFileInputRef.current) {
      importerFileInputRef.current.value = "";
    }
  };

  const pickJsonFile = (file?: File | null) => {
    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".json")) {
      setSelectedJsonFile(null);
      setImporterStatus("idle");
      setImporterMessage("Please select a .json file.");
      return;
    }

    setSelectedJsonFile(file);
    setImporterStatus("idle");
    setImporterMessage("");
  };

  const handleJsonFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    pickJsonFile(event.target.files?.[0]);
  };

  const handleJsonDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsJsonDragActive(true);
  };

  const handleJsonDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsJsonDragActive(false);
  };

  const handleJsonDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsJsonDragActive(false);
    pickJsonFile(event.dataTransfer.files?.[0]);
  };

  const formatUploadError = async (response: Response) => {
    try {
      const data = await response.json();
      const detail = data.detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (detail?.errors?.length) {
        const firstErrors = detail.errors
          .slice(0, 5)
          .map((error: { row?: number | null; field?: string; message?: string }) => {
            const row = error.row ? `Row ${error.row}` : "File";
            const field = error.field ? ` ${error.field}` : "";
            return `${row}${field}: ${error.message}`;
          })
          .join("\n");
        const remaining = detail.errors.length > 5 ? `\n...and ${detail.errors.length - 5} more error(s).` : "";
        return `${detail.message || "JSON upload validation failed."}\n${firstErrors}${remaining}`;
      }

      return detail?.message || data.message || "JSON upload failed.";
    } catch (error) {
      return "JSON upload failed.";
    }
  };

  const uploadJsonFile = async () => {
    if (!selectedJsonFile) {
      setImporterStatus("error");
      setImporterMessage("Select a JSON file before importing.");
      return;
    }

    setImporterLoading(true);
    setImporterStatus("loading");
    setImporterMessage("Uploading JSON test cases...");

    try {
      const token = await getValidAccessToken(API_ENDPOINTS.REFRESH);
      if (!token) {
        setImporterStatus("error");
        setImporterMessage("Authentication failed");
        setImporterLoading(false);
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedJsonFile);

      const response = await fetch(API_ENDPOINTS.TESTCASE_UPLOAD_JSON, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        setImporterStatus("error");
        setImporterMessage(await formatUploadError(response));
        setImporterLoading(false);
        return;
      }

      const data = await response.json();
      setImporterStatus("success");
      setImporterMessage(data.message || "JSON test cases imported successfully.");
      setImporterLoading(false);
      importerRefreshTimerRef.current = window.setTimeout(() => {
        setRefreshKey((prev) => prev + 1);
        setImporterDialogOpen(false);
        resetImporter();
      }, 1500);
    } catch (error) {
      setImporterStatus("error");
      setImporterMessage(`Error: ${error instanceof Error ? error.message : "An unexpected error occurred"}`);
      setImporterLoading(false);
    }
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
      setHighlightedRowId(null); // Clear highlight when row is deleted
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

  const filteredCases = testCases.filter((tc) =>{
    const q = searchQuery.toLowerCase();

    if (!q) return true;

    if (searchField === "testcase") {
      return tc.name.toLowerCase().includes(q);
    } else if (searchField === "strategy") {
      return tc.strategyName.toLowerCase().includes(q);
    } else if (searchField === "domain") {
      return tc.domainName.toLowerCase().includes(q);
    }
    return true;
  }
    // tc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    // tc.strategyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    // tc.domainName.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const totalItems = filteredCases.length;
  const itemsPerPage = 15;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

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

      <main className="flex-1 bg-background">
        <div className="p-8 flex flex-col h-screen">
          <PageHeaderWithBack title="Test Cases" />

          <div className="flex gap-4 mb-6 ">
            <Select defaultValue="testcase"
              onValueChange={(value: "testcase" | "strategy" | "domain") => setSearchField(value)}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="testcase">Testcase Name</SelectItem>
                <SelectItem value="strategy">Strategy Name</SelectItem>
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
            <div className="ml-auto flex items-center gap-4">
              <HistoryButton
                entityType="Test Case"
                title="Test Cases"
                idField="testCaseId"
                idLabel="Test Case ID"
              />
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
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  aria-label="Go to first page"
                >
                  <ChevronsLeft className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  aria-label="Go to previous page"
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
                  aria-label="Go to next page"
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  aria-label="Go to last page"
                >
                  <ChevronsRight className="w-5 h-5" />
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
          <div className="bg-white rounded-lg shadow overflow-hidden w-full overflow-y-auto overflow-x-auto">
            <table className="w-full table-fixed">
              <thead className="border-b-2">
                <tr>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[12%]">Testcase ID</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[12%]">Testcases</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[20%]">Metrics</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[12%]">Strategies</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[12%]">Domains</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left w-[12%]">Languages</th>
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
                  paginatedCases.map((testCase,index) => (
                    <tr
                      key={testCase.id}
                      className={`border-b cursor-pointer transition-colors duration-200 ${
                        highlightedRowId === testCase.id
                          ? "bg-primary/10 hover:bg-primary/15 border-primary/30"
                          : "hover:bg-muted/50"
                      }`}
                      onClick={() => {
                        setSelectedCase(testCase);
                        setHighlightedRowId(testCase.id);
                      }}
                    >
                      <td className="p-2 pl-12">{(currentPage - 1) * itemsPerPage + index + 1}</td>
                      <td className="p-2 pl-2 max-w-[200px] whitespace-normal break-words">{testCase.name}</td>
                      <td className="p-2 truncate">{testCase.metricName}</td>
                      <td className="p-2 truncate">{testCase.strategyName}</td>
                      <td className="p-2 pl-6 capitalize first-letter">{testCase.domainName}</td>
                      <td className="p-2 pl-6 capitalize first-letter">{testCase.language}</td>
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
                + Add Test Case
              </Button>
            </div>
          )}
        </div>
      </main>

      {/* <button
        onClick={() => {
          resetImporter();
          setImporterDialogOpen(true);
        }}
        disabled={importerLoading}
        className="fixed bottom-8 right-8 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2 z-30"
      >
        {importerLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Importing...</span>
          </>
        ) : (
          <>
            <Upload className="w-5 h-5" />
            <span>Import Data</span>
          </>
        )}
      </button> */}

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
              {/* <div className=" flex flex-row align-center justify-center">
                <Label className="text-base font-semibold pl-2">Test Case  - </Label> <Label className="text-base font-semibold text-xl pl-2 text-primary hover:text-primary/90"> {selectedCase.name} </Label>
                
              </div> */}
              <div className="flex items-center justify-center gap-2 flex-wrap text-center w-full">
                <Label className="text-base font-semibold whitespace-nowrap">
                  Test Case -
                </Label>

                 <Label className="text-xl font-semibold text-primary hover:text-primary/90 break-all min-w-0 max-w-full">
                  {selectedCase.name}
                </Label>
              </div>


              <div className="space-y-1">
                <Label className="text-base font-semibold">User Prompt</Label>
                <Textarea
                  ref={userPromptsRef}
                  value={selectedCase.userPrompts}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.userPrompts))}px`,
                    maxHeight: "120px",
                    minHeight: "70px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">System prompt</Label>
                <Textarea
                  ref={systemPromptsRef}
                  value={selectedCase.systemPrompts}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.systemPrompts))}px`,
                    maxHeight: "120px",
                    minHeight: "70px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>

              { selectedCase.responseText && selectedCase.responseText.trim() !== "" && (
              <div className="space-y-1">
                <Label className="text-base font-semibold">Response</Label>
                <Textarea
                  ref={responseTextRef}
                  value={selectedCase.responseText}
                  readOnly
                  style={{
                    height: '${height}px',
                    //height: `${getTextareaHeight(getLineCount(selectedCase.responseText))}px`,
                    maxHeight: "120px",
                    minHeight: "70px",
                    overflowY: "auto"
                  }}
                  className="bg-muted"
                />
              </div>
              )}
              
              <div className=" space-y-1 ">
                <Label className="text-base font-semibold basis-[25%] pt-1">Strategy</Label>
                {/* <Label className=" font-normal p-2 m-4 bg-muted"> {selectedCase.strategyName} </Label> */}
                <Input value={selectedCase.strategyName} readOnly className="bg-muted basis-[75%]" />
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
                    maxHeight: "120px",
                    minHeight: "70px",
                    overflowY: "auto",
                  }}
                  className="bg-muted min-h-[80px]"
                />
              </div>
              )}

              <div className="space-y-1">
                <Label className="text-base font-semibold basis-[25%] pt-1">Metric</Label>
                <Input 
                  value={selectedCase.metricNameList && selectedCase.metricNameList.length > 0 
                    ? selectedCase.metricNameList.join(", ") 
                    : selectedCase.metricName} 
                  readOnly 
                  className="bg-muted basis-[75%]" 
                />
              </div>

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
                <p className="text-white px-2.5">Edit</p>
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

      <Dialog open={importerDialogOpen} onOpenChange={setImporterDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {importerStatus === "loading" && "Importing Test Cases..."}
              {importerStatus === "success" && "Import Successful"}
              {importerStatus === "error" && "Import Failed"}
              {importerStatus === "idle" && "Import Test Cases"}
            </DialogTitle>
          </DialogHeader>

          <div className="py-6 text-center">
            {importerStatus === "loading" && (
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
                <p className="text-foreground font-medium">{importerMessage}</p>
              </div>
            )}

            {importerStatus === "success" && (
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <CircleCheck className="w-7 h-7 text-green-600" />
                </div>
                <p className="text-foreground font-medium">{importerMessage}</p>
              </div>
            )}

            {importerStatus === "error" && (
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <CircleX className="w-7 h-7 text-red-600" />
                </div>
                <p className="text-foreground font-medium whitespace-pre-line">{importerMessage}</p>
              </div>
            )}

            {importerStatus === "idle" && (
              <div
                className={`flex flex-col items-center gap-4 rounded-lg border-2 border-dashed px-6 py-8 transition-colors ${
                  isJsonDragActive ? "border-blue-600 bg-blue-50" : "border-gray-300 bg-white"
                }`}
                onDragOver={handleJsonDragOver}
                onDragLeave={handleJsonDragLeave}
                onDrop={handleJsonDrop}
              >
                <input
                  ref={importerFileInputRef}
                  type="file"
                  accept="application/json,.json"
                  className="hidden"
                  onChange={handleJsonFileChange}
                />
                <button
                  type="button"
                  onClick={() => importerFileInputRef.current?.click()}
                  className="rounded-full p-3 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2"
                  aria-label="Choose JSON file"
                >
                  <Upload className="w-12 h-12 text-blue-600" />
                </button>
                <div className="w-full space-y-1">
                  <p className="w-full text-foreground font-medium">
                    {selectedJsonFile ? selectedJsonFile.name.length > 40 ? `${selectedJsonFile.name.slice(0, 40)}...` : selectedJsonFile.name : "Click the upload icon or drop a JSON file here"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Missing fields will be reported before import. Existing test case names are skipped.
                  </p>
                  {importerMessage && (
                    <p className="text-sm text-red-600 whitespace-pre-line">{importerMessage}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {importerStatus === "idle" && (
            <div className="flex gap-4 justify-end pt-4">
              <button
                onClick={() => setImporterDialogOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={uploadJsonFile}
                disabled={importerLoading || !selectedJsonFile}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400"
              >
                Import
              </button>
            </div>
          )}

          {(importerStatus === "error" || importerStatus === "success") && (
            <div className="flex gap-4 justify-end pt-4">
              <button
                onClick={() => {
                  if (importerStatus === "success") {
                    setImporterDialogOpen(false);
                    resetImporter();
                    return;
                  }

                  setImporterStatus("idle");
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <Button
            variant="ghost"
            className="absolute top-2 right-2 w-4 h-6 flex items-center justify-center rounded-full bg-gray-200 hover:bg-gray-300 transition-colors"
            onClick={() => {
              setDeleteDialogOpen(false);
            }}
          >
            <X className="mr-2 h-4 w-4" />
          </Button>
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
          <AlertDialogFooter className="justify-center sm:justify-center">
            {/* <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel> */}
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
                "Confirm Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TestCases;
