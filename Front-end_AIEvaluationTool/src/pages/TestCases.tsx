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
import { TestCaseUpdateDialog } from "@/components/TestCaseUpdateDialog";
import { TestCaseAddDialog } from "@/components/TestCaseAddDialog";

interface TestCase {
  id: number;
  name: string;
  strategyName: string;
  domainName: string;
  userPrompts: string;
  systemPrompts: string;
  responseText: string;
  llmPrompt: string;
}

const TestCases = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCase, setSelectedCase] = useState<TestCase | null>(null);
  const [updateCase, setUpdateCase] = useState<TestCase | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const totalItems = 1635;
  const itemsPerPage = 100;

  // Sample data
  const testCases: TestCase[] = [
    {
      id: 1,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 2,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    // Add more sample data as needed
  ];

  const filteredCases = testCases.filter((tc) =>
    tc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.strategyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.domainName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 bg-background">
        <div className="p-8">
          <h1 className="text-4xl font-bold mb-8 text-center">Test Cases</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="testcase">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="testcase">Testcase Name</SelectItem>
                <SelectItem value="strategy">Strategy Name</SelectItem>
                <SelectItem value="domain">Domain Name</SelectItem>
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
                1 - {itemsPerPage} of {totalItems}
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
                  <th className="text-left p-4 font-semibold">Testcase ID</th>
                  <th className="text-left p-4 font-semibold">Testcase Name</th>
                  <th className="text-left p-4 font-semibold">Strategy Name</th>
                  <th className="text-left p-4 font-semibold">Domain Name</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((testCase) => (
                  <tr
                    key={testCase.id}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => setSelectedCase(testCase)}
                  >
                    <td className="p-4">{testCase.id}</td>
                    <td className="p-4">{testCase.name}</td>
                    <td className="p-4">{testCase.strategyName}</td>
                    <td className="p-4">{testCase.domainName}</td>
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
              + Add Test Case
            </Button>
          </div>
        </div>
      </main>

      <Dialog open={!!selectedCase} onOpenChange={() => setSelectedCase(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Test Case Details</DialogTitle>
            {/* <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-4"
              onClick={() => setSelectedCase(null)}
            >
              <X className="w-5 h-5" />
            </Button> */}
          </DialogHeader>

          {selectedCase && (
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label>Testcase Name</Label>
                <Input value={selectedCase.name} readOnly className="bg-muted" />
              </div>

              <div className="space-y-2">
                <Label>User Prompts</Label>
                <Textarea
                  value={selectedCase.userPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label>System prompts</Label>
                <Textarea
                  value={selectedCase.systemPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label>Response Text</Label>
                <Textarea
                  value={selectedCase.responseText}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label>Strategy Name</Label>
                <Input value={selectedCase.strategyName} readOnly className="bg-muted" />
              </div>

              <div className="space-y-2">
                <Label>LLM Prompt</Label>
                <Textarea
                  value={selectedCase.llmPrompt}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="flex justify-center gap-4 pt-4">
                <Button variant="destructive">Delete</Button>
                <Button 
                  className="bg-primary hover:bg-primary/90"
                  onClick={() => {
                    setUpdateCase(selectedCase);
                    setSelectedCase(null);
                  }}
                >
                  Update
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <TestCaseUpdateDialog
        testCase={updateCase}
        open={!!updateCase}
        onOpenChange={(open) => !open && setUpdateCase(null)}
      />

      <TestCaseAddDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </div>
  );
};

export default TestCases;
