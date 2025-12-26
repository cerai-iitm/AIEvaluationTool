import { useCallback, useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";

export interface LlmPromptItem {
  llmPromptId: number;
  prompt: string;
  language: string | null;
  notes?: string;
}

interface LlmPromptUpdateDialogProps {
  prompt: LlmPromptItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: (prompt: LlmPromptItem) => void;
  onSuccess?: () => void;
}

export function LlmPromptUpdateDialog({
  prompt,
  open,
  onOpenChange,
  onUpdate,
  onSuccess,
}: LlmPromptUpdateDialogProps) {
  const { toast } = useToast();
  const [promptText, setPromptText] = useState("");
  const [language, setLanguage] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isOptionsLoading, setIsOptionsLoading] = useState(false);

  const promptLanguage = prompt?.language ?? "";

  useEffect(() => {
    if (prompt) {
      setPromptText(prompt.prompt);
      setLanguage(promptLanguage);
      setNotes("");
    }
  }, [prompt, promptLanguage]);

  useEffect(() => {
    if (!open) {
      setNotes("");
      setIsSubmitting(false);
      setLanguageOptions([]);
    }
  }, [open]);

  const fetchLanguages = useCallback(async () => {
    setIsOptionsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.LANGUAGES_V2, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to load languages");
      }

      const languageData = await response.json();
      const languageNames = Array.from(
        new Set([
          ...(Array.isArray(languageData) ? languageData : [])
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string =>
              Boolean(name),
            ),
          ...(promptLanguage ? [promptLanguage] : []),
        ]),
      );

      setLanguageOptions(languageNames);

      setLanguage((current) => {
        if (current && languageNames.includes(current)) {
          return current;
        }
        if (promptLanguage && languageNames.includes(promptLanguage)) {
          return promptLanguage;
        }
        return languageNames[0] ?? "";
      });
    } catch (error: any) {
      console.error("Failed to load languages:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to load languages",
        variant: "destructive",
      });
    } finally {
      setIsOptionsLoading(false);
    }
  }, [promptLanguage, toast]);

  useEffect(() => {
    if (open) {
      fetchLanguages();
    }
  }, [open, fetchLanguages]);

  if (!prompt) return null;

  const originalLanguage = prompt.language ?? "";

  const isChanged =
    promptText !== prompt.prompt || language !== originalLanguage;

  const handleSubmit = async () => {
    if (!isChanged || !notes.trim() || !language) {
      toast({
        title: "Validation error",
        description:
          "Please modify the prompt, select language, and provide notes before submitting.",
        variant: "destructive",
      });
      return;
    }

    if (!promptText.trim()) {
      toast({
        title: "Validation error",
        description:
          "LLM Prompt is empty.",
        variant: "destructive",
      })
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        API_ENDPOINTS.LLMPROMPT_UPDATE_V2(prompt.llmPromptId),
        {
          method: "PUT",
          headers,
          body: JSON.stringify({
            llmPromptId: prompt.llmPromptId,
            prompt: promptText.trim(),
            language,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update LLM prompt");
      }

      const updated = {
        ...prompt,
        llmPromptId: prompt.llmPromptId,
        prompt: promptText,
        language,
      };
      onUpdate?.(updated);
      onSuccess?.();

      toast({
        title: "LLM Prompt updated",
        description: `LLM Prompt ${prompt.llmPromptId} updated successfully.`,
      });

      onOpenChange(false);
    } catch (error: any) {
      console.error("Update LLM prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to update LLM prompt",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[80vh] max-w-[30vw] overflow-y-auto"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="sr-only">LLM Prompts</DialogTitle>
        </DialogHeader>
        <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
          <div className="space-y-1">
            <Label className="text-base font-semibold">LLM Prompt</Label>
            <Textarea
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="bg-muted min-h-[80px]"
              style={{
                maxHeight: "120px",
                minHeight: "75px",
                overflowY: "auto",
              }}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">Language Name</Label>
            <Select
              value={language || undefined}
              onValueChange={setLanguage}
              disabled={isOptionsLoading || !languageOptions.length}
            >
              <SelectTrigger className="capitalize bg-muted">
                <SelectValue 
                  placeholder={
                    isOptionsLoading
                      ? "Loading languages..."
                      : "Select a language"
                  }
                />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[300px]">
                {languageOptions.length ? (
                  languageOptions.map((l) => (
                    <SelectItem key={l} value={l} className="capitalize">
                      {l}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="__no-language" disabled>
                    No languages available
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
          <Label className="text-base font-semibold mr-2">Notes</Label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="bg-muted"
            placeholder="Enter notes"
            maxLength={75}
          />

          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 ml-4"
            disabled={!isChanged || !notes.trim() || isSubmitting || !language || !promptText.trim()}
            onClick={handleSubmit}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              "Submit"
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default LlmPromptUpdateDialog;
