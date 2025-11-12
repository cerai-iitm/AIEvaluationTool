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
import { Search, X, Check, AlertCircle } from "lucide-react";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";

interface TestCaseAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const strategies = [
  "robustness_advglue_mnli",
  "robustness_advins",
  "safety_strategy",
  "String Matching - Wrong - Not implemented",
  "language_detect_langdetect",
  "tat_inm_mvh",
  "toxicity",
  "truthfulness_external",
  "truthfulness_internal_squad",
  "uptime_calculation",
  "compute_error_rate",
  "compute_mtbf",
  "detect_toxicity_using_perspective_api",
  "efficacy_of_content_filtering",
  "fairness_preference_force",
  "fairness_stereotype_query",
  "fairness_stereotype_recognition",
  "fluency_score",
  "grammatical_strategies",
  "hallucination_haluqa",
  "indian_lana_grammatical_check",
];

// Strategies that show LLM Prompt field
const strategiesWithLLMPrompt = [
  "fairness_stereotype_recognition",
  "fairness_stereotype_query",
  "toxicity",
  "truthfulness_external",
];

export const TestCaseAddDialog = ({
  open,
  onOpenChange,
  onSuccess,
}: TestCaseAddDialogProps) => {
  const { toast } = useToast();
  const [testCaseName, setTestCaseName] = useState("");
  const [isNameAvailable, setIsNameAvailable] = useState<boolean | null>(null);
  const [isCheckingName, setIsCheckingName] = useState(false);
  const [userPrompts, setUserPrompts] = useState("");
  const [systemPrompts, setSystemPrompts] = useState("");
  const [responseText, setResponseText] = useState("");
  const [llmPrompt, setLlmPrompt] = useState("");
  const [strategy, setStrategy] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");

  // Check test case name availability against database
  useEffect(() => {
    const checkNameAvailability = async () => {
      const name = testCaseName.trim();
      if (!name) {
        setIsNameAvailable(null);
        return;
      }

      setIsCheckingName(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.TEST_CASES, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const testCases = Array.isArray(data) ? data : [];
        
        // Check if any test case has the same name (case-insensitive)
        const nameExists = testCases.some(
          (tc: any) => 
            tc.testcase_name && 
            tc.testcase_name.toLowerCase().trim() === name.toLowerCase().trim()
        );

        setIsNameAvailable(!nameExists);
      } catch (error) {
        console.error("Error checking name availability:", error);
        setIsNameAvailable(null); // Set to null on error to not show incorrect status
      } finally {
        setIsCheckingName(false);
      }
    };

    // Debounce the check
    const timeout = setTimeout(() => {
      checkNameAvailability();
    }, 500);

    return () => clearTimeout(timeout);
  }, [testCaseName]);

  // const handleSearchClick = (type: "userPrompt" | "response" | "llm") => {
  //   setSearchType(type);
  //   setSearchDialogOpen(true);
  // };

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    switch (selection.type) {
      case "userPrompt":
        setUserPrompts(selection.userPrompt);
        setSystemPrompts(selection.systemPrompt ?? "");
        break;
      case "systemPrompt":
        setSystemPrompts(selection.systemPrompt);
        if (selection.userPrompt) {
          setUserPrompts(selection.userPrompt);
        }
        break;
      case "response":
        setResponseText(selection.responseText);
        break;
      case "llm":
        setLlmPrompt(selection.llmPrompt);
        break;
      default:
        break;
    }
    setSearchDialogOpen(false);
    setFocusedField(null);
  };

  const [focusedField, setFocusedField] = useState<null | "userPrompt" | "response" | "llm">(null);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
    if (type === "userPrompt" || type === "response" || type === "llm") {
      setFocusedField(type);
    } else {
      setFocusedField(null);
    }
  };

  const showLLMPrompt = strategy && strategiesWithLLMPrompt.includes(strategy);

  const handleSubmit = async () => {
    // Validate required fields
    if (!testCaseName.trim()) {
      toast({
        title: "Validation Error",
        description: "Test case name is required",
        variant: "destructive",
      });
      return;
    }

    if (!userPrompts.trim()) {
      toast({
        title: "Validation Error",
        description: "User prompt is required",
        variant: "destructive",
      });
      return;
    }

    if (!responseText.trim()) {
      toast({
        title: "Validation Error",
        description: "Response text is required",
        variant: "destructive",
      });
      return;
    }

    if (!strategy) {
      toast({
        title: "Validation Error",
        description: "Strategy is required",
        variant: "destructive",
      });
      return;
    }

    // Check if name is available
    if (isNameAvailable === false) {
      toast({
        title: "Validation Error",
        description: "Test case name already exists. Please choose a different name.",
        variant: "destructive",
      });
      return;
    }

    if (isCheckingName) {
      toast({
        title: "Please wait",
        description: "Checking name availability...",
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
        testcase_name: testCaseName.trim(),
        strategy_name: strategy,
        user_prompt: userPrompts.trim(),
        system_prompt: systemPrompts.trim() || null,
        response_text: responseText.trim() || null,
        llm_judge_prompt: showLLMPrompt && llmPrompt.trim() ? llmPrompt.trim() : null,
      };

      console.log("Creating test case:", payload);

      const response = await fetch(API_ENDPOINTS.TEST_CASE_CREATE, {
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
      console.log("Test case created successfully:", data);

      toast({
        title: "Success",
        description: `Test case "${testCaseName}" created successfully`,
      });

      // Reset form
      setTestCaseName("");
      setUserPrompts("");
      setSystemPrompts("");
      setResponseText("");
      setLlmPrompt("");
      setStrategy("");
      setNotes("");
      setIsNameAvailable(null);

      // Close dialog
      onOpenChange(false);

      // Trigger refresh in parent component
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error("Error creating test case:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create test case",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Add Test Case</DialogTitle>
            {/* <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-4"
              onClick={() => onOpenChange(false)}
            >
              <X className="w-5 h-5" />
            </Button> */}
          </DialogHeader>

          <div className="space-y-4 pt-4">
            <div className="space-y-1">
              <Label className="text-base font-semibold">Test Case</Label>
              <div className="relative">
                <Input
                  placeholder="Enter New Test Case Name"
                  value={testCaseName}
                  onChange={(e) => setTestCaseName(e.target.value)}
                  className={`bg-muted pr-24 ${
                    isNameAvailable === false ? "border-destructive" : ""
                  }`}
                  required
                  disabled={isSubmitting}
                />
                {isCheckingName && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-muted-foreground">
                    <span className="text-sm">Checking...</span>
                  </div>
                )}
                {!isCheckingName && isNameAvailable === true && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-green-600">
                    <Check className="w-4 h-4" />
                    <span className="text-sm font-medium">Available</span>
                  </div>
                )}
                {!isCheckingName && isNameAvailable === false && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-destructive">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">Taken</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2 pb-4">
              {/* <div className="flex items-center justify-between"> */}
                <Label className="text-base font-semibold">Prompt</Label>
              {/* </div> */}
              <div className="space-y-1">
                <Label className="text-sm font-semibold">User Prompts</Label>
                <div className="relative">
                <Textarea
                  value={userPrompts}
                  onChange={(e) => setUserPrompts(e.target.value)}
                  onFocus = {() => setFocusedField("userPrompt")}
                  onBlur = {() => setFocusedField(null)}
                  className="bg-muted min-h-[100px] pr-10"
                  required
                />
                { focusedField === "userPrompt" && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onMouseDown = {e => e.preventDefault()}
                    onClick={() => handleSearchClick("userPrompt")}
                    tabIndex = {-1} //not focusable, only clickable
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                )}
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-sm font-semibold">System prompts</Label>
                <Textarea
                  value={systemPrompts}
                  onChange={(e) => setSystemPrompts(e.target.value)}
                  className="bg-muted min-h-[80px]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Response</Label>
              <div className="relative">
                <Textarea
                  value={responseText}
                  readOnly
                  className="bg-muted min-h-[80px] pr-10"
                  required
                  onChange ={(e) => setResponseText(e.target.value)}
                  onFocus = {() => setFocusedField("response")}
                  onBlur = {() => setFocusedField(null)}
                />
                { focusedField === "response" && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2"
                  onMouseDown = {e => e.preventDefault()}
                  onClick={() => handleSearchClick("response")}
                  tabIndex = {-1}
                >
                  <Search className="w-4 h-4" />
                </Button>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Strategy</Label>
              <Select value={strategy} onValueChange={setStrategy}>
                <SelectTrigger>
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent className="bg-popover max-h-[300px]">
                  {strategies.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {showLLMPrompt && (
              <div className="space-y-2">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <div className="relative">
                  <Textarea
                    value={llmPrompt}
                    readOnly
                    className="bg-muted min-h-[80px] pr-10"
                    required
                    onFocus = {() => setFocusedField("llm")}
                    onBlur = {() => setFocusedField(null)}
                  />
                  { focusedField === "llm" && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onClick={() => handleSearchClick("llm")}
                    onMouseDown = {e => e.preventDefault()}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
              <Label className="text-base font-semibold mr-2">Notes</Label>
              <input
                placeholder="Enter Notes"
                type="text"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
              />
              <button
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleSubmit}
                disabled={isSubmitting || isCheckingName || isNameAvailable === false}
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </button>
            </div>
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
