import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";

interface PromptSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (prompt: string) => void;
  searchType: "userPrompt" | "response" | "llm";
}


export const PromptSearchDialog = ({
  open,
  onOpenChange,
  onSelect,
  searchType,
}: PromptSearchDialogProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [items, setItems] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch data from API
  useEffect(() => {
    if (!open) {
      setItems([]);
      setSearchQuery("");
      setError(null);
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Get the appropriate API endpoint based on searchType
        let endpoint: string;
        switch (searchType) {
          case "userPrompt":
            endpoint = API_ENDPOINTS.PROMPTS;
            break;
          case "response":
            endpoint = API_ENDPOINTS.RESPONSES;
            break;
          case "llm":
            endpoint = API_ENDPOINTS.LLM_PROMPTS;
            break;
          default:
            endpoint = API_ENDPOINTS.PROMPTS;
        }

        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        // Add auth token if available
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(endpoint, { headers });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        console.log("API Response for", searchType, ":", data);
        
        // Handle different response formats - could be array or object with items
        const itemsArray = Array.isArray(data) ? data : (data.items || data.data || []);
        
        // Extract text from items if they are objects, otherwise use as strings
        const extractedItems = itemsArray
          .map((item: any) => {
            if (typeof item === "string") {
              return item;
            }
            
            // Extract the appropriate field based on searchType
            let text: string | undefined;
            if (searchType === "userPrompt") {
              text = item.user_prompt;
            } else if (searchType === "response") {
              text = item.response_text;
            } else if (searchType === "llm") {
              // LLM prompts API returns 'prompt' field, not 'llm_prompt'
              text = item.prompt;
            }
            
            // Fallback to common field names if specific field not found
            if (!text) {
              text = item.text || item.prompt || item.response || item.content;
            }
            
            // If still no text, convert to string or return empty
            return text || "";
          })
          .filter((item: string) => item && item.trim() !== ""); // Filter out empty strings

        console.log("Extracted items:", extractedItems);
        setItems(extractedItems);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
        setItems([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [open, searchType]);

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
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <p className="text-sm italic">Loading...</p>
              </div>
            ) : error ? (
              <div className="flex-1 flex items-center justify-center text-destructive">
                <p className="text-sm italic">Error: {error}</p>
              </div>
            ) : filteredItems.length === 0 ? (
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
