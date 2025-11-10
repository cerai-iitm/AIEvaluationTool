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
import { Search, X, Check } from "lucide-react";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";

interface TestCaseAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
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
}: TestCaseAddDialogProps) => {
  const [testCaseName, setTestCaseName] = useState("");
  const [isNameAvailable, setIsNameAvailable] = useState<boolean | null>(null);
  const [userPrompts, setUserPrompts] = useState("");
  const [systemPrompts, setSystemPrompts] = useState("");
  const [responseText, setResponseText] = useState("");
  const [llmPrompt, setLlmPrompt] = useState("");
  const [strategy, setStrategy] = useState("");
  const [notes, setNotes] = useState("");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");

  // Check test case name availability
  useEffect(() => {
    if (testCaseName.trim()) {
      // Simulate availability check
      const timeout = setTimeout(() => {
        setIsNameAvailable(true);
      }, 300);
      return () => clearTimeout(timeout);
    } else {
      setIsNameAvailable(null);
    }
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

  const handleSubmit = () => {
    console.log("Adding test case:", {
      testCaseName,
      userPrompts,
      systemPrompts,
      responseText,
      llmPrompt,
      strategy,
      notes,
    });
    onOpenChange(false);
    // Reset form
    setTestCaseName("");
    setUserPrompts("");
    setSystemPrompts("");
    setResponseText("");
    setLlmPrompt("");
    setStrategy("");
    setNotes("");
  };

  const showLLMPrompt = strategy && strategiesWithLLMPrompt.includes(strategy);

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
                  className="bg-muted pr-24"
                  required
                />
                {isNameAvailable && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-accent">
                    <Check className="w-4 h-4" />
                    <span className="text-sm font-medium">Available</span>
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
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800"
                onClick={handleSubmit}
              >
                Submit
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
