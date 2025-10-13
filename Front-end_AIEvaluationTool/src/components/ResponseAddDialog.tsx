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

interface ResponseAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const responseTypes = [
  "Ground Truth",
  "Model Response",
  "Reference Response",
  "Human Response",
];

const languages = [
  "English",
  "Hindi",
  "Tamil",
  "Gujarati",
  "Bengali",
  "Telugu",
  "Marathi",
  "Kannada",
  "Malayalam",
  "Punjabi",
  "Auto",
];

export const ResponseAddDialog = ({
  open,
  onOpenChange,
}: ResponseAddDialogProps) => {
  const [responseName, setResponseName] = useState("");
  const [isNameAvailable, setIsNameAvailable] = useState<boolean | null>(null);
  const [userPrompts, setUserPrompts] = useState("");
  const [systemPrompts, setSystemPrompts] = useState("");
  const [responseText, setResponseText] = useState("");
  const [responseType, setResponseType] = useState("");
  const [language, setLanguage] = useState("");
  const [notes, setNotes] = useState("");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<"userPrompt" | "response" | "systemPrompt">("userPrompt");

  // Check response name availability
  useEffect(() => {
    if (responseName.trim()) {
      // Simulate availability check
      const timeout = setTimeout(() => {
        setIsNameAvailable(true);
      }, 300);
      return () => clearTimeout(timeout);
    } else {
      setIsNameAvailable(null);
    }
  }, [responseName]);

  const handleSearchClick = (type: "userPrompt" | "response" | "systemPrompt") => {
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
    } else if (searchType === "systemPrompt") {
      setSystemPrompts(prompt);
    }
    setSearchDialogOpen(false);
  };

  const handleSubmit = () => {
    console.log("Adding response:", {
      responseName,
      userPrompts,
      systemPrompts,
      responseText,
      responseType,
      language,
      notes,
    });
    onOpenChange(false);
    // Reset form
    setResponseName("");
    setUserPrompts("");
    setSystemPrompts("");
    setResponseText("");
    setResponseType("");
    setLanguage("");
    setNotes("");
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Add Response</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label className="text-base font-semibold">Response Name</Label>
              <div className="relative">
                <Input
                  placeholder="Enter Response Name"
                  value={responseName}
                  onChange={(e) => setResponseName(e.target.value)}
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
              <Label className="text-base font-semibold">Response Text</Label>
              <div className="relative">
                <Textarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  className="min-h-[100px] pr-10"
                  placeholder="Enter the response text..."
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

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-base font-semibold">Response Type</Label>
                <Select value={responseType} onValueChange={setResponseType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select response type" />
                  </SelectTrigger>
                  <SelectContent className="bg-popover max-h-[300px]">
                    {responseTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">Language</Label>
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent className="bg-popover max-h-[300px]">
                    {languages.map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {lang}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-base font-semibold">Prompt Section</Label>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleSearchClick("userPrompt")}
                    title="Search User Prompts"
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleSearchClick("systemPrompt")}
                    title="Search System Prompts"
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-sm font-normal">User Prompts</Label>
                <Textarea
                  value={userPrompts}
                  onChange={(e) => setUserPrompts(e.target.value)}
                  className="min-h-[80px]"
                  placeholder="Enter user prompt..."
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-normal">System prompts</Label>
                <Textarea
                  value={systemPrompts}
                  onChange={(e) => setSystemPrompts(e.target.value)}
                  className="min-h-[80px]"
                  placeholder="Enter system prompt..."
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Enter notes..."
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
