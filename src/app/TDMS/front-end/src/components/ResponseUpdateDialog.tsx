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
  response_id: number;
  response_text: string;
  response_type: string;
  language: string;
  user_prompt: string;
  system_prompt: string;
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
  const [responseText, setResponseText] = useState(
    response?.response_text || "",
  );
  const [responseType, setResponseType] = useState(
    response?.response_type || "",
  );
  const [language, setLanguage] = useState(response?.language || "");
  const [userPrompts, setUserPrompts] = useState(response?.user_prompt || "");
  const [systemPrompts, setSystemPrompts] = useState(
    response?.system_prompt || "",
  );
  const [notes, setNotes] = useState(response?.notes || "");
  const [isLoading, setIsLoading] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingLanguages, setIsFetchingLanguages] = useState(false);

  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");
  const [focusedField, setFocusedField] = useState<
    null | "userPrompt" | "systemPrompt"
  >(null);

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
      setResponseText(response.response_text || "");
      setResponseType(response.response_type || "");
      setLanguage(response.language || "");
      setUserPrompts(response.user_prompt || "");
      setSystemPrompts(response.system_prompt || "");
      setNotes(response.notes || "");
    }
  }, [response]);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
  };

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    setUserPrompts(selection.userPrompt);
    setSystemPrompts(selection.systemPrompt ?? "");
    setFocusedField(null);
    setSearchDialogOpen(false);
  };

  const responseInitial = response || {
    response_id: 0,
    response_text: "",
    response_type: "",
    language: "",
    user_prompt: "",
    system_prompt: "",
    notes: "",
  };

  const isChanged =
    responseText !== (responseInitial.response_text || "") ||
    responseType !== (responseInitial.response_type || "") ||
    language !== (responseInitial.language || "") ||
    userPrompts !== (responseInitial.user_prompt || "") ||
    systemPrompts !== (responseInitial.system_prompt || "") ||
    notes !== (responseInitial.notes || "");

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

      const updatePayload: any = {};

      if (responseText !== (responseInitial.response_text || "")) {
        updatePayload.response_text = responseText;
      }
      if (responseType !== (responseInitial.response_type || "")) {
        updatePayload.response_type = responseType;
      }
      if (language !== (responseInitial.language || "")) {
        updatePayload.language = language;
      }

      const response_api = await fetch(
        API_ENDPOINTS.RESPONSE_UPDATE_V2(response.response_id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify(updatePayload),
        },
      );

      if (!response_api.ok) {
        const errorData = await response_api.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response_api.status}`,
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
          error instanceof Error ? error.message : "Failed to update response",
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
                  <SelectTrigger className="bg-muted capitalize">
                    <SelectValue />
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
                    readOnly
                    className="bg-muted min-h-[100px] pr-10"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-sm font-normal">System prompts</Label>
                <div className="relative">
                  <Textarea
                    value={systemPrompts}
                    readOnly
                    className="bg-muted min-h-[80px] pr-10"
                  />
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
