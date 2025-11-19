import { useCallback, useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";

interface PromptAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd?: (prompt: { userPrompt: string; systemPrompt: string; language: string; domain: string }) => void;
  onSuccess?: () => void;
}

export function PromptAddDialog({ open, onOpenChange, onAdd, onSuccess }: PromptAddDialogProps) {
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

  useEffect(() => {
    if (!open) {
      setUserPrompt("");
      setSystemPrompt("");
      setLanguage("");
      setDomain("");
      setNotes("");
      setIsSubmitting(false);
    }
  }, [open]);

  const fetchReferenceData = useCallback(async () => {
    setIsOptionsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const [languagesResponse, domainsResponse] = await Promise.all([
        fetch(API_ENDPOINTS.LANGUAGES, { method: "GET", headers }),
        fetch(API_ENDPOINTS.DOMAINS, { method: "GET", headers }),
      ]);

      if (!languagesResponse.ok || !domainsResponse.ok) {
        const langError = await languagesResponse.json().catch(() => ({}));
        const domainError = await domainsResponse.json().catch(() => ({}));
        throw new Error(langError.detail || domainError.detail || "Failed to load reference data");
      }

      const languageData = await languagesResponse.json();
      const domainData = await domainsResponse.json();

      const languageNames = Array.from(
        new Set(
          (Array.isArray(languageData) ? languageData : [])
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string => Boolean(name))
        )
      );
      const domainNames = Array.from(
        new Set(
          (Array.isArray(domainData) ? domainData : [])
            .map((dom: any) => dom?.domain_name)
            .filter((name: string | null | undefined): name is string => Boolean(name))
        )
      );

      setLanguageOptions(languageNames);
      setDomainOptions(domainNames);

      setLanguage((current) => {
        if (current && languageNames.includes(current)) {
          return current;
        }
        return languageNames[0] ?? "";
      });
      setDomain((current) => {
        if (current && domainNames.includes(current)) {
          return current;
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
  }, [toast]);

  useEffect(() => {
    if (open) {
      fetchReferenceData();
    }
  }, [open, fetchReferenceData]);

  const isValid = userPrompt.trim().length > 0 && systemPrompt.trim().length > 0;

  const handleSubmit = async () => {
    if (!isValid || !notes.trim() || !language || !domain) {
      toast({
        title: "Validation error",
        description: "Please fill all fields before submitting.",
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

      const response = await fetch(API_ENDPOINTS.PROMPT_CREATE, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_prompt: userPrompt.trim(),
          system_prompt: systemPrompt.trim(),
          language,
          domain,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create prompt");
      }

      toast({
        title: "Prompt created",
        description: "Prompt added successfully.",
      });

      onAdd?.({ userPrompt, systemPrompt, language, domain });
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      console.error("Create prompt failed:", error);
      toast({
        title: "Error",
        description: error.message || "Unable to create prompt",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" onOpenAutoFocus={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="sr-only">Prompts</DialogTitle>
        </DialogHeader>

        <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
          <div className="space-y-1">
            <Label className="text-base font-semibold">User Prompt</Label>
            <Textarea value={userPrompt} onChange={(e) => setUserPrompt(e.target.value)} className="bg-muted min-h-[80px]" />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">System Prompt</Label>
            <Textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} className="bg-muted min-h-[80px]" readOnly />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">Language</Label>
            <Select
              value={language || undefined}
              onValueChange={setLanguage}
              disabled={isOptionsLoading || !languageOptions.length}
            >
              <SelectTrigger>
                <SelectValue placeholder={isOptionsLoading ? "Loading languages..." : "Select a language"} />
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
            <Label className="text-base font-semibold">Domain</Label>
            <Select
              value={domain || undefined}
              onValueChange={setDomain}
              disabled={isOptionsLoading || !domainOptions.length}
            >
              <SelectTrigger>
                <SelectValue placeholder={isOptionsLoading ? "Loading domains..." : "Select a domain"} />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[200px]">
                {domainOptions.length ? (
                  domainOptions.map((d) => (
                    <SelectItem key={d} value={d}>
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

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center items-center gap-4 border-gray-200 z-10">
          <Label className="text-base font-bold mr-2">Notes</Label>
          <Input value={notes} onChange={(e) => setNotes(e.target.value)} className="bg-gray-200 rounded px-4 py-1 mr-4 w-96" placeholder="Enter notes" required />
          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border border-green-800 "
            disabled={!isValid || !notes.trim() || !language || !domain || isSubmitting}
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

export default PromptAddDialog;


