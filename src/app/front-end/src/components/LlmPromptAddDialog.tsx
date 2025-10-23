import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const languages = ["Auto", "English", "Tamil", "Hindi", "Gujarati", "Bengali"];

interface LlmPromptAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd?: (prompt: { prompt: string; language: string; notes?: string }) => void;
}

export function LlmPromptAddDialog({ open, onOpenChange, onAdd }: LlmPromptAddDialogProps) {
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("");
  const [notes, setNotes] = useState("");

  const isValid = prompt.trim().length > 0;

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
              value={prompt} 
              onChange={(e) => setPrompt(e.target.value)} 
              className="bg-muted min-h-[80px]" 
              placeholder="Enter your LLM prompt here..."
            />
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
            <Label className="text-base font-semibold">Notes</Label>
            <Input 
              value={notes} 
              onChange={(e) => setNotes(e.target.value)} 
              className="bg-muted" 
              placeholder="Enter notes (optional)"
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center items-center gap-4 border-gray-200 z-10">
          <Button
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800"
            disabled={!isValid}
            onClick={() => {
              onAdd?.({ prompt, language, notes });
              onOpenChange(false);
              setPrompt("");
              setLanguage("");
              setNotes("");
            }}
          >
            Submit
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default LlmPromptAddDialog;
