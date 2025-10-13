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
import { PromptSearchDialog } from "./PromptSearchDialog";


interface TestCase {
  id: number;
  name: string;
  strategyName: string;
  // domainName: string;
  userPrompts: string;
  systemPrompts: string;
  responseText: string;
  llmPrompt: string;
}

interface TestCaseUpdateDialogProps {
  testCase: TestCase | null;
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
];

// const domains = ["General", "Education", "agriculture", "Healthcare", "Learning Disability"];

export const TestCaseUpdateDialog = ({
  testCase,
  open,
  onOpenChange,
}: TestCaseUpdateDialogProps) => {
  const [userPrompts, setUserPrompts] = useState(testCase?.userPrompts);
  const [systemPrompts, setSystemPrompts] = useState(testCase?.systemPrompts || "");
  const [responseText, setResponseText] = useState(testCase?.responseText || "");
  const [llmPrompt, setLlmPrompt] = useState(testCase?.llmPrompt || "");
  const [strategy, setStrategy] = useState(testCase?.strategyName || "");
  // const [domain, setDomain] = useState(testCase?.domainName || "");
  const [notes, setNotes] = useState("");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<"userPrompt" | "response" | "llm">("userPrompt");

  const handleSearchClick = (type: "userPrompt" | "response" | "llm") => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const [focusedField, setFocusedField] = useState<null | "userPrompt" | "response" | "llm">(null);


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

  useEffect(() => {
    setUserPrompts(testCase?.userPrompts || '');
    setSystemPrompts(testCase?.systemPrompts || '');
    setResponseText(testCase?.responseText || '');
    setLlmPrompt(testCase?.llmPrompt || '');
    setStrategy(testCase?.strategyName || '');
    // setDomain(testCase?.domainName || '');
    setNotes(''); // Or testCase?.notes if available
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
  };
  const isChanged = (
    userPrompts !== testCaseInitial.userPrompts ||
    systemPrompts !== (testCaseInitial.systemPrompts || "") ||
    responseText !== (testCaseInitial.responseText || "") ||
    llmPrompt !== (testCaseInitial.llmPrompt || "") ||
    strategy !== (testCaseInitial.strategyName || "") ||
    notes !== ""
  );



  const handleSubmit = () => {
    console.log("Submitting:", {
      userPrompts,
      systemPrompts,
      responseText,
      llmPrompt,
      strategy,
      // domain,
      notes,
    });
    onOpenChange(false);
  };

  if (!testCase) return null;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
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

          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label className="text-base font-semibold">Test Case</Label>
              <Input
                value={testCase.name}
                readOnly
                className="bg-muted"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Prompt</Label>
              <div className="space-y-2">
                <Label className="text-sm font-normal">User Prompts</Label>
                <div className="relative">
                  <Textarea
                    value={userPrompts}
                    onFocus={() => setFocusedField("userPrompt")}
                    onBlur={() => setTimeout(() => setFocusedField(null), 100)}
                    onChange={(e) => setUserPrompts(e.target.value)}
                    className="bg-muted min-h-[100px] pr-10"
                  />
                  { focusedField === "userPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleSearchClick("userPrompt")}
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>

              </div>

              <div className="space-y-2">
                <Label className="text-sm font-normal">System prompts</Label>
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
                  onFocus = { () => setFocusedField("response")}
                  onBlur={() => setTimeout(() => setFocusedField(null), 100)}
                  onChange={(e) => setResponseText(e.target.value)}
                  readOnly
                  className="bg-muted min-h-[80px] pr-10"
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

            <div className="space-y-2">
              <Label className="text-base font-semibold">Strategy</Label>
              <Select value={strategy} onValueChange={setStrategy}>
                <SelectTrigger>
                  <SelectValue />
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

            <div className="space-y-2">
              <Label className="text-base font-semibold">LLM Prompt</Label>
              <div className="relative">
                <Textarea
                  value={llmPrompt}
                  onFocus={() => setFocusedField("llm")}
                  onBlur = {() => setTimeout(() => setFocusedField(null), 100)}
                  onChange={(e) => setLlmPrompt(e.target.value)}
                  readOnly
                  className="bg-muted min-h-[80px] pr-10"
                />
                { focusedField === "llm" && (
                  
                
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2"
                  onClick={() => handleSearchClick("llm")}
                >
                  <Search className="w-4 h-4" />
                </Button>
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

            <div className="space-y-2">

            </div>

            <div className="flex justify-center items-center pt-4">
              <label className="text-base font-bold mr-2">
                Notes :
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
              />
              <button
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800"
                onClick={handleSubmit}
                disabled={!isChanged}
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
