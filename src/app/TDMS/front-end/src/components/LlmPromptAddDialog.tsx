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

interface LlmPromptAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd?: (prompt: {
    prompt: string;
    language: string;
    notes?: string;
  }) => void;
  onSuccess?: () => void;
}

export function LlmPromptAddDialog({
  open,
  onOpenChange,
  onAdd,
  onSuccess,
}: LlmPromptAddDialogProps) {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isOptionsLoading, setIsOptionsLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setPrompt("");
      setLanguage("");
      setNotes("");
      setIsSubmitting(false);
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
        new Set(
          (Array.isArray(languageData) ? languageData : [])
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string =>
              Boolean(name),
            ),
        ),
      );

      setLanguageOptions(languageNames);
      setLanguage((current) => {
        if (current && languageNames.includes(current)) {
          return current;
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
  }, [toast]);

  useEffect(() => {
    if (open) {
      fetchLanguages();
    }
  }, [open, fetchLanguages]);

  const isValid = prompt.trim().length > 0 && language.trim().length > 0;

  const handleSubmit = async () => {
    if (!isValid || !notes.trim()) {
      toast({
        title: "Validation error",
        description:
          "Please fill all fields including notes before submitting.",
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

      const response = await fetch(API_ENDPOINTS.LLMPROMPT_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify({
          prompt: prompt.trim(),
          language,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create LLM prompt");
      }

      toast({
        title: "LLM Prompt created",
        description: "LLM Prompt added successfully.",
      });

      onAdd?.({ prompt, language, notes });
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      console.error("Create LLM prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to create LLM prompt",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[90vh] overflow-y-auto"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="sr-only">LLM Prompts</DialogTitle>
        </DialogHeader>

        <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
          <div className="space-y-1">
            <Label className="text-base font-semibold">LLM Prompt</Label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="bg-muted min-h-[80px]"
              placeholder="Enter your LLM prompt here..."
            />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">Language</Label>
            <Select
              value={language || undefined}
              onValueChange={setLanguage}
              disabled={isOptionsLoading || !languageOptions.length}
            >
              <SelectTrigger>
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
                    <SelectItem key={l} value={l}>
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
          <div className="space-y-1">

          </div>
        </div>

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center items-center gap-4 border-gray-200 z-10">
          <Label className="text-base font-semibold">Notes</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="bg-muted"
              placeholder="Enter notes (required)"
            />
          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800"
            disabled={!isValid || !notes.trim() || isSubmitting}
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

export default LlmPromptAddDialog;
