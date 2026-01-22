import { useState, useEffect } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { set } from "date-fns";
import test from "node:test";


interface TestCase {
  id: number;
  name: string;
  strategyName: string;
  // domainName: string;
  userPrompts: string;
  systemPrompts: string;
  responseText: string;
  llmPrompt: string;
  metricName: string;  // For backward compatibility
  metricNameList?: string[];  // List of metric names
}

interface TestCaseUpdateDialogProps {
  testCase: TestCase | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateSuccess?: () => void; // Callback to refresh test cases list
}

interface Strategy {
  strategy_id: number | null;
  strategy_name: string | null;
  requires_llm_prompt: boolean | null;
}

interface Metric {
  metric_id: number | null;
  metric_name: string | null;
}

// const domains = ["General", "Education", "agriculture", "Healthcare", "Learning Disability"];

export const TestCaseUpdateDialog = ({
  testCase,
  open,
  onOpenChange,
  onUpdateSuccess,
}: TestCaseUpdateDialogProps) => {
  const { toast } = useToast();
  const [userPrompts, setUserPrompts] = useState(testCase?.userPrompts);
  const [systemPrompts, setSystemPrompts] = useState(testCase?.systemPrompts || "");
  const [responseText, setResponseText] = useState(testCase?.responseText || "");
  const [llmPrompt, setLlmPrompt] = useState(testCase?.llmPrompt || "");
  const [strategy, setStrategy] = useState(testCase?.strategyName || "");
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  // const [domain, setDomain] = useState(testCase?.domainName || "");
  const [notes, setNotes] = useState("");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingStrategies, setIsFetchingStrategies] = useState(false);
  const [isFetchingMetrics, setIsFetchingMetrics] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const [focusedField, setFocusedField] = useState<null | "userPrompt" | "systemPrompt" | "response" | "llm">(null);

  const [errors, setErrors] = useState({
    userPrompts: false,
    systemPrompts: false,
    responseText: false,
    llmPrompt: false,
  });

  // function getTextareaHeight(lineCount: number){
  //   if (lineCount <=1) return 40;
  //   if (lineCount <=4) return lineCount * 40;
  //   return 160
  // }
  // const SmartTextarea = ({ value, ...props}) => {
  //   const lineCount = value.split("\n").length;
  //   const height = getTextareaHeight(lineCount);
  // }

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    switch (selection.type) {
      case "userPrompt":
        setUserPrompts(selection.userPrompt);
        if (errors.userPrompts && selection.userPrompt?.trim()) {
          setErrors(prev => ({ ...prev, userPrompts: false }));
        }
        // if (selection.systemPrompt !== undefined) {
        //   setSystemPrompts(selection.systemPrompt ?? "");
        // }
        break;
      case "systemPrompt":
        setSystemPrompts(selection.systemPrompt);
        if (errors.systemPrompts && selection.systemPrompt?.trim()) {
          setErrors(prev => ({ ...prev, systemPrompts: false }));
        }
        // if (selection.userPrompt) {
        //   setUserPrompts(selection.userPrompt);
        // }
        break;
      case "response":
        setResponseText(selection.responseText);
        if (errors.responseText && selection.responseText?.trim()) {
          setErrors(prev => ({ ...prev, responseText: false }));
        }
        break;
      case "llm":
        setLlmPrompt(selection.llmPrompt);
        if (errors.llmPrompt && selection.llmPrompt?.trim() && selection.llmPrompt !== "None") {
          setErrors(prev => ({ ...prev, llmPrompt: false }));
        }
        break;
      default:
        break;
    }
    setFocusedField(null);
    setSearchDialogOpen(false);
  };

  // Fetch current user role and strategies from API
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

    const fetchStrategies = async () => {
      setIsFetchingStrategies(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.STRATEGIES_V2, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (Array.isArray(data)) {
          setStrategies(data);
        } else {
          console.error("Unexpected strategies data format:", data);
          toast({
            title: "Error",
            description: "Failed to load strategies",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error fetching strategies:", error);
        toast({
          title: "Error",
          description: "Failed to load strategies from server",
          variant: "destructive",
        });
      } finally {
        setIsFetchingStrategies(false);
      }
    };

  // fetch metric from api
    const fetchMetrics = async () => {
      setIsFetchingMetrics(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };
        
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.METRICS_V2, { headers });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (Array.isArray(data)) {
          setMetrics(data);
          console.log("Fetched metrics:", data); // Debug log
        } else {
          console.error("Unexpected metrics data format:", data);
          toast({
            title: "Error",
            description: "Failed to load metrics: Invalid data format",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error fetching metrics:", error);
        toast({
          title: "Error",
          description: "Failed to load metrics from server",
          variant: "destructive",
        });
      } finally {
        setIsFetchingMetrics(false);
      }
    };

    if (open) {
      fetchUserRole();
      fetchStrategies();
      fetchMetrics();
    } else {
      // Reset errors when dialog closes
      setErrors({
        userPrompts: false,
        systemPrompts: false,
        responseText: false,
        llmPrompt: false,
      });
    }
  }, [open, toast]);

  useEffect(() => {
    setUserPrompts(testCase?.userPrompts || '');
    setSystemPrompts(testCase?.systemPrompts || '');
    setResponseText(testCase?.responseText || '');
    setLlmPrompt(testCase?.llmPrompt || '');
    setStrategy(testCase?.strategyName || '');
    // Initialize selectedMetrics from metricNameList or parse from metricName
    if (testCase?.metricNameList && testCase.metricNameList.length > 0) {
      setSelectedMetrics(testCase.metricNameList);
    } else if (testCase?.metricName) {
      setSelectedMetrics(testCase.metricName.split(", ").filter(Boolean));
    } else {
      setSelectedMetrics([]);
    }
    // setDomain(testCase?.domainName || '');
    setNotes(''); // Or testCase?.notes if available
    // Reset errors when test case changes
    setErrors({
      userPrompts: false,
      systemPrompts: false,
      responseText: false,
      llmPrompt: false,
    });
  }, [testCase]);

  const testCaseInitial: TestCase = testCase || {
    id: 0,
    name: "",
    strategyName: "",
    // domainName: "",
    userPrompts: "",
    systemPrompts: "",
    responseText: "",
    llmPrompt: "",
    metricName: "",
    metricNameList: [],
  };
  
  const initialMetrics = testCaseInitial.metricNameList && testCaseInitial.metricNameList.length > 0
    ? testCaseInitial.metricNameList
    : (testCaseInitial.metricName ? testCaseInitial.metricName.split(", ").filter(Boolean) : []);
  
  const isChanged = (
    userPrompts !== (testCaseInitial.userPrompts || "") ||
    systemPrompts.trim() !== (testCaseInitial.systemPrompts || "") ||
    responseText.trim() !== (testCaseInitial.responseText || "") ||
    llmPrompt.trim() !== (testCaseInitial.llmPrompt || "") ||
    strategy.trim() !== (testCaseInitial.strategyName || "") ||
    JSON.stringify(selectedMetrics.sort()) !== JSON.stringify(initialMetrics.sort())

    // notes !== ""
  );

  const handleMetricToggle = (metricName: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metricName) ? prev.filter((m) => m !== metricName) : [...prev, metricName]
    );
  };

  // const notNull = (
  //   userPrompts !== "" ||
  //   systemPrompts !== "" ||
  //   responseText !== "" ||
  //   llmPrompt !== "" ||
  //   strategy !== "" ||
  //   notes !== ""
  // );

  // Check if the selected strategy requires LLM prompt or if test case already has one
  // For update dialog, show LLM prompt field if:
  // 1. Selected strategy requires it, OR
  // 2. Test case has existing LLM prompt value (so user can view/edit/clear it)
  const selectedStrategyRequiresLLM = strategy && strategies.some(
    (s) => s.strategy_name === strategy && s.requires_llm_prompt === true
  );
  const hasExistingLLMPrompt = testCaseInitial.llmPrompt && testCaseInitial.llmPrompt.trim() !== "";
  const showLLMPrompt = selectedStrategyRequiresLLM || hasExistingLLMPrompt;



  const handleSubmit = async () => {
    // Check if user has permission to update
    if (!hasPermission(currentUserRole, "canUpdateTables") && 
        !hasPermission(currentUserRole, "canUpdateRecords")) {
      toast({
        title: "Access Denied",
        description: "You don't have permission to update test cases",
        variant: "destructive",
      });
      return;
    }

    if (!testCase?.id) {
      toast({
        title: "Error",
        description: "Test case ID is missing",
        variant: "destructive",
      });
      return;
    }

    // Validate required fields
    let hasErrors = false;
    const newErrors = {
      userPrompts: false,
      systemPrompts: false,
      responseText: false,
      llmPrompt: false,
    };

    if (!userPrompts || !userPrompts.trim()) {
      toast({
        title: "Validation Error",
        description: "User prompt is required",
        variant: "destructive",
      });
      newErrors.userPrompts = true;
      hasErrors = true;
    }

    if (!systemPrompts || !systemPrompts.trim()) {
      toast({
        title: "Validation Error",
        description: "System prompt is required",
        variant: "destructive",
      });
      newErrors.systemPrompts = true;
      hasErrors = true;
    }

    if (!responseText || !responseText.trim()) {
      toast({
        title: "Validation Error",
        description: "Response text is required",
        variant: "destructive",
      });
      newErrors.responseText = true;
      hasErrors = true;
    }

    if (selectedStrategyRequiresLLM && (!llmPrompt || llmPrompt === "None" || llmPrompt.trim() === "")) {
      toast({
        title: "Validation Error",
        description: "LLM prompt is required",
        variant: "destructive",
      });
      newErrors.llmPrompt = true;
      hasErrors = true;
    }

    if (hasErrors) {
      setErrors(newErrors);
      return;
    }

    // if (!testCase?.llmPrompt || llmPrompt === "none") {
    //   toast({
    //     title: "Error",
    //     description: "LLM prompt cannot be 'none'",
    //     variant: "destructive",
    //   });
    //   return;
    // }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // Prepare update payload - only include fields that have changed
      const updatePayload: any = {};
      
      if (userPrompts !== testCaseInitial.userPrompts) {
        updatePayload.user_prompt = userPrompts;
      }
      if (systemPrompts !== (testCaseInitial.systemPrompts || "")) {
        updatePayload.system_prompt = systemPrompts;
      }
      if (responseText !== (testCaseInitial.responseText || "")) {
        updatePayload.response_text = responseText;
      }
      // if (llmPrompt !== (testCaseInitial.llmPrompt || "")) {
      //   updatePayload.llm_judge_prompt = llmPrompt;
      // }
      
      // Handle LLM judge prompt based on strategy requirements
      const currentStrategyRequiresLLM = selectedStrategyRequiresLLM;
      const hasLLMPromptChanged = llmPrompt !== (testCaseInitial.llmPrompt || "");
      const strategyChanged = strategy !== (testCaseInitial.strategyName || "");
      
      // If strategy doesn't require LLM prompt, always send null to clear judge_prompt
      if (!currentStrategyRequiresLLM) {
        // Strategy doesn't require LLM prompt - always send null
        // This ensures judge_prompt is set to null when requires_llm_prompt is false
        updatePayload.llm_judge_prompt = null;
      } else if (hasLLMPromptChanged || strategyChanged) {
        // Strategy requires LLM prompt and something changed
        if (llmPrompt && llmPrompt.trim() !== "") {  // && llmPrompt !== "none"
          updatePayload.llm_judge_prompt = llmPrompt;
        } else {
          // If strategy requires LLM but prompt is empty/none, send null to clear it
          updatePayload.llm_judge_prompt = null;
        }
      }
      
      if (strategy !== (testCaseInitial.strategyName || "")) {
        updatePayload.strategy_name = strategy;
      }
      
      // Handle metrics - check if changed
      const currentMetrics = selectedMetrics.sort();
      const initialMetricsSorted = initialMetrics.sort();
      if (JSON.stringify(currentMetrics) !== JSON.stringify(initialMetricsSorted)) {
        updatePayload.metric_name_list = selectedMetrics;
      }

      // Always include notes if provided
      if (notes && notes.trim()) {
        updatePayload.notes = notes.trim();
      }

      const response = await fetch(
        //API_ENDPOINTS.TEST_CASES_UPDATE_BY_ID(testCase.id),
        API_ENDPOINTS.TESTCASE_UPDATE_V2(testCase.id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify(updatePayload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const updatedData = await response.json();
      console.log("Update successful:", updatedData);

      toast({
        title: "Success",
        description: "Test case updated successfully",
      });

      // Reset errors on successful update
      setErrors({
        userPrompts: false,
        systemPrompts: false,
        responseText: false,
        llmPrompt: false,
      });

      // Call the callback to refresh the test cases list
      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      onOpenChange(false);
    } catch (error) {
      console.error("Error updating test case:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to update test case",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!testCase) return null;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus = {(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">Update Test Case</DialogTitle>
            
            {/* <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-4"
              onClick={() => onOpenChange(false)}
            >
              <X className="w-5 h-5" />
            </Button> */}
          </DialogHeader>

          <div className = "overflow-y-auto flex-1 pr-1 pl-1">

            <div className=" pb-4 flex flex-row align-center justify-center">
              <Label className="text-base font-semibold">Test Case -</Label>
              <Label className="text-base font-semibold text-xl pl-2 text-primary hover:text-primary/90">{testCase.name}</Label>
              {/* <Input
                value={testCase.name}
                readOnly
                className="bg-muted"
              /> */}
            </div>

            <div className="space-y-1 pb-1">
              {/* <Label className="text-base font-semibold">Prompt</Label> */}
              <div className="space-y-1 pb-4">
                <Label className="text-base font-semibold">User Prompts</Label>
                <div className="relative">
                  <Textarea
                    value={userPrompts}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "75px",
                      overflowY: "auto"
                    }}
                    onFocus={() => setFocusedField("userPrompt")}
                    onBlur={() => setFocusedField(null)}
                    onChange={(e) => {
                      setUserPrompts(e.target.value);
                      if (errors.userPrompts && e.target.value.trim()) {
                        setErrors(prev => ({ ...prev, userPrompts: false }));
                      }
                    }}
                    className={`bg-muted min-h-[73px] pr-10 ${
                      errors.userPrompts ? 'border-red-500 ring-2 ring-red-200' : ''
                    }`}
                  />
                  { focusedField === "userPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleSearchClick("userPrompt")}
                      tabIndex = {-1}
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>

              </div>

              <div className="space-y-1 pb-4">
                <Label className="text-base font-semibold">System prompts</Label>
                <div className="relative">
                  <Textarea
                    value={systemPrompts}
                    style = {{
                        height: '${height}px',
                        maxHeight: "120px",
                        minHeight: "75px",
                        overflowY: "auto"
                    }}
                    onChange={(e) => {
                      setSystemPrompts(e.target.value);
                      if (errors.systemPrompts && e.target.value.trim()) {
                        setErrors(prev => ({ ...prev, systemPrompts: false }));
                      }
                    }}
                    className={`bg-muted min-h-[73px] pr-10 ${
                      errors.systemPrompts ? 'border-red-500 ring-2 ring-red-200' : ''
                    }`}
                    onFocus={() => setFocusedField("systemPrompt")}
                    onBlur={() => setFocusedField(null)}
                    // tabIndex = {-1}
                    // onClick = {() => setFocusedField("systemPrompt")}
                  />
                  { focusedField === "systemPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleSearchClick("systemPrompt")}
                      
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-1 pb-4">
              <Label className="text-base font-semibold">Response</Label>
              <div className="relative">
                <Textarea
                  value={responseText}
                  style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "75px",
                      overflowY: "auto"
                  }}
                  // readOnly = {responseText === "None"}
                  onFocus = { () => setFocusedField("response")}
                  onBlur={() => setFocusedField(null)}
                  onChange={(e) => {
                    setResponseText(e.target.value);
                    if (errors.responseText && e.target.value.trim()) {
                      setErrors(prev => ({ ...prev, responseText: false }));
                    }
                  }}
                  className={`bg-muted min-h-[73px] pr-10 ${
                    errors.responseText ? 'border-red-500 ring-2 ring-red-200' : ''
                  }`}
                  tabIndex = {-1}
                />
                { focusedField === "response" && (
                  
                
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2"
                  onMouseDown={e => e.preventDefault()}
                  onClick={() => handleSearchClick("response")}
                >
                  <Search className="w-4 h-4" />
                </Button>
                )}
              </div>
            </div>

            <div className="space-y-1 pb-4">
              <Label className="text-base font-semibold">Strategy</Label>
              <Select value={strategy} onValueChange={setStrategy} disabled={isFetchingStrategies}>
                <SelectTrigger className="bg-muted">
                  <SelectValue placeholder={isFetchingStrategies ? "Loading strategies..." : "Select strategy"} />
                </SelectTrigger>
                <SelectContent className="bg-popover max-h-[300px]">
                  {strategies.length === 0 && !isFetchingStrategies ? (
                    <SelectItem value="" disabled>No strategies available</SelectItem>
                  ) : (
                    strategies
                      .filter((s) => s.strategy_name != null)
                      .map((s) => (
                        <SelectItem key={s.strategy_name} value={s.strategy_name!}>
                          {s.strategy_name}
                        </SelectItem>
                      ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {selectedStrategyRequiresLLM ? (
              <div className="space-y-1 pb-4">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <div className="relative">
                  <Textarea
                    value={llmPrompt}
                    style = {{
                        height: '${height}px',
                        maxHeight: "120px",
                        minHeight: "75px",
                        overflowY: "auto"
                    }}
                    placeholder="Enter prompt or Search"
                    onFocus={() => setFocusedField("llm")}
                    onBlur = {() => setTimeout(() => setFocusedField(null), 100)}
                    onChange={(e) => {
                      setLlmPrompt(e.target.value);
                      if (errors.llmPrompt && e.target.value.trim() && e.target.value !== "None") {
                        setErrors(prev => ({ ...prev, llmPrompt: false }));
                      }
                    }}
                    className={`bg-muted min-h-[73px] pr-10 ${
                      errors.llmPrompt ? 'border-red-500 ring-2 ring-red-200' : ''
                    }`}
                    // readOnly = {llmPrompt === "None" || llmPrompt === ""}
                  />
                  { focusedField === "llm" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleSearchClick("llm")}
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ):(
                <div className="space-y-1 pb-4 hidden">
                  <Label className="text-base font-semibold">LLM Prompt</Label>
                  <Textarea
                    value=""
                    readOnly
                    className="bg-muted min-h-[40px]"
                    style={{
                      height: "20px",
                      maxHeight: "20px"
                    }}
                  />
                </div>
            )
            }
            
            

            <div className="space-y-2 pb-4">
              <Label className="text-base font-semibold">Metrics</Label>
              <div className="bg-muted p-4 rounded-md max-h-[150px] overflow-y-auto">
                {isFetchingMetrics ? (
                  <div className="text-sm text-muted-foreground">
                    Loading metrics...
                  </div>
                ) : metrics.filter((m) => m.metric_name != null).length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    No metrics available
                  </div>
                ) : (
                  <div className="space-y-2">
                    {metrics
                      .filter((m) => m.metric_name != null)
                      .map((m) => (
                        <div key={m.metric_name} className="flex items-center space-x-2">
                          <Checkbox
                            id={`metric-update-${m.metric_name}`}
                            checked={selectedMetrics.includes(m.metric_name!)}
                            onCheckedChange={() => handleMetricToggle(m.metric_name!)}
                          />
                          <label
                            htmlFor={`metric-update-${m.metric_name}`}
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                          >
                            {m.metric_name}
                          </label>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>



            {/* <div className="space-y-2">
              <Label className="text-base font-semibold">Domain</Label>
              <Select value={domain} onValueChange={setDomain}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  {domains.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div> */}

           

            </div>

            <div className="flex justify-center items-center p-2 border-gray-300 bg-white sticky bottom-0 z-10">
              <label className="text-base font-bold mr-2">
                Notes 
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
                disabled={!hasPermission(currentUserRole, "canUpdateTables") && 
                         !hasPermission(currentUserRole, "canUpdateRecords")}
              />
              <button
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleSubmit}
                disabled={
                  !isChanged || 
                  !notes.trim() || 
                  isLoading ||
                  selectedMetrics.length === 0 ||
                  (!hasPermission(currentUserRole, "canUpdateTables") && 
                   !hasPermission(currentUserRole, "canUpdateRecords"))
                }
              >
                {isLoading ? "Updating..." : "Submit"}
              </button>
            </div>

          
          
        </DialogContent>
      </Dialog>

      <PromptSearchDialog
        open={searchDialogOpen}
        onOpenChange={setSearchDialogOpen}
        onSelect={handleSelectPrompt}
        searchType={searchType}
      />
    </>
  );
};
