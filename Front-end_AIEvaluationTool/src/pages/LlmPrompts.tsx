import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { LlmPromptUpdateDialog } from "@/components/LlmPromptUpdateDialog";
import { LlmPromptAddDialog } from "@/components/LlmPromptAddDialog";

interface LlmPromptItem {
  id: number;
  prompt: string;
  language: string;
}

const LlmPrompts = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPrompt, setSelectedPrompt] = useState<LlmPromptItem | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState<LlmPromptItem | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const llmPromptRows: LlmPromptItem[] = [
    {
      id: 1,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "Auto",
    },
    {
      id: 2,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "English",
    },
    {
      id: 3,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "Tamil",
    },
    {
      id: 4,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "English",
    },
    {
      id: 5,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "English",
    },
    {
      id: 6,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "Auto",
    },
    {
      id: 7,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "English",
    },
    {
      id: 8,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "Tamil",
    },
    {
      id: 9,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "English",
    },
    {
      id: 10,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "English",
    },
    {
      id: 11,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "Auto",
    },
    {
      id: 12,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "English",
    },
    {
      id: 13,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "Tamil",
    },
    {
      id: 14,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "English",
    },
    {
      id: 15,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "English",
    },
    {
      id: 16,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "English",
    },
    {
      id: 17,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "English",
    },
    {
      id: 18,
      prompt: "Evaluate if the agent's response, the llm response for sensitive data, check the LLM is rejection, Evaluate the response",
      language: "Tamil",
    },
    {
      id: 19,
      prompt: "You are llm judge aimed to evaluate the llm response for sensitive data, check the LLM is rejection, Evaluation the",
      language: "English",
    },
    {
      id: 20,
      prompt: "You are llm judge aimed to evaluate the llm response construct a sentence more then 20 words based on above",
      language: "English",
    },
  ];

  const filteredPrompts = llmPromptRows.filter(
    (p) =>
      p.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.language.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredPrompts.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  const paginatedPrompts = filteredPrompts.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">LLM Prompts</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="llmprompts">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="llmprompts">LLM Prompts</SelectItem>
                <SelectItem value="language">Language</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />
            <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {totalItems === 0
                  ? "0"
                  : `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(
                      currentPage * itemsPerPage,
                      totalItems
                    )} of ${totalItems}`}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">Prompt ID</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">LLM Prompts</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Language</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedPrompts.map((row) => (
                    <tr
                      key={row.id}
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => setSelectedPrompt(row)}
                    >
                      <td className="p-2 text-center">{row.id}</td>
                      <td className="p-2 truncate max-w-[650px] pr-8 mr-2">{row.prompt}</td>
                      <td className="p-2">{row.language}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-6 sticky bottom-5">
            <Button
              className="bg-primary hover:bg-primary/90"
              onClick={() => setAddDialogOpen(true)}
            >
              + Add Prompts
            </Button>
          </div>
        </div>
      </main>

      <Dialog open={!!selectedPrompt} onOpenChange={() => setSelectedPrompt(null)}>
        <DialogContent
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="sr-only">LLM Prompt Details</DialogTitle>
          </DialogHeader>

          {selectedPrompt && (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="space-y-1">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <Textarea value={selectedPrompt.prompt} readOnly className="bg-muted min-h-[80px]" />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Language</Label>
                <Input value={selectedPrompt.language} readOnly className="bg-muted" />
              </div>
            </div>
          )}

          <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center gap-4 border-gray-200 z-10">
            <Button variant="destructive">Delete</Button>
            <Button
              className="bg-primary hover:bg-primary/90"
              onClick={() => {
                setUpdatePrompt(selectedPrompt);
                setSelectedPrompt(null);
              }}
            >
              Update
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <LlmPromptUpdateDialog
        prompt={updatePrompt}
        open={!!updatePrompt}
        onOpenChange={(open) => !open && setUpdatePrompt(null)}
      />

      <LlmPromptAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </div>
  );
};

export default LlmPrompts;
