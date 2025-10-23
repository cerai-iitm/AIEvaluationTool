import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const languages = ["Auto", "English", "Tamil", "Hindi", "Gujarati", "Bengali"];

export interface LlmPromptItem {
  id: number;
  prompt: string;
  language: string;
  notes?: string;
}

interface LlmPromptUpdateDialogProps {
  prompt: LlmPromptItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: (prompt: LlmPromptItem) => void;
}

export function LlmPromptUpdateDialog({ prompt, open, onOpenChange, onUpdate }: LlmPromptUpdateDialogProps) {
  const [promptText, setPromptText] = useState("");
  const [language, setLanguage] = useState(languages[0]);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (prompt) {
      setPromptText(prompt.prompt);
      setLanguage(prompt.language);
      setNotes(prompt.notes || "");
    }
  }, [prompt]);

  if (!prompt) return null;

  const isChanged =
    promptText !== prompt.prompt ||
    language !== prompt.language ||
    notes !== (prompt.notes || "");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" onOpenAutoFocus={(e) => e.preventDefault()}>
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
            />
          </div>
          <div className="space-y-1">
            <Label className="text-base font-semibold">Language Name</Label>
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
            <Label className="text-base font-semibold">Notes</Label>
            <Input 
              value={notes} 
              onChange={(e) => setNotes(e.target.value)} 
              className="bg-muted" 
              placeholder="Enter notes (optional)"
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center gap-4 border-gray-200 z-10">
          <Button 
            variant="destructive"
            onClick={() => {
              // Handle delete functionality
              onOpenChange(false);
            }}
          >
            Delete
          </Button>
          <Button
            className="bg-primary hover:bg-primary/90"
            disabled={!isChanged}
            onClick={() => {
              const updated = { ...prompt, prompt: promptText, language, notes };
              onUpdate?.(updated);
              onOpenChange(false);
            }}
          >
            Update
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default LlmPromptUpdateDialog;
