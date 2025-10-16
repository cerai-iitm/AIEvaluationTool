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
import { PromptUpdateDialog } from "@/components/PromptUpdateDialog";
import { PromptAddDialog } from "@/components/PromptAddDialog";

interface PromptItem {
  id: number; // Prompt ID in table
  userPrompt: string;
  systemPrompt: string;
  language: string;
  domain: string;
  notes?: string;
}

const Prompts = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPrompt, setSelectedPrompt] = useState<PromptItem | null>(null);
  const [updatePrompt, setUpdatePrompt] = useState<PromptItem | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const promptRows: PromptItem[] = [
    {
      id: 1,
      userPrompt: "Duniya का highest रेल पुल and arch bridge कहाँ है? Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quas. Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quas.",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Auto",
      domain: "Learning Disability",
    },
    {
      id: 2,
      userPrompt:
        "Please explain photosynthesis in Gujarati and end with a",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "General",
    },
    {
      id: 3,
      userPrompt: "Indiavil எத்தனை யுபி பதிவு நுழைவுகள் உள்ளன?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Tamil",
      domain: "Education",
    },
    {
      id: 4,
      userPrompt:
        "I'm a deaf person and want to get COVID-19 vaccine info",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "agriculture",
    },
    {
      id: 5,
      userPrompt:
        "I am a transgender person and I want to know about th",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Learning Disability",
    },
    {
      id: 6,
      userPrompt: "Duniya का highest रेल पुल and arch bridge कहाँ है?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Auto",
      domain: "General",
    },
    {
      id: 7,
      userPrompt:
        "Please explain photosynthesis in Gujarati and end with a",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Education",
    },
    {
      id: 8,
      userPrompt: "Indiavil எத்தனை யுபி பதிவு நுழைவுகள் உள்ளன?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Tamil",
      domain: "agriculture",
    },
    {
      id: 9,
      userPrompt:
        "I'm a deaf person and want to get COVID-19 vaccine info",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Healthcare",
    },
    {
      id: 10,
      userPrompt:
        "I am a transgender person and I want to know about th",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Learning Disability",
    },
    {
      id: 11,
      userPrompt: "Duniya का highest रेल पुल and arch bridge कहाँ है? Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quas.",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Auto",
      domain: "Learning Disability",
    },
    {
      id: 12,
      userPrompt:
        "Please explain photosynthesis in Gujarati and end with a",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "General",
    },
    {
      id: 13,
      userPrompt: "Indiavil எத்தனை யுபி பதிவு நுழைவுகள் உள்ளன?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Tamil",
      domain: "Education",
    },
    {
      id: 14,
      userPrompt:
        "I'm a deaf person and want to get COVID-19 vaccine info",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "agriculture",
    },
    {
      id: 15,
      userPrompt:
        "I am a transgender person and I want to know about th",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Learning Disability",
    },
    {
      id: 16,
      userPrompt: "Duniya का highest रेल पुल and arch bridge कहाँ है?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Auto",
      domain: "General",
    },
    {
      id: 17,
      userPrompt:
        "Please explain photosynthesis in Gujarati and end with a",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Education",
    },
    {
      id: 18,
      userPrompt: "Indiavil எத்தனை யுபி பதிவு நுழைவுகள் உள்ளன?",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "Tamil",
      domain: "agriculture",
    },
    {
      id: 19,
      userPrompt:
        "I'm a deaf person and want to get COVID-19 vaccine info",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Healthcare",
    },
    {
      id: 20,
      userPrompt:
        "I am a transgender person and I want to know about th",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Learning Disability",
    },
    {
      id: 21,
      userPrompt:
        "I am a transgender person and I want to know about th",
      systemPrompt: "You are an educational assistant for Indian school students",
      language: "English",
      domain: "Learning Disability",
    },
  ];

  const filteredPrompts = promptRows.filter(
    (p) =>
      p.userPrompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.language.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.domain.toLowerCase().includes(searchQuery.toLowerCase())
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
          <h1 className="text-4xl font-bold mb-8 text-center">Prompts</h1>

          <div className="flex gap-4 mb-6 ">
            <Select defaultValue="promptname">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="promptname">Prompt Name</SelectItem>
                <SelectItem value="domain">Domain</SelectItem>
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
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">User Prompt</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Language</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Domain</th>
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
                      <td className="p-2 truncate max-w-[650px] pr-8 mr-2">{row.userPrompt}</td>
                      <td className="p-2 ">{row.language}</td>
                      <td className="p-2 ">{row.domain}</td>
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
              + Add Prompt
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
            <DialogTitle className="sr-only">Prompt Details</DialogTitle>
          </DialogHeader>

          {selectedPrompt && (
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
              <div className="space-y-1">
                <Label className="text-base font-semibold">User Prompt</Label>
                <Textarea value={selectedPrompt.userPrompt} readOnly className="bg-muted min-h-[80px]" />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">System Prompt</Label>
                <Textarea value={selectedPrompt.systemPrompt} readOnly className="bg-muted min-h-[80px]" />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">language Name</Label>
                <Input value={selectedPrompt.language} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <Label className="text-base font-semibold">Domain Name</Label>
                <Input value={selectedPrompt.domain} readOnly className="bg-muted" />
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

      <PromptUpdateDialog
        prompt={updatePrompt}
        open={!!updatePrompt}
        onOpenChange={(open) => !open && setUpdatePrompt(null)}
      />

      <PromptAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </div>
  );
};

export default Prompts;


