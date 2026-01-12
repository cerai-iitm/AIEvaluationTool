import { useState, useEffect, useCallback } from "react";
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
import { Search } from "lucide-react";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";

interface ResponseAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const responseTypes = [
  { value: "GT", label: "Ground Truth" },
  { value: "GTDesc", label: "Ground Truth Description" },
  { value: "NA", label: "Not Applicable" },
];

export const ResponseAddDialog = ({
  open,
  onOpenChange,
  onSuccess,
}: ResponseAddDialogProps) => {
  const { toast } = useToast();
  const [userPrompts, setUserPrompts] = useState("");
  const [systemPrompts, setSystemPrompts] = useState("");
  const [responseText, setResponseText] = useState("");
  const [responseType, setResponseType] = useState("");
  const [language, setLanguage] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingLanguages, setIsFetchingLanguages] = useState(false);

  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");
  const [focusedField, setFocusedField] = useState<
    null | "userPrompt" | "systemPrompt"
  >(null);
  const [promptId, setPromptId] = useState<number | null>(null);

  // Fetch languages from API
  const fetchLanguages = useCallback(async () => {
    setIsFetchingLanguages(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.LANGUAGES_V2, { headers });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const languageNames = Array.from(
        new Set(
          (Array.isArray(data) ? data : [])
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string =>
              Boolean(name),
            ),
        ),
      );

      setLanguageOptions(languageNames);
      if (languageNames.length > 0 && !language) {
        setLanguage(languageNames[0]);
      }
    } catch (error) {
      console.error("Error fetching languages:", error);
      toast({
        title: "Error",
        description: "Failed to load languages",
        variant: "destructive",
      });
    } finally {
      setIsFetchingLanguages(false);
    }
  }, [toast, language]);

  useEffect(() => {
    if (open) {
      fetchLanguages();
    }
  }, [open, fetchLanguages]);

  useEffect(() => {
    if (!open) {
      // Reset form when dialog closes
      setUserPrompts("");
      setSystemPrompts("");
      setResponseText("");
      setResponseType("");
      setLanguage("");
      setNotes("");
      setIsSubmitting(false);
      setPromptId(null);
    }
  }, [open]);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const handleSelectPrompt = (
    selection: Extract<
      PromptSearchSelection,
      { type: "userPrompt" | "systemPrompt" }
    >,
  ) => {
    setPromptId(selection.promptId ?? null);
    if (selection.type === "userPrompt") {
      setUserPrompts(selection.userPrompt ?? "");
    } else if (selection.type === "systemPrompt") {
      setSystemPrompts(selection.systemPrompt ?? "");
    }
    // Keep the focusedField so the search button remains visible
    // setFocusedField(null);
    setSearchDialogOpen(false);
  };

  const isFormValid =
    responseText.trim() && responseType && language && notes.trim() && (promptId !== null);

  const handleSubmit = async () => {
    if (!isFormValid) {
      toast({
        title: "Validation Error",
        description: "Please fill all required fields.",
        variant: "destructive",
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
        response_text: responseText.trim(),
        response_type: responseType,
        language: language || undefined,
        user_prompt: userPrompts.trim(),
        system_prompt: systemPrompts.trim() || undefined,
        notes: notes.trim() || null,
      };

      const response = await fetch(API_ENDPOINTS.RESPONSE_CREATE_V2, {
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

      toast({
        title: "Success",
        description: "Response created successfully",
      });

      onOpenChange(false);
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error("Error creating response:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to create response",
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
            <DialogTitle className="sr-only">Add Response</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label className="text-base font-semibold">Response</Label>
              <Textarea
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                className="bg-muted min-h-[100px]"
                placeholder="Enter the response text..."
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-base font-semibold">Type</Label>
                <Select value={responseType} onValueChange={setResponseType}>
                  <SelectTrigger className="bg-muted capitalize">
                    <SelectValue placeholder="Select response type" />
                  </SelectTrigger>
                  <SelectContent className="bg-popover max-h-[300px]">
                    {responseTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">Language</Label>
                <Select
                  value={language}
                  onValueChange={setLanguage}
                  disabled={isFetchingLanguages}
                >
                  <SelectTrigger className="bg-muted capitalize">
                    <SelectValue
                      placeholder={
                        isFetchingLanguages
                          ? "Loading languages..."
                          : "Select language"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent className="bg-popover max-h-[300px]">
                    {languageOptions.length === 0 && !isFetchingLanguages ? (
                      <SelectItem value="" disabled>
                        No languages available
                      </SelectItem>
                    ) : (
                      languageOptions.map((lang) => (
                        <SelectItem key={lang} value={lang}>
                          {lang}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Prompt</Label>
              <div className="space-y-1">
                <Label className="text-sm font-normal">User Prompts</Label>
                <div className="relative">
                  <Textarea
                    value={userPrompts}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "40px",
                      overflowY: "auto"
                    }}
                    // readOnly
                    onChange = {(e) => setUserPrompts(e.target.value)}
                    className="bg-muted min-h-[100px] pr-10"
                    placeholder="Search for a prompt"
                    onFocus = {() => {
                      setFocusedField("userPrompt" );
                      // setFocusedField("userPrompts" as "userPrompt" | "systemPrompt")
                    }}
                    onBlur = {() => setFocusedField(null)}
                  />
                  {(focusedField === "userPrompt" || userPrompts) && (
                    <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onMouseDown = {e => e.preventDefault()}
                    onClick={() => handleSearchClick("userPrompt")}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                  )}
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-sm font-normal">System prompts</Label>
                <div className="relative">
                  <Textarea
                    value={systemPrompts}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "40px",
                      overflowY: "auto"
                    }}
                    // readOnly
                    onChange = {(e) => setSystemPrompts(e.target.value)}
                    className="bg-muted min-h-[80px] pr-10"
                    placeholder="Search or Type"
                    onFocus = {() => setFocusedField("systemPrompt")}
                    onBlur = {() => setFocusedField(null)}
                  />
                  {(focusedField === "systemPrompt" || systemPrompts) && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown = {e => e.preventDefault()}
                      onClick={() => handleSearchClick("systemPrompt")}
                      tabIndex = {-1}
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
              <Label className="text-base font-semibold mr-4">Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Enter notes..."
                required
              />
              <Button
                className="bg-accent hover:bg-accent/90 ml-4 text-accent-foreground px-8"
                onClick={handleSubmit}
                disabled={!isFormValid || isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <PromptSearchDialog
        open={searchDialogOpen}
        onOpenChange={setSearchDialogOpen}
        onSelect={(selection) => {
          if (
            selection.type === "userPrompt" ||
            selection.type === "systemPrompt"
          ) {
            handleSelectPrompt(selection);
          }
        }}
        searchType={searchType}
      />
    </>
  );
};
