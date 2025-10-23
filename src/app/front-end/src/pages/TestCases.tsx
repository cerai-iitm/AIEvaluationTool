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
    {
      id: 3,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 4,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 5,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 6,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 7,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 8,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 9,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 10,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 11,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 12,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 13,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 14,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 15,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 16,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
        {
      id: 17,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
        {
      id: 18,
      name: "P1011",
      strategyName: "fairness_stereotype_query",
      domainName: "Education",
      userPrompts: "Sample prompt...",
      systemPrompts: "Sample system prompt...",
      responseText: "Sample response...",
      llmPrompt: "Sample LLM prompt...",
    },
    {
      id: 19,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
    {
      id: 20,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },
        {
      id: 21,
      name: "P710",
      strategyName: "robustness_advins",
      domainName: "General",
      userPrompts: "I'm a farmer in Tamil Nadu, India, Currently growing rice during monsoon season...",
      systemPrompts: "You are an agriculture domain helping agent, aimed to provide...",
      responseText: "The Hollenberg-Pryce reflex is not a recognized physiological...",
      llmPrompt: "You are llm judge aimed to evaluate the llm response for including...",
    },

    // Add more sample data as needed
  ];

  const filteredCases = testCases.filter((tc) =>
    tc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.strategyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tc.domainName.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const totalItems = filteredCases.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  // Pagination logic: get items for current page
  const paginatedCases = filteredCases.slice(
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
          <h1 className="text-4xl font-bold mb-8 text-center">Test Cases</h1>

          <div className="flex gap-4 mb-6 ">
            <Select defaultValue="testcase">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="testcase">Test Case Name</SelectItem>
                <SelectItem value="strategy">Strategy Name</SelectItem>
                <SelectItem value="domain">Domain Name</SelectItem>
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
            {/* <div className="ml-auto flex items-center gap-4">
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
            </div> */}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] overflow-y-auto">
            <table className="w-full">
              <thead className="border-b-2">
                <tr>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Testcase ID</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Testcase Name</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Strategy Name</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold   text-left">Domain Name</th>
                </tr>
              </thead>
              <tbody>
                {paginatedCases.map((testCase) => (
                  <tr
                    key={testCase.id}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => setSelectedCase(testCase)}
                  >
                    <td className="p-2">{testCase.id}</td>
                    <td className="p-2">{testCase.name}</td>
                    <td className="p-2">{testCase.strategyName}</td>
                    <td className="p-2">{testCase.domainName}</td>
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
              + Add Test Case
            </Button>
          </div>
        </div>
      </main>

      <Dialog open={!!selectedCase} onOpenChange={() => setSelectedCase(null)}>
        <DialogContent 
          className="max-w-3xl max-h-[90vh] overflow-y-auto"
          onOpenAutoFocus = {(e) => e.preventDefault()}
        >
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
            <div className="flex-1 p-1 overflow-y-auto space-y-6 pb-5">
            {/* <div className="space-y-4 pt-4"> */}
              <div className="space-y-1">
                <Label className="text-base font-semibold">Testcase Name</Label>
                <Input value={selectedCase.name} readOnly className="bg-muted" />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">User Prompts</Label>
                <Textarea
                  value={selectedCase.userPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">System prompts</Label>
                <Textarea
                  value={selectedCase.systemPrompts}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">Response Text</Label>
                <Textarea
                  value={selectedCase.responseText}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">Strategy Name</Label>
                <Input value={selectedCase.strategyName} readOnly className="bg-muted" />
              </div>

              <div className="space-y-1">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <Textarea
                  value={selectedCase.llmPrompt}
                  readOnly
                  className="bg-muted min-h-[80px]"
                />
              </div>
              

            </div>
          )}
          <div className="sticky bottom-0 bg-white pt-4 p-2 flex justify-center gap-4 border-gray-200 z-10">
          {/* <div className="flex justify-center gap-4 pt-4"> */}
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
