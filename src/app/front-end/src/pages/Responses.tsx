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
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ResponseUpdateDialog } from "@/components/ResponseUpdateDialog";
import { ResponseAddDialog } from "@/components/ResponseAddDialog";

interface Response {
  id: number;
  name: string;
  responseText: string;
  responseType: string;
  language: string;
  userPrompts: string;
  systemPrompts: string;
  notes: string;
}

const Responses = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedResponse, setSelectedResponse] = useState<Response | null>(null);
  const [updateResponse, setUpdateResponse] = useState<Response | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const totalItems = 288;
  const itemsPerPage = 100;

  // Sample data based on the images
  const responses: Response[] = [
    {
      id: 1,
      name: "Response 1",
      responseText: "I'm a farmer in Tamil Nadu, India, Currently growing rice during the Kharif season. I want to implement an effective crop rotation plan and integrated pest management strategy for the next three years. Can you suggest suitable crop sequences and pest control",
      responseType: "Ground Truth",
      language: "English",
      userPrompts: "What is the recommended pesticide application rate for a new, disease-resistant tomato variety introduced last year, based on the latest agricultural regulations in tamilnadu?",
      systemPrompts: "You are an AI assistant that not only provides the answer but explains your reasoning in a clear manner.",
      notes: "Random message for update and add"
    },
    {
      id: 2,
      name: "Response 2",
      responseText: "दुनिया का सबसे ऊँचा रेल पुल और आर्च ब्रिज भारत में चेनाब ब्रिज (Chenab Bridge)",
      responseType: "Ground Truth",
      language: "Hindi",
      userPrompts: "Tell me about the highest railway bridge in India",
      systemPrompts: "You are an AI assistant that provides information about Indian infrastructure.",
      notes: ""
    },
    {
      id: 3,
      name: "Response 3",
      responseText: "Gujarati: ફોટોસિન્થેસિસ થી ખેતર પ્રક્રિયા છે માં... Summary in English:",
      responseType: "Ground Truth",
      language: "Gujarati",
      userPrompts: "Explain the process of photosynthesis in Gujarati",
      systemPrompts: "You are an AI assistant that explains scientific concepts in regional languages.",
      notes: ""
    },
    {
      id: 4,
      name: "Response 4",
      responseText: "இந்தியாவில் முக்கியமான 3 பயிர் பருவங்கள் உள்ளன:",
      responseType: "Ground Truth",
      language: "Tamil",
      userPrompts: "What are the main crop seasons in India?",
      systemPrompts: "You are an AI assistant that provides agricultural information in Tamil.",
      notes: ""
    },
    {
      id: 5,
      name: "Response 5",
      responseText: "Accessible information on COVID-19 vaccines for deaf individuals",
      responseType: "Ground Truth",
      language: "English",
      userPrompts: "How can deaf individuals access COVID-19 vaccine information?",
      systemPrompts: "You are an AI assistant that provides accessible health information.",
      notes: ""
    },
    {
      id: 6,
      name: "Response 6",
      responseText: "Yes, as an AIDS patient, you can get a full-body scan (like a full-body MRI or CT scan)",
      responseType: "Ground Truth",
      language: "English",
      userPrompts: "Can AIDS patients get full-body scans?",
      systemPrompts: "You are an AI assistant that provides medical information and advice.",
      notes: ""
    },
    // Add more sample data as needed
    ...Array.from({ length: 10 }, (_, i) => ({
      id: i + 7,
      name: `Response ${i + 7}`,
      responseText: `Sample response text for response ${i + 7}. This is placeholder content that represents the actual response data.`,
      responseType: "Ground Truth",
      language: ["English", "Hindi", "Tamil", "Gujarati"][i % 4],
      userPrompts: `Sample user prompt for response ${i + 7}`,
      systemPrompts: `Sample system prompt for response ${i + 7}`,
      notes: ""
    }))
  ];

  const filteredResponses = responses.filter((response) =>
    response.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    response.responseText.toLowerCase().includes(searchQuery.toLowerCase()) ||
    response.language.toLowerCase().includes(searchQuery.toLowerCase()) ||
    response.responseType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>
      

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8">
          <h1 className="text-4xl font-bold mb-8 text-center">Responses</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="responsename">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="responsename">Response Name</SelectItem>
                <SelectItem value="responseid">Response ID</SelectItem>
                <SelectItem value="responsetype">Response Type</SelectItem>
                <SelectItem value="language">Language</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-md"
            />

            <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {currentPage === 1 ? "00" : `${(currentPage - 1) * itemsPerPage + 1}`} of {totalItems}
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
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="border-b-2">
                <tr>
                  <th className="text-left p-4 font-semibold">Response ID</th>
                  <th className="text-left p-4 font-semibold">Response Text</th>
                  <th className="text-left p-4 font-semibold">Language</th>
                  <th className="text-left p-4 font-semibold">Response Type</th>
                </tr>
              </thead>
              <tbody>
                {filteredResponses.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((response) => (
                  <tr
                    key={response.id}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => setSelectedResponse(response)}
                  >
                    <td className="p-2">{response.id}</td>
                    <td className="p-2 max-w-md truncate">{response.responseText}</td>
                    <td className="p-2">{response.language}</td>
                    <td className="p-2">{response.responseType === "Ground Truth" ? "GT" : response.responseType}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6">
            <Button 
              className="bg-primary hover:bg-primary/90"
              onClick={() => setAddDialogOpen(true)}
            >
              + Add Response
            </Button>
          </div>
        </div>
      </main>

      <Dialog open={!!selectedResponse} onOpenChange={() => setSelectedResponse(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Response Details</DialogTitle>
          </DialogHeader>

          {selectedResponse && (
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label>Response Text</Label>
                <Textarea
                  value={selectedResponse.responseText}
                  readOnly
                  className="bg-muted min-h-[100px]"
                />
              </div>

              <div className="space-y-2">
                <Label>Response Type</Label>
                <Input value={selectedResponse.responseType} readOnly className="bg-muted" />
              </div>

              <div className="space-y-2">
                <Label>Language</Label>
                <Input value={selectedResponse.language} readOnly className="bg-muted" />
              </div>

              <div className="space-y-2">
                <Label>User Prompts</Label>
                <Textarea
                  value={selectedResponse.userPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label>System Prompts</Label>
                <Textarea
                  value={selectedResponse.systemPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Input value={selectedResponse.notes} readOnly className="bg-muted" />
              </div>

              <div className="flex justify-center gap-4 pt-4">
                <Button variant="destructive">Delete</Button>
                <Button 
                  className="bg-primary hover:bg-primary/90"
                  onClick={() => {
                    setUpdateResponse(selectedResponse);
                    setSelectedResponse(null);
                  }}
                >
                  Update
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <ResponseUpdateDialog
        response={updateResponse}
        open={!!updateResponse}
        onOpenChange={(open) => !open && setUpdateResponse(null)}
      />

      <ResponseAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </div>
  );
};

export default Responses;
