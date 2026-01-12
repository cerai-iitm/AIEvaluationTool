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
import { Loader2, Search } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";

export interface PromptItem {
  prompt_id: number;
  user_prompt: string;
  system_prompt: string;
  language: string | null;
  domain: string | null;
  notes?: string;
}

interface PromptUpdateDialogProps {
  prompt: PromptItem;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: (prompt: PromptItem) => void;
  onSuccess?: () => void;
}

export function PromptUpdateDialog({
  prompt,
  open,
  onOpenChange,
  onUpdate,
  onSuccess,
}: PromptUpdateDialogProps) {
  const { toast } = useToast();
  const [userPrompt, setUserPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [language, setLanguage] = useState("");
  const [domain, setDomain] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [isOptionsLoading, setIsOptionsLoading] = useState(false);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("systemPrompt");
  const [focusedField, setFocusedField] = useState<null | "systemPrompt">(null);

  const promptLanguage = prompt?.language ?? "";
  const promptDomain = prompt?.domain ?? "";

  useEffect(() => {
    if (prompt) {
      setUserPrompt(prompt.user_prompt);
      setSystemPrompt(prompt.system_prompt);
      setLanguage(promptLanguage);
      setDomain(promptDomain);
      setNotes("");
    }
  }, [prompt, promptLanguage, promptDomain]);

  useEffect(() => {
    if (!open) {
      setNotes("");
      setIsSubmitting(false);
      setLanguageOptions([]);
      setDomainOptions([]);
      setFocusedField(null);
      setSearchDialogOpen(false);
    }
  }, [open]);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
    if (type === "systemPrompt") {
      setFocusedField("systemPrompt");
    } else {
      setFocusedField(null);
    }
  };

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    switch (selection.type) {
      case "systemPrompt":
        setSystemPrompt(selection.systemPrompt);
        break;
      default:
        break;
    }
    setSearchDialogOpen(false);
    setFocusedField(null);
  };

  const fetchReferenceData = useCallback(async () => {
    setIsOptionsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const [languagesResponse, domainsResponse] = await Promise.all([
        fetch(API_ENDPOINTS.LANGUAGES_V2, { method: "GET", headers }),
        fetch(API_ENDPOINTS.DOMAINS_V2, { method: "GET", headers }),
      ]);

      if (!languagesResponse.ok || !domainsResponse.ok) {
        const langError = await languagesResponse.json().catch(() => ({}));
        const domainError = await domainsResponse.json().catch(() => ({}));
        throw new Error(
          langError.detail ||
            domainError.detail ||
            "Failed to load reference data",
        );
      }

      const languageData = await languagesResponse.json();
      const domainData = await domainsResponse.json();

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
      const domainNames = Array.from(
        new Set([
          ...(Array.isArray(domainData) ? domainData : [])
            .map((dom: any) => dom?.domain_name)
            .filter((name: string | null | undefined): name is string =>
              Boolean(name),
            ),
          ...(promptDomain ? [promptDomain] : []),
        ]),
      );

      setLanguageOptions(languageNames);
      setDomainOptions(domainNames);

      setLanguage((current) => {
        if (current && languageNames.includes(current)) {
          return current;
        }
        if (promptLanguage && languageNames.includes(promptLanguage)) {
          return promptLanguage;
        }
        return languageNames[0] ?? "";
      });
      setDomain((current) => {
        if (current && domainNames.includes(current)) {
          return current;
        }
        if (promptDomain && domainNames.includes(promptDomain)) {
          return promptDomain;
        }
        return domainNames[0] ?? "";
      });
    } catch (error: any) {
      console.error("Failed to load reference data:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to load languages/domains",
        variant: "destructive",
      });
    } finally {
      setIsOptionsLoading(false);
    }
  }, [promptLanguage, promptDomain, toast]);

  useEffect(() => {
    if (open) {
      fetchReferenceData();
    }
  }, [open, fetchReferenceData]);

  if (!prompt) return null;

  const originalLanguage = prompt.language ?? "";
  const originalDomain = prompt.domain ?? "";

  const isChanged =
    userPrompt !== prompt.user_prompt ||
    systemPrompt !== prompt.system_prompt ||
    language !== originalLanguage ||
    domain !== originalDomain;

  const handleSubmit = async () => {
    if (!isChanged || !notes.trim() || !language || !domain) {
      toast({
        title: "Validation error",
        description:
          "Please modify the prompt, select language and domain, and add notes.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        API_ENDPOINTS.PROMPT_UPDATE_V2(prompt.prompt_id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify({
            prompt_id: prompt.prompt_id,
            user_prompt: userPrompt.trim(),
            system_prompt: systemPrompt.trim(),
            language,
            domain,
            notes: notes.trim() || null,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update prompt");
      }

      const updated = {
        ...prompt,
        prompt_id: prompt.prompt_id,
        user_prompt: userPrompt,
        system_prompt: systemPrompt,
        language,
        domain,
      };
      onUpdate?.(updated);
      onSuccess?.();

      toast({
        title: "Prompt updated",
        description: `Prompt ${prompt.prompt_id} updated successfully.`,
      });

      onOpenChange(false);
    } catch (error: any) {
      console.error("Update prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to update prompt",
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
          <DialogTitle className="sr-only">Prompts</DialogTitle>
        </DialogHeader>
        <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
          <div className="space-y-1">
            <Label className="text-base font-semibold">User Prompt</Label>
            <Textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="bg-muted min-h-[80px]"
              style={{
                maxHeight: "120px",
                minHeight: "70px",
                overflow: "auto",
              }}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">System Prompt</Label>
            <div className="relative">
              <Textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                onFocus={() => setFocusedField("systemPrompt")}
                onBlur={() => setFocusedField(null)}
                className="bg-muted min-h-[80px] pr-10"
                style={{
                  maxHeight: "120px",
                  minHeight: "70px",
                  overflow: "auto",
                }}
                placeholder="Enter system prompt or Search "
              />
              {focusedField === "systemPrompt" && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => handleSearchClick("systemPrompt")}
                  tabIndex={-1}
                >
                  <Search className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label className="text-base font-semibold">Language</Label>
              <Select
                value={language || undefined}
                onValueChange={setLanguage}
                disabled={isOptionsLoading || !languageOptions.length}
              >
                <SelectTrigger className="bg-muted capitalize">
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
            <div className="space-y-1 pb-4">
              <Label className="text-base font-semibold">Domain</Label>
              <Select
                value={domain || undefined}
                onValueChange={setDomain}
                disabled={isOptionsLoading || !domainOptions.length}
              >
                <SelectTrigger className="bg-muted capitalize">
                  <SelectValue
                    placeholder={
                      isOptionsLoading ? "Loading domains..." : "Select a domain"
                    }
                  />
                </SelectTrigger>
                <SelectContent className="bg-popover max-h-[300px]">
                  {domainOptions.length ? (
                    domainOptions.map((d) => (
                      <SelectItem key={d} value={d} className="capitalize">
                        {d}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="__no-domain" disabled>
                      No domains available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center items-center gap-4 border-gray-200 z-10">
          <Label className="text-base font-bold mr-2">Notes</Label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
            placeholder="Enter notes"
            required
          />
          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 "
            disabled={
              !isChanged ||
              !notes.trim() ||
              !language ||
              !domain ||
              isSubmitting
            }
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
      <PromptSearchDialog
        open={searchDialogOpen}
        onOpenChange={setSearchDialogOpen}
        onSelect={handleSelectPrompt}
        searchType={searchType}
      />
    </Dialog>
  );
}

export default PromptUpdateDialog;
