import { useState } from "react";
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
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";

interface Response {
  id: number;
  name: string;
  responseText: string;
  responseType: string;
  language: string;
  userPrompts: string;
  systemPrompts: string;
  notes: string;
}

interface ResponseUpdateDialogProps {
  response: Response | null;
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

export const ResponseUpdateDialog = ({
  response,
  open,
  onOpenChange,
}: ResponseUpdateDialogProps) => {
  const [responseText, setResponseText] = useState(response?.responseText || "");
  const [responseType, setResponseType] = useState(response?.responseType || "");
  const [language, setLanguage] = useState(response?.language || "");
  const [userPrompts, setUserPrompts] = useState(response?.userPrompts || "");
  const [systemPrompts, setSystemPrompts] = useState(response?.systemPrompts || "");
  const [notes, setNotes] = useState(response?.notes || "");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

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
        // No-op for response dialog, but keeping for completeness.
        break;
      default:
        break;
    }
    setSearchDialogOpen(false);
  };

  const handleSubmit = () => {
    console.log("Updating response:", {
      id: response?.id,
      responseText,
      responseType,
      language,
      userPrompts,
      systemPrompts,
      notes,
    });
    onOpenChange(false);
  };

  if (!response) return null;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Update Response</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label className="text-base font-semibold">Response Text</Label>
              <div className="relative">
                <Textarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  className="min-h-[100px] pr-10"
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
                    <SelectValue />
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
                    <SelectValue />
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
                <div className="relative">
                  <Textarea
                    value={userPrompts}
                    onChange={(e) => setUserPrompts(e.target.value)}
                    className="min-h-[80px] pr-10"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onClick={() => handleSearchClick("userPrompt")}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-normal">System prompts</Label>
                <div className="relative">
                  <Textarea
                    value={systemPrompts}
                    onChange={(e) => setSystemPrompts(e.target.value)}
                    className="min-h-[80px] pr-10"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onClick={() => handleSearchClick("systemPrompt")}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
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
