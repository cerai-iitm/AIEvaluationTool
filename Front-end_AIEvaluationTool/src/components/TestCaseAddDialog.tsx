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
import { PromptSearchDialog } from "./PromptSearchDialog";

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
  const [searchType, setSearchType] = useState<"userPrompt" | "response" | "llm">("userPrompt");

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

  const handleSearchClick = (type: "userPrompt" | "response" | "llm") => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const handleSelectPrompt = (prompt: string) => {
    if (searchType === "userPrompt") {
      setUserPrompts(prompt);
      // Simulate backend call to update system prompts
      setSystemPrompts("You are an AI assistant that not only provides the answer but explains your reasoning in a clear manner.");
    } else if (searchType === "response") {
      setResponseText(prompt);
    } else if (searchType === "llm") {
      setLlmPrompt(prompt);
    }
    setSearchDialogOpen(false);
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
            <div className="space-y-2">
              <Label className="text-base font-semibold">Test Case</Label>
              <div className="relative">
                <Input
                  placeholder="Enter Test Case Name"
                  value={testCaseName}
                  onChange={(e) => setTestCaseName(e.target.value)}
                  className="pr-24"
                />
                {isNameAvailable && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-accent">
                    <Check className="w-4 h-4" />
                    <span className="text-sm font-medium">Available</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-base font-semibold">Prompt</Label>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleSearchClick("userPrompt")}
                >
                  <Search className="w-4 h-4" />
                </Button>
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-normal">User Prompts</Label>
                <Textarea
                  value={userPrompts}
                  onChange={(e) => setUserPrompts(e.target.value)}
                  className="min-h-[100px]"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-normal">System prompts</Label>
                <Textarea
                  value={systemPrompts}
                  onChange={(e) => setSystemPrompts(e.target.value)}
                  className="min-h-[80px]"
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
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2"
                  onClick={() => handleSearchClick("response")}
                >
                  <Search className="w-4 h-4" />
                </Button>
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
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onClick={() => handleSearchClick("llm")}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label className="text-base font-semibold">Notes</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="min-h-[60px]"
              />
            </div>

            <div className="flex justify-center pt-4">
              <Button
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
                onClick={handleSubmit}
              >
                Submit
              </Button>
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
