import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const domains = ["General", "Education", "Agriculture", "Healthcare", "Learning Disability"];
const languages = ["Auto", "English", "Tamil", "Hindi", "Gujarati", "Bengali"];

interface PromptAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd?: (prompt: { userPrompt: string; systemPrompt: string; language: string; domain: string }) => void;
}

export function PromptAddDialog({ open, onOpenChange, onAdd }: PromptAddDialogProps) {
  const [userPrompt, setUserPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [language, setLanguage] = useState("");
  const [domain, setDomain] = useState("");
  const [notes, setNotes] = useState("");
 
  const isValid = userPrompt.trim().length > 0 && systemPrompt.trim().length > 0;

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
            <Label className="text-base font-semibold">Language</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger>
                <SelectValue placeholder="Select a language" />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[300px]">

                {languages.map((l) => (
                  <SelectItem key={l} value={l}>{l}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">Domain</Label>
            <Select value={domain} onValueChange={setDomain}>
              <SelectTrigger>
                <SelectValue placeholder="Select a domain" />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[200px]">
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
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border border-green-800 "
            disabled={!isValid || !notes}
            onClick={() => {
              onAdd?.({ userPrompt, systemPrompt, language, domain });
              onOpenChange(false);
              setUserPrompt("");
              setSystemPrompt("");
              setLanguage(languages[0]);
              setDomain(domains[0]);
            }}
          >
            Submit
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default PromptAddDialog;


