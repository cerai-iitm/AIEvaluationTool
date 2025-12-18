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

export type PromptSearchType = "userPrompt" | "systemPrompt" | "response" | "llm";

export type PromptSearchSelection =
  | {
      type: "userPrompt";
      promptId?: number | null;
      userPrompt: string;
      // systemPrompt?: string | null;
      // language?: string | null;
      // domain?: string | null;
      raw?: unknown;
    }
  | {
      type: "systemPrompt";
      promptId?: number | null;
      systemPrompt: string;
      // userPrompt?: string | null;
      // language?: string | null;
      // domain?: string | null;
      raw?: unknown;
    }
  | {
      type: "response";
      responseId?: number | null;
      promptId?: number | null;
      responseText: string;
      raw?: unknown;
    }
  | {
      type: "llm";
      promptId?: number | null;
      llmPrompt: string;
      language?: string | null;
      raw?: unknown;
    };

interface PromptSearchItem {
  id: string;
  displayPrimary: string;
  // displaySecondary?: string;
  searchIndex: string;
  selection: PromptSearchSelection;
}

interface PromptSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (selection: PromptSearchSelection) => void;
  searchType: PromptSearchType;
}

const normalizeString = (value: unknown): string => {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
};

export const PromptSearchDialog = ({
  open,
  onOpenChange,
  onSelect,
  searchType,
}: PromptSearchDialogProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [items, setItems] = useState<PromptSearchItem[]>([]);
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
            endpoint = API_ENDPOINTS.USER_PROMPTS_V2;
            break;
          case "systemPrompt":
            endpoint = API_ENDPOINTS.SYSTEM_PROMPTS_V2;
            break;
          case "response":
            endpoint = API_ENDPOINTS.RESPONSES_V2;
            break;
          case "llm":
            endpoint = API_ENDPOINTS.LLMPROMPTS_V2;
            break;
          default:
            endpoint = API_ENDPOINTS.PROMPTS_V2;
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

        // Handle different response formats - could be array or object with items/data
        const itemsArray: any[] = Array.isArray(data)
          ? data
          : data?.items || data?.data || [];

        const mappedItems: PromptSearchItem[] = itemsArray
          .map((rawItem, index): PromptSearchItem | null => {
            const promptId =
              rawItem?.prompt_id ??
              rawItem?.promptId ??
              rawItem?.id ??
              null;

            if (searchType === "userPrompt") {
              const userPrompt =
                normalizeString(rawItem?.user_prompt) ||
                normalizeString(rawItem?.userPrompt) ||
                normalizeString(rawItem?.prompt);
              const systemPrompt =
                normalizeString(rawItem?.system_prompt) ||
                normalizeString(rawItem?.systemPrompt);

              if (!userPrompt.trim() && !systemPrompt.trim()) {
                return null;
              }

              // const language =
              //   rawItem?.language ??
              //   rawItem?.lang_name ??
              //   rawItem?.lang ??
              //   rawItem?.langName ??
              //   null;
              // const domain =
              //   rawItem?.domain ??
              //   rawItem?.domain_name ??
              //   rawItem?.domainName ??
              //   null;

              const displayPrimary =
                userPrompt.trim() || "(No user prompt text)";
              // const displaySecondary = systemPrompt.trim()
              //   ? systemPrompt
              //   : undefined;
              const searchIndex = [
                userPrompt,
                systemPrompt,
                // language,
                // domain,
              ]
                .filter(Boolean)
                .map((value) => value.toString().toLowerCase())
                .join(" ");

              return {
                id: `userPrompt-${promptId ?? index}`,
                displayPrimary,
                // displaySecondary,
                searchIndex,
                selection: {
                  type: "userPrompt",
                  promptId: typeof promptId === "number" ? promptId : null,
                  userPrompt,
                  // systemPrompt: systemPrompt || null,
                  // language,
                  // domain,
                  raw: rawItem,
                },
              };
            }

            if (searchType === "systemPrompt") {
              const systemPrompt =
                normalizeString(rawItem?.system_prompt) ||
                normalizeString(rawItem?.systemPrompt);
              const userPrompt =
                normalizeString(rawItem?.user_prompt) ||
                normalizeString(rawItem?.userPrompt);

              // if (!systemPrompt.trim() && !userPrompt.trim()) {
              //   return null;
              // }

              // const language =
              //   rawItem?.language ??
              //   rawItem?.lang_name ??
              //   rawItem?.lang ??
              //   rawItem?.langName ??
              //   null;
              // const domain =
              //   rawItem?.domain ??
              //   rawItem?.domain_name ??
              //   rawItem?.domainName ??
              //   null;

              const displayPrimary =
                systemPrompt.trim() || "(No system prompt text)";
              // const displaySecondary = userPrompt.trim()
              //   ? userPrompt
              //   : undefined;
              const searchIndex = [
                systemPrompt,
                userPrompt,
                // language,
                // domain,
              ]
                .filter(Boolean)
                .map((value) => value.toString().toLowerCase())
                .join(" ");

              return {
                id: `systemPrompt-${promptId ?? index}`,
                displayPrimary,
                // displaySecondary,
                searchIndex,
                selection: {
                  type: "systemPrompt",
                  promptId: typeof promptId === "number" ? promptId : null,
                  systemPrompt,
                  // userPrompt: userPrompt || null,
                  // language,
                  // domain,
                  raw: rawItem,
                },
              };
            }

            if (searchType === "response") {
              const responseText =
                normalizeString(rawItem?.response_text) ||
                normalizeString(rawItem?.response) ||
                normalizeString(rawItem?.text);

              if (!responseText.trim()) {
                return null;
              }

              const responseId =
                rawItem?.response_id ??
                rawItem?.responseId ??
                rawItem?.id ??
                null;
              const associatedUserPrompt =
                normalizeString(rawItem?.user_prompt) ||
                normalizeString(rawItem?.userPrompt);
              const associatedSystemPrompt =
                normalizeString(rawItem?.system_prompt) ||
                normalizeString(rawItem?.systemPrompt);

              const searchIndex = [
                responseText,
                associatedUserPrompt,
                associatedSystemPrompt,
              ]
                .filter(Boolean)
                .map((value) => value.toString().toLowerCase())
                .join(" ");

              return {
                id: `response-${responseId ?? index}`,
                displayPrimary: responseText,
                // displaySecondary: associatedUserPrompt
                //   ? `User: ${associatedUserPrompt}`
                //   : undefined,
                searchIndex,
                selection: {
                  type: "response",
                  responseId: typeof responseId === "number" ? responseId : null,
                  promptId: typeof promptId === "number" ? promptId : null,
                  responseText,
                  raw: rawItem,
                },
              };
            }

            // searchType === "llm"
            if ( searchType === "llm") {
              
            
              const llmPrompt =
                normalizeString(rawItem?.llmjudgeprompt_name) ||
                normalizeString(rawItem?.prompt) ||
                normalizeString(rawItem?.llm_prompt) ||
                normalizeString(rawItem?.text);

              const promptId =
                rawItem?.llmjudgeprompt_id ??
                rawItem?.llmPromptId ??
                rawItem?.id ??
                null;

              if (!llmPrompt.trim()) {
                return null;
              }

              const language =
                rawItem?.language ??
                rawItem?.lang_name ??
                rawItem?.lang ??
                rawItem?.langName ??
                null;

              const searchIndex = [llmPrompt, promptId]
                .filter(Boolean)
                .map((value) => value.toString().toLowerCase())
                .join(" ");

              return {
                id: `llm-${promptId ?? index}`,
                displayPrimary: llmPrompt,
                // displaySecondary: language
                //   ? `Language: ${language}`
                //   : undefined,
                searchIndex,
                selection: {
                  type: "llm",
                  promptId: typeof promptId === "number" ? promptId : null,
                  llmPrompt,
                  language,
                  raw: rawItem,
                },
              };
            }
          })
          .filter(Boolean) as PromptSearchItem[];

        setItems(mappedItems);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
        setItems([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [open, searchType]);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredItems =
    normalizedQuery.length === 0
      ? items
      : items.filter((item) => item.searchIndex.includes(normalizedQuery));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="sr-only">Search Prompts</DialogTitle>
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
              filteredItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelect(item.selection);
                    onOpenChange(false);
                  }}
                  className="w-full text-left p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <p className="text-sm font-medium">{item.displayPrimary}</p>
                  {/* {item.displaySecondary ? (
                    <p className="text-xs text-muted-foreground mt-1">
                      {item.displaySecondary}
                    </p>
                  ) : null} */}
                </button>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
