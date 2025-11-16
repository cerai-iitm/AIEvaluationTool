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

interface Response {
  id: number;
  response_id: number;
  name?: string;
  responseText: string;
  responseType: string;
  language: string;
  userPrompts: string;
  systemPrompts: string;
  notes?: string;
}

interface ResponseUpdateDialogProps {
  response: Response | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateSuccess?: () => void;
}

const responseTypes = [
  { value: "GT", label: "Ground Truth" },
  { value: "GTDesc", label: "Ground Truth Description" },
  { value: "NA", label: "Not Applicable" },
];

export const ResponseUpdateDialog = ({
  response,
  open,
  onOpenChange,
  onUpdateSuccess,
}: ResponseUpdateDialogProps) => {
  const { toast } = useToast();
  const [responseText, setResponseText] = useState(response?.responseText || "");
  const [responseType, setResponseType] = useState(response?.responseType || "");
  const [language, setLanguage] = useState(response?.language || "");
  const [userPrompts, setUserPrompts] = useState(response?.userPrompts || "");
  const [systemPrompts, setSystemPrompts] = useState(response?.systemPrompts || "");
  const [notes, setNotes] = useState(response?.notes || "");
  const [isLoading, setIsLoading] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingLanguages, setIsFetchingLanguages] = useState(false);
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");
  const [focusedField, setFocusedField] = useState<null | "userPrompt" | "systemPrompt">(null);

  // Map display name to backend response type
  const mapDisplayToResponseType = (display: string): string => {
    const mapping: Record<string, string> = {
      'Ground Truth': 'GT',
      'Ground Truth Description': 'GTDesc',
      'Not Applicable': 'NA',
    };
    return mapping[display] || display;
  };

  // Map backend response type to display name
  const mapResponseTypeToDisplay = (type: string): string => {
    const mapping: Record<string, string> = {
      'GT': 'Ground Truth',
      'GTDesc': 'Ground Truth Description',
      'NA': 'Not Applicable',
    };
    return mapping[type] || type;
  };

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

      const response = await fetch(API_ENDPOINTS.LANGUAGES, { headers });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const languageNames = Array.from(
        new Set(
          (Array.isArray(data) ? data : [])
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string => Boolean(name))
        )
      );

      setLanguageOptions(languageNames);
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
  }, [toast]);

  useEffect(() => {
    if (open) {
      fetchLanguages();
    }
  }, [open, fetchLanguages]);

  useEffect(() => {
    if (response) {
      setResponseText(response.responseText || "");
      setResponseType(response.responseType || "");
      setLanguage(response.language || "");
      setUserPrompts(response.userPrompts || "");
      setSystemPrompts(response.systemPrompts || "");
      setNotes(response.notes || "");
    }
  }, [response]);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    switch (selection.type) {
      case "userPrompt":
        setUserPrompts(selection.userPrompt);
        if (selection.systemPrompt !== undefined) {
          setSystemPrompts(selection.systemPrompt ?? "");
        }
        break;
      case "systemPrompt":
        setSystemPrompts(selection.systemPrompt);
        if (selection.userPrompt) {
          setUserPrompts(selection.userPrompt);
        }
        break;
      default:
        break;
    }
    setFocusedField(null);
    setSearchDialogOpen(false);
  };

  const responseInitial = response || {
    id: 0,
    response_id: 0,
    responseText: "",
    responseType: "",
    language: "",
    userPrompts: "",
    systemPrompts: "",
    notes: "",
  };

  const isChanged = (
    responseText !== (responseInitial.responseText || "") ||
    responseType !== (responseInitial.responseType || "") ||
    language !== (responseInitial.language || "") ||
    userPrompts !== (responseInitial.userPrompts || "") ||
    systemPrompts !== (responseInitial.systemPrompts || "") ||
    notes !== (responseInitial.notes || "")
  );

  const handleSubmit = async () => {
    if (!response?.response_id) {
      toast({
        title: "Error",
        description: "Response ID is missing",
        variant: "destructive",
      });
      return;
    }

    if (!notes || !notes.trim()) {
      toast({
        title: "Validation Error",
        description: "Notes field is required",
        variant: "destructive",
      });
      return;
    }

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
      
      if (responseText !== (responseInitial.responseText || "")) {
        updatePayload.response_text = responseText;
      }
      if (responseType !== (responseInitial.responseType || "")) {
        updatePayload.response_type = mapDisplayToResponseType(responseType);
      }
      if (language !== (responseInitial.language || "")) {
        updatePayload.lang_name = language;
      }
      if (userPrompts !== (responseInitial.userPrompts || "")) {
        updatePayload.user_prompt = userPrompts;
      }
      if (systemPrompts !== (responseInitial.systemPrompts || "")) {
        updatePayload.system_prompt = systemPrompts;
      }

      const response_api = await fetch(
        API_ENDPOINTS.RESPONSE_UPDATE(response.response_id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify(updatePayload),
        }
      );

      if (!response_api.ok) {
        const errorData = await response_api.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response_api.status}`
        );
      }

      toast({
        title: "Success",
        description: "Response updated successfully",
      });

      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      onOpenChange(false);
    } catch (error) {
      console.error("Error updating response:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to update response",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
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
              <Label className="text-base font-semibold">Response</Label>
              <Textarea
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                className="bg-muted min-h-[100px]"
              />
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
                      <SelectItem key={type.value} value={type.label}>
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
                  <SelectTrigger>
                    <SelectValue
                      placeholder={
                        isFetchingLanguages ? "Loading languages..." : "Select language"
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
                    onChange={(e) => setUserPrompts(e.target.value)}
                    onFocus={() => setFocusedField("userPrompt")}
                    onBlur={() => setTimeout(() => setFocusedField(null), 100)}
                    className="bg-muted min-h-[100px] pr-10"
                  />
                  {focusedField === "userPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={(e) => e.preventDefault()}
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
                    onChange={(e) => setSystemPrompts(e.target.value)}
                    onFocus={() => setFocusedField("systemPrompt")}
                    onBlur={() => setTimeout(() => setFocusedField(null), 100)}
                    className="bg-muted min-h-[80px] pr-10"
                  />
                  {focusedField === "systemPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSearchClick("systemPrompt")}
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-base font-semibold">Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Enter notes..."
                required
              />
            </div>

            <div className="flex justify-center pt-4">
              <Button
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
                onClick={handleSubmit}
                disabled={!isChanged || !notes || isLoading}
              >
                {isLoading ? "Updating..." : "Submit"}
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
