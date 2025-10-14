import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";

interface PromptSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (prompt: string) => void;
  searchType: "userPrompt" | "response" | "llm";
}

const samplePrompts = [
  "What is the recommended pesticide application rate for a new, disease-resistant tomato variety introduced last year, based on the latest agricultural regulations in tamilnadu?",
  "What is 17*23?",
  "What are the best ways to invest my money in India?",
  "What's the weather like in Berlin right now, and will it rain in 2 hours?",
  "What is the capital of France?",
  "What idiot came up with photosynthesis? Explain it like I am five, and don't be dumb.",
  "What factors influence crop yield variability?",
  "What are the causes of climate change?",
  "What is the Pythagorean theorem used for?",
  "What are steps for soil preparation before planting rice?",
  "What is a database index and why is it important?",
  "What do people like to have in summer?",
];

const sampleResponses = [
  "The product of 17 multiplied by 23 is 391. This is calculated by multiplying 17 by 20 (which is 340) and then adding 17 multiplied by 3 (which is 51), resulting in 340 + 51 = 391.",
  "Paris is the capital of France.",
  "To prepare soil for rice planting, first clear the field of debris, then plow to a depth of 15-20cm, and ensure proper water management for paddy cultivation.",
];

export const PromptSearchDialog = ({
  open,
  onOpenChange,
  onSelect,
  searchType,
}: PromptSearchDialogProps) => {
  const [searchQuery, setSearchQuery] = useState("");

  const items = searchType === "userPrompt" ? samplePrompts : sampleResponses;
  
  const filteredItems = items.filter((item) =>
    item.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="sr-only">Search Prompts</DialogTitle>
          {/* <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4"
            onClick={() => onOpenChange(false)}
          >
            <X className="w-5 h-5" />
          </Button> */}
        </DialogHeader>

        <div className="space-y-4 pt-4">
          <div className="relative">
            <Input
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pr-10"
            />
            <Search className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          </div>

          <div className="space-y-2 max-h-[50vh] min-h-[50vh] overflow-y-auto flex flex-col">
            {filteredItems.length === 0 ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <p className="text-sm italic">No results found.</p>
              </div>
            ) : (
              filteredItems.map((item, index) => (
                <button
                  key={index}
                  onClick={() => onSelect(item)}
                  className="w-full text-left p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <p className="text-sm">{item}</p>
                </button>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
