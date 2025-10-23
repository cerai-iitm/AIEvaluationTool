import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const domains = ["General", "Education", "Agriculture", "Healthcare", "Learning Disability"];
const languages = ["Auto", "English", "Tamil", "Hindi", "Gujarati", "Bengali"];

export interface PromptItem {
  id: number;
  userPrompt: string;
  systemPrompt: string;
  language: string;
  domain: string;
  notes?: string;
}

interface PromptUpdateDialogProps {
  prompt: PromptItem ;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: (prompt: PromptItem) => void;
}

export function PromptUpdateDialog({ prompt, open, onOpenChange, onUpdate }: PromptUpdateDialogProps) {
  const [userPrompt, setUserPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [language, setLanguage] = useState(languages[0]);
  const [domain, setDomain] = useState(domains[0]);
  const [notes, setNotes] = useState("");

  // const isValid = userPrompt.trim().length > 0 && systemPrompt.trim().length > 0;

  useEffect(() => {
    if (prompt) {
      setUserPrompt(prompt.userPrompt);
      setSystemPrompt(prompt.systemPrompt);
      setLanguage(prompt.language);
      setDomain(prompt.domain);
    }
  }, [prompt]);

  if (!prompt) return null;

  const isChanged =
    userPrompt !== prompt.userPrompt ||
    systemPrompt !== prompt.systemPrompt ||
    language !== prompt.language ||
    domain !== prompt.domain;
    

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
            <Textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} className="bg-muted min-h-[80px]" />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">language Name</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[300px]">
                {languages.map((l) => (
                  <SelectItem key={l} value={l}>{l}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Domain Name</Label>
            <Select value={domain} onValueChange={setDomain}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[300px]">
                {domains.map((d) => (
                  <SelectItem key={d} value={d}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center items-center gap-4 border-gray-200 z-10">

          <Label className="text-base font-bold mr-2">Notes</Label>
          <Input value={notes} onChange={(e) => setNotes(e.target.value)} className="bg-gray-200 rounded px-4 py-1 mr-4 w-96" placeholder="Enter notes" required />
          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 "
            disabled={!isChanged || !notes}
            onClick={() => {
              const updated = { ...prompt, userPrompt, systemPrompt, language, domain };
              onUpdate?.(updated);
              onOpenChange(false);
            }}
          >
            Submit
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default PromptUpdateDialog;


