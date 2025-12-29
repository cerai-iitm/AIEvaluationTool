import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X, Check, AlertCircle } from "lucide-react";
import {
  PromptSearchDialog,
  PromptSearchSelection,
  PromptSearchType,
} from "./PromptSearchDialog";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { hasPermission } from "@/utils/permissions";
import { set } from "date-fns";

interface TestCaseAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface Strategy {
  strategy_id: number | null;
  strategy_name: string | null;
  requires_llm_prompt: boolean | null;
}

const responseTypes = [
  {value: "GT", label: "Ground Truth"},
  {value: "GTDesc", label: "Ground Truth Description"},
  {value: "NA", label: "Not Applicable"}
]

export const TestCaseAddDialog = ({
  open,
  onOpenChange,
  onSuccess,
}: TestCaseAddDialogProps) => {
  const { toast } = useToast();
  const [testCaseName, setTestCaseName] = useState("");
  const [isNameAvailable, setIsNameAvailable] = useState<boolean | null>(null);
  const [isCheckingName, setIsCheckingName] = useState(false);
  const [userPrompts, setUserPrompts] = useState("");
  const [systemPrompts, setSystemPrompts] = useState("");
  const [responseText, setResponseText] = useState("");
  const [llmPrompt, setLlmPrompt] = useState("");
  const [strategy, setStrategy] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isFetchingStrategies, setIsFetchingStrategies] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searchType, setSearchType] = useState<PromptSearchType>("userPrompt");

  // Language and Domain states
  const [language, setLanguage] = useState("");
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingLanguages, setIsFetchingLanguages] = useState(false);
  const [domain, setDomain] = useState("");
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [isFetchingDomains, setIsFetchingDomains] = useState(false);

  // Response Type and ResponseLanguage
  const [responseType, setResponseType] = useState("");
  const [typeOptions, setTypeOptions] = useState<string[]>([])
  const [isFetchingTypes, setIsFetchingTypes] = useState(false);
  const [responseLanguage, setResponseLanguage] = useState("");
  const [responseLanguageOptions, setResponseLanguageOptions] = useState<string[]>([]);

  //show response details state - control visibility of response type and response language
  const [showRequestDetails, setShowRequestDetails] = useState(false);
  

  // Show details state - controls visibility of System Prompts, Domain, and Language
  const [showDetails, setShowDetails] = useState(false);
  const [domainSelectOpen, setDomainSelectOpen] = useState(false);
  const [languageSelectOpen, setLanguageSelectOpen] = useState(false);

  

  const [errors, setErrors] = useState({
    domain: false,
    language: false,
    responseType: false,
    responseLanguage: false,
    systemPrompts: false,
    llmPrompt: false
  })


  // Fetch current user role and strategies from API
  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const response = await fetch(API_ENDPOINTS.CURRENT_USER, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCurrentUserRole(userData.role || "");
        }
      } catch (error) {
        console.error("Error fetching user role:", error);
      }
    };

    // Fetch language from API
    const fetchLanguages = async () => {
      setIsFetchingLanguages(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.LANGUAGES_V2, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (Array.isArray(data)) {
          const langNames = data
            .map((lang: any) => lang?.lang_name)
            .filter((name: string | null | undefined): name is string => Boolean(name));
          setLanguageOptions(langNames);
          // if (langNames.length > 0 && !language) {
          //   setLanguage(langNames[0]);
          // }
        } else {
          console.error("Unexpected languages data format:", data);
          toast({
            title: "Error",
            description: "Failed to load languages",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error fetching languages:", error);
        toast({
          title: "Error",
          description: "Failed to load languages from server",
          variant: "destructive",
        });
      } finally {
        setIsFetchingLanguages(false);
      }
    };

    // Fetch Domain from API
    const fetchDomains = async () => {
      setIsFetchingDomains(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.DOMAINS_V2, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (Array.isArray(data)) {
          const domainNames = data
            .map((dom: any) => dom?.domain_name)
            .filter((name: string | null | undefined): name is string => Boolean(name));
          setDomainOptions(domainNames);
          // if (domainNames.length > 0 && !domain) {
          //   setDomain(domainNames[0]);
          // }
        } else {
          console.error("Unexpected domains data format:", data);
          toast({
            title: "Error",
            description: "Failed to load domains",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error fetching domains:", error);
        toast({
          title: "Error",
          description: "Failed to load domains from server",
          variant: "destructive",
        });
      } finally {
        setIsFetchingDomains(false);
      }
    };

    // Fetch strategies from API
    const fetchStrategies = async () => {
      setIsFetchingStrategies(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(API_ENDPOINTS.STRATEGIES_V2, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (Array.isArray(data)) {
          setStrategies(data);
        } else {
          console.error("Unexpected strategies data format:", data);
          toast({
            title: "Error",
            description: "Failed to load strategies",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error fetching strategies:", error);
        toast({
          title: "Error",
          description: "Failed to load strategies from server",
          variant: "destructive",
        });
      } finally {
        setIsFetchingStrategies(false);
      }
    };

    if (open) {
      fetchUserRole();
      fetchStrategies();
      fetchLanguages();
      fetchDomains();
    } else {
      // Reset states when dialog closes
      setShowDetails(false);
      setFocusedField(null);
      setDomainSelectOpen(false);
      setLanguageSelectOpen(false);
      setErrors({
        domain: false,
        language: false,
        responseType: false,
        responseLanguage: false,
        systemPrompts: false,
        llmPrompt: false,
      });
    }
  }, [open, toast]);

  // Check test case name availability against database
  useEffect(() => {
    const checkNameAvailability = async () => {
      const name = testCaseName.trim();
      if (!name) {
        setIsNameAvailable(null);
        return;
      }

      setIsCheckingName(true);
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        //const response = await fetch(API_ENDPOINTS.TEST_CASES, { headers });
        const response = await fetch(API_ENDPOINTS.TESTCASES_V2, { headers });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const testCases = Array.isArray(data) ? data : [];
        
        // Check if any test case has the same name (case-insensitive)
        const nameExists = testCases.some(
          (tc: any) => 
            tc.testcase_name && 
            tc.testcase_name.toLowerCase().trim() === name.toLowerCase().trim()
        );

        setIsNameAvailable(!nameExists);
      } catch (error) {
        console.error("Error checking name availability:", error);
        setIsNameAvailable(null); // Set to null on error to not show incorrect status
      } finally {
        setIsCheckingName(false);
      }
    };

    // Debounce the check
    const timeout = setTimeout(() => {
      checkNameAvailability();
    }, 500);

    return () => clearTimeout(timeout);
  }, [testCaseName]);

  // const handleSearchClick = (type: "userPrompt" | "response" | "llm") => {
  //   setSearchType(type);
  //   setSearchDialogOpen(true);
  // };

  const isAdded = (
    userPrompts && strategy && testCaseName
    
  )

  const handleSelectPrompt = (selection: PromptSearchSelection) => {
    switch (selection.type) {
      case "userPrompt":
        setUserPrompts(selection.userPrompt);
        // setSystemPrompts(selection.systemPrompt ?? "");
        break;
      case "systemPrompt":
        setSystemPrompts(selection.systemPrompt);
        // if (selection.userPrompt) {
        //   setUserPrompts(selection.userPrompt);
        // }
        break;
      case "response":
        setResponseText(selection.responseText);
        break;
      case "llm":
        setLlmPrompt(selection.llmPrompt);
        break;
      default:
        break;
    }
    setSearchDialogOpen(false);
    setFocusedField(null);
  };

  const [focusedField, setFocusedField] = useState<
    | null
    | "userPrompt"
    | "systemPrompt"
    | "response"
    | "llm"
    | "domain"
    | "language"
    | "responseType"
    | "responseLanguage"
  >(null);

  const handleSearchClick = (type: PromptSearchType) => {
    setSearchType(type);
    setSearchDialogOpen(true);
    if (type === "userPrompt" || type === "response" || type === "llm") {
      setFocusedField(type);
    } else {
      setFocusedField(null);
    }
  };

  // Check if the selected strategy requires LLM prompt
  const showLLMPrompt = strategy && strategies.some(
    (s) => s.strategy_name === strategy && s.requires_llm_prompt === true
  );

  const handleSubmit = async () => {
    // Check if user has permission to create
    if (!hasPermission(currentUserRole, "canCreateTables") && 
        !hasPermission(currentUserRole, "canCreateRecords")) {
      toast({
        title: "Access Denied",
        description: "You don't have permission to create test cases",
        variant: "destructive",
      });
      return;
    }

    // Validate required fields
    if (!testCaseName.trim()) {
      toast({
        title: "Validation Error",
        description: "Test case name is required",
        variant: "destructive",
      });
      return;
    }

    if (!userPrompts.trim()) {
      toast({
        title: "Validation Error",
        description: "User prompt is required",
        variant: "destructive",
      });
      return;
    }

    if (!strategy) {
      toast({
        title: "Validation Error",
        description: "Strategy is required",
        variant: "destructive",
      });
      return;
    }

    if (!systemPrompts.trim()) {
      toast({
        title: "Validation Error",
        description: "System prompt is required",
        variant: "destructive",
      });
      setErrors(prev => ({ ...prev, systemPrompts: true }));
      setShowDetails(true);
      setShowRequestDetails(false);
      setFocusedField("systemPrompt");
      return;
    }

    if (!domain.trim()) {
      toast({
        title: "Validation Error",
        description: "Prompt Domain is required",
        variant: "destructive",
      });
      setErrors(prev => ({ ...prev, domain: true }));
      setShowDetails(true);
      setShowRequestDetails(false);
      setFocusedField("domain");
      return;
    }

    if (!language.trim()) {
      toast({
        title: "Validation Error",
        description: "Prompt Language is required",
        variant: "destructive",
      });
      setErrors(prev => ({ ...prev, language: true }));
      setShowDetails(true);
      setShowRequestDetails(false);
      setFocusedField("language");
      return;
    }

    // if (!responseText.trim()) {
    //   toast({
    //     title: "Validation Error",
    //     description: "Response text is required",
    //     variant: "destructive",
    //   });
    //   return;
    // }

    // if response text is available means response type and response language is required
    if (responseText.trim()) {
      if (!responseType) {
        toast({
          title: "Validation Error",
          description: "Response type is required",
          variant: "destructive",
        });
        setErrors(prev => ({ ...prev, responseType: true }));
        setShowRequestDetails(true);
        setShowDetails(false);
        setFocusedField("responseType");
        return;

      }
      if (!responseLanguage) {
        toast({
          title: "Validation Error",
          description: "Response language is required",
          variant: "destructive",
        });
        setErrors(prev => ({ ...prev, responseLanguage: true }));
        setShowRequestDetails(true);
        setShowDetails(false);
        setFocusedField("responseLanguage");
        return;
      }
    }

    if (!llmPrompt.trim() && showLLMPrompt) {
      toast({
        title: "Validation Error",
        description: "LLM prompt is required",
        variant: "destructive",
      });
      setErrors(prev => ({ ...prev, llmPrompt: true }));
      setShowDetails(false);
      setShowRequestDetails(false);
      setFocusedField("llm");
      return;
    }






    // Check if name is available
    if (isNameAvailable === false) {
      toast({
        title: "Validation Error",
        description:
          "Test case name already exists. Please choose a different name.",
        variant: "destructive",
      });
      return;
    }

    if (isCheckingName) {
      toast({
        title: "Please wait",
        description: "Checking name availability...",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const payload = {
        testcase_name: testCaseName.trim(),
        strategy_name: strategy,
        user_prompt: userPrompts.trim(),
        system_prompt: systemPrompts.trim() || null,
        response_text: responseText.trim() || null,
        response_type: responseType || null,
        response_lang: responseLanguage || null,
        language_name: language.trim(),
        domain_name: domain.trim(),
        llm_judge_prompt:
          showLLMPrompt && llmPrompt.trim() ? llmPrompt.trim() : null,
      };

      console.log("Creating test case:", payload);
      const response = await fetch(API_ENDPOINTS.TESTCASE_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("Test case created successfully:", data);

      toast({
        title: "Success",
        description: `Test case "${testCaseName}" created successfully`,
      });

      // Reset form
      setTestCaseName("");
      setUserPrompts("");
      setSystemPrompts("");
      setResponseText("");
      setLlmPrompt("");
      setStrategy("");
      setNotes("");
      setLanguage("");
      setDomain("");
      setIsNameAvailable(null);
      setShowDetails(false);
      setFocusedField(null);

      setShowRequestDetails(false);
      setResponseType("");
      setResponseLanguage("");
      setErrors({
        domain: false,
        language: false,
        responseType: false,
        responseLanguage: false,
        systemPrompts: false,
        llmPrompt: false,
      });

      // Close dialog
      onOpenChange(false);

      // setHighlightedRowId(data.testcase_id);

      // Trigger refresh in parent component
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error("Error creating test case:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create test case",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="sr-only">Add Test Case</DialogTitle>
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
            <div className="space-y-1">
              <Label className="text-base font-semibold">Test Case</Label>
              <div className="relative">
                <Input
                  placeholder="Enter new test case name"
                  value={testCaseName}
                  onChange={(e) => setTestCaseName(e.target.value)}
                  onFocus={() => {
                    setShowDetails(false);
                    setShowRequestDetails(false);
                  }}
                  className={`bg-muted pr-24 ${
                    isNameAvailable === false ? "border-destructive" : ""
                  }`}
                  required
                  disabled={isSubmitting}
                />
                {isCheckingName && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-muted-foreground">
                    <span className="text-sm">Checking...</span>
                  </div>
                )}
                {!isCheckingName && isNameAvailable === true && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-green-600">
                    <Check className="w-4 h-4" />
                    <span className="text-sm font-medium">Available</span>
                  </div>
                )}
                {!isCheckingName && isNameAvailable === false && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-destructive">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">Taken</span>
                  </div>
                )}
              </div>
            </div>
                <hr />
            <div className="space-y-1 pb-2">
              {/* <div className="flex items-center justify-between"> */}
                <Label className="text-base font-semibold">Prompt</Label>
              {/* </div> */}
              <div className="space-y-1">
                <Label className="text-sm font-semibold">User Prompt</Label>
                <div className="relative">
                  <Textarea
                    value={userPrompts}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "75px",
                      overflowY: "auto"
                    }}
                    placeholder="Enter user prompt or Search "
                    onChange={(e) => setUserPrompts(e.target.value)}
                    onFocus={() => {
                      setFocusedField("userPrompt");
                      setShowRequestDetails(false);
                    }}
                    onBlur={() => setFocusedField(null)}
                    //onClick={() => {setShowDetails((prev) => !prev); setFocusedField("userPrompt")}}
                    onClick={() => {setShowDetails(true); setShowRequestDetails(false)}}
                    className="bg-muted min-h-[73px] pr-10"
                    required
                  />
                  { focusedField === "userPrompt" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-2"
                      onMouseDown = {e => e.preventDefault()}
                      onClick={() => handleSearchClick("userPrompt")}
                      tabIndex = {-1} //not focusable, only clickable
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              {showDetails && (
                <>
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">System prompt</Label>
                    <div className="relative">
                      <Textarea
                        value={systemPrompts}
                        style = {{
                          height: '${height}px',
                          maxHeight: "120px",
                          minHeight: "40px",
                          overflowY: "auto"
                        }}
                        placeholder="Enter system prompt or Search "
                        onChange={(e) => {
                          setSystemPrompts(e.target.value);
                          if (errors.systemPrompts && e.target.value.trim()) {
                            setErrors(prev => ({ ...prev, systemPrompts: false }));
                          }
                        }}
                        onFocus={() => setFocusedField("systemPrompt")}
                        onBlur={() => setFocusedField(null)}
                        className={`bg-muted min-h-[73px] pr-10 ${
                          errors.systemPrompts ? 'border-red-500 ring-2 ring-red-200' : ''
                        }`}
                        required
                        onClick = {() => {
                          setShowDetails(true);
                          setShowRequestDetails(false);
                        }}
                        
                      />
                      { focusedField === "systemPrompt" && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute right-2 top-2"
                          onMouseDown = {e => e.preventDefault()}
                          onClick={() => handleSearchClick("systemPrompt")}
                          tabIndex = {-1} // not focusable, only clickable
                        >
                          <Search className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-sm font-semibold">Domain</Label>
                      <Select
                        value={domain}
                        onValueChange={(value) => {
                          setDomain(value);
                          if (errors.domain && value.trim()) {
                            setErrors(prev => ({ ...prev, domain: false }));
                          }
                        }}
                        onOpenChange={setDomainSelectOpen}
                        disabled={isFetchingDomains}
                        
                      >
                        <SelectTrigger className={`
                          ${errors.domain ? 'bg-red-50 border-red-500 ring-2 ring-red-200' : 'bg-muted capitalize'}
                          focus-visible:ring-ring focus-visible:ring-2
                        `}>
                          <SelectValue placeholder={isFetchingDomains ? "Loading domains..." : "Select Domain"}/>
                        </SelectTrigger>
                        <SelectContent className="bg-popover max-h-[300px]">
                          {domainOptions.length === 0 && !isFetchingDomains ? (
                            <SelectItem value="" disabled>No domains available</SelectItem>
                          ) : (
                            domainOptions.map((dom) => (
                              <SelectItem key={dom} value={dom} className="capitalize">
                                {dom}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-sm font-semibold">Language</Label>
                      <Select
                        value={language}
                        onValueChange={(value) => {
                          setLanguage(value);
                          if (errors.language && value.trim()) {
                            setErrors(prev => ({ ...prev, language: false }));
                          }
                        }}
                        // onOpenChange={setLanguageSelectOpen}
                        disabled={isFetchingLanguages}
                      >
                        <SelectTrigger
                          className={`
                            ${errors.language ? 'bg-red-50 border-red-500 ring-2 ring-red-200': 'bg-muted capitalize'}
                            focus-visible:ring-ring focus-visible:ring-2
                            `}
                        >
                          <SelectValue
                            placeholder={
                              isFetchingLanguages ? "Loading languages..." : "Select Language"
                            }
                          />
                        </SelectTrigger>
                        <SelectContent className="bg-popover max-h-[300px]">
                          {languageOptions.length === 0 && !isFetchingLanguages ? (
                            <SelectItem value="" disabled>No languages available</SelectItem>
                          ) : (
                            languageOptions.map((lang) => (
                              <SelectItem key={lang} value={lang} className="capitalize">{lang}</SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="line"></div>  
              <hr />
            <div className="space-y-1 pb-2">
              <div className="space-y-2">
                <Label className="text-base font-semibold">Response</Label>
                <div className="relative">
                  <Textarea
                    value={responseText}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "75px",
                      overflowY: "auto"
                    }}
                    placeholder="Enter response or Search "
                    className="bg-muted min-h-[73px] pr-10"
                    onChange={(e) => setResponseText(e.target.value)}
                    onFocus={() => {
                      setFocusedField("response");
                      setShowDetails(false);
                    }}
                    onBlur={() => setFocusedField(null)}
                    onClick={() => {
                      setShowRequestDetails(true);
                      setShowDetails(false);
                    }}
                  />
                  { focusedField === "response" && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onMouseDown = {e => e.preventDefault()}
                    onClick={() => handleSearchClick("response")}
                    tabIndex = {-1}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                  )}
                </div>
              </div>
              {showRequestDetails && (
                <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-base font-semibold">Response Type</Label>
                    <Select 
                      value={responseType} 
                      onValueChange={(value) => {
                        setResponseType(value);
                        if (errors.responseType && value) {
                          setErrors(prev => ({ ...prev, responseType: false }));
                        }
                      }}
                    >
                      <SelectTrigger className={`
                        ${errors.responseType ? 'bg-red-50 border-red-500 ring-2 ring-red-200' : 'bg-muted'}
                        focus-visible:ring-ring focus-visible:ring-2 placeholder:text-muted-foreground
                      `}>
                        <SelectValue className="placeholder:text-muted-foreground" placeholder="Select response type" />
                      </SelectTrigger>
                      <SelectContent className="bg-popover max-h-[300px]">
                        {responseTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-base font-semibold">Language</Label>
                    <Select
                      value={responseLanguage}
                      onValueChange={(value) => {
                        setResponseLanguage(value);
                        if (errors.responseLanguage && value) {
                          setErrors(prev => ({ ...prev, responseLanguage: false }));
                        }
                      }}
                      disabled={isFetchingLanguages}
                    >
                      <SelectTrigger className={`
                        ${errors.responseLanguage ? 'bg-red-50 border-red-500 ring-2 ring-red-200' : 'bg-muted capitalize'}
                        focus-visible:ring-ring focus-visible:ring-2
                      `}>
                        <SelectValue
                          className="placeholder:blur placeholder:text-muted-foreground/50 placeholder:italic placeholder:text-sm placeholder:capitalize capitalize"  
                          placeholder={
                            isFetchingLanguages
                              ? "Loading languages..."
                              : "Select language"
                          }
                        />
                      </SelectTrigger>
                      <SelectContent className="bg-popover max-h-[300px]">
                        {languageOptions.length === 0 && !isFetchingLanguages ? (
                          <SelectItem value="" disabled>
                            No languages available
                          </SelectItem>
                        ) : (
                          languageOptions.map((lang) => (
                            <SelectItem key={lang} value={lang} className="capitalize">
                              {lang}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                </>
              )}
            </div>
              <hr />
            <div className="space-y-1">
              <Label className="text-base font-semibold">Strategy</Label>
              <Select 
                value={strategy} 
                onValueChange={setStrategy}
                onOpenChange={(open) => {
                  if (open) {
                    setShowDetails(false);
                    setShowRequestDetails(false);
                  }
                }}
                disabled={isFetchingStrategies}
              >
                <SelectTrigger className={`bg-muted`}>
                  <SelectValue className="placeholder:blur" placeholder={isFetchingStrategies ? "Loading strategies..." : "Select strategy"} />
                </SelectTrigger>
                <SelectContent className="bg-popover max-h-[300px]">
                  {strategies
                    .filter((s) => s.strategy_name != null)
                    .map((s) => (
                      <SelectItem key={s.strategy_name} value={s.strategy_name!}>
                        {s.strategy_name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {showLLMPrompt && (
              <div className="space-y-2">
                <Label className="text-base font-semibold">LLM Prompt</Label>
                <div className="relative">
                  <Textarea
                    value={llmPrompt}
                    style = {{
                      height: '${height}px',
                      maxHeight: "120px",
                      minHeight: "75px",
                      overflowY: "auto"
                    }}
                    placeholder="Enter prompt or Search"
                    // readOnly = {llmPrompt === "" || llmPrompt === null || llmPrompt === "none"}
                    // className="bg-muted min-h-[73px] pr-10"
                    className={`bg-muted min-h-[73px] pr-10 ${
                          errors.llmPrompt ? 'border-red-500 ring-2 ring-red-200' : ''
                    }`}
                    required
                    // onChange={(e) => setLlmPrompt(e.target.value)}
                    onChange={(e) => {
                          setLlmPrompt(e.target.value);
                          if (errors.llmPrompt && e.target.value) {
                            setErrors(prev => ({ ...prev, llmPrompt: false }));
                          }
                        }}
                    onFocus={() => {
                      setFocusedField("llm");
                      setShowDetails(false);
                      setShowRequestDetails(false);
                    }}
                    onBlur={() => setFocusedField(null)}
                    onClick={() => {
                      setShowDetails(false);
                      setShowRequestDetails(false);
                    }}
                  />
                  { focusedField === "llm" && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2"
                    onClick={() => handleSearchClick("llm")}
                    onMouseDown = {e => e.preventDefault()}
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
              <Label className="text-base font-semibold mr-2">Notes</Label>
              <Input
                placeholder="Enter Notes"
                type="text"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                onFocus={() => {
                  setShowDetails(false);
                  setShowRequestDetails(false);
                }}
                className="bg-muted rounded px-4 py-1 mr-4 w-96"
                required
              />
              <button
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleSubmit}
                disabled={
                  isSubmitting || 
                  isCheckingName || 
                  isNameAvailable === false || 
                  !isAdded || 
                  !notes ||
                  (!hasPermission(currentUserRole, "canCreateTables") && 
                   !hasPermission(currentUserRole, "canCreateRecords"))
                }
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <PromptSearchDialog
        open={searchDialogOpen}
        onOpenChange={setSearchDialogOpen}
        onSelect={handleSelectPrompt}
        searchType={searchType}
      />
    </>
  );
};
