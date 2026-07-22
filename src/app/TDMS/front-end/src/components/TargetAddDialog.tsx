import { useState, useEffect, useCallback } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { NameCharacterCounter } from "@/components/NameCharacterCounter";
import {
  isNameOverCharacterLimit,
  isNameUsingAllowedCharacters,
  NAME_ALLOWED_CHARACTERS_MESSAGE,
} from "@/utils/nameValidation";
import XPathConfigurationEditor from "@/components/XPathConfigurationEditor";

interface TargetAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface DomainOption {
  domain_name?: string;
}

interface LanguageOption {
  lang_name?: string;
}

type XPathPages = Record<string, Record<string, string>>;

const WHATSAPP_XPATH_TEMPLATE_KEY = "whatsapp_web";
const WEB_APP_XPATH_TEMPLATE_KEY = "cpgrams";

const normalizeTargetType = (value: string) => value.trim().toLowerCase();

const getXPathTemplateKeyForTargetType = (targetType: string) => {
  const normalizedType = normalizeTargetType(targetType);
  if (normalizedType === "whatsapp") return WHATSAPP_XPATH_TEMPLATE_KEY;
  if (normalizedType === "webapp") return WEB_APP_XPATH_TEMPLATE_KEY;
  return "";
};

const toXPathPages = (value: unknown): XPathPages =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as XPathPages)
    : {};

const toBlankXPathPages = (pages: XPathPages): XPathPages =>
  Object.fromEntries(
    Object.entries(pages).map(([pageName, elements]) => [
      pageName,
      Object.fromEntries(
        Object.keys(elements || {}).map((elementName) => [elementName, ""]),
      ),
    ]),
  );

const getXPathFieldCount = (pages: XPathPages) =>
  Object.values(pages).reduce(
    (count, elements) => count + Object.keys(elements || {}).length,
    0,
  );

const getMissingXPathCount = (pages: XPathPages) =>
  Object.values(pages).reduce(
    (count, elements) =>
      count +
      Object.values(elements || {}).filter((xpath) => !xpath.trim()).length,
    0,
  );

export default function TargetAddDialog({
  open,
  onOpenChange,
  onSuccess,
}: TargetAddDialogProps) {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [domain, setDomain] = useState("");
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [targetTypes, setTargetTypes] = useState<string[]>([]);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingOptions, setIsFetchingOptions] = useState(false);
  const [xpathPages, setXpathPages] = useState<XPathPages>({});

  // Fetch options from API
  const fetchOptions = useCallback(async () => {
    setIsFetchingOptions(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const [typesResponse, domainsResponse, languagesResponse] =
        await Promise.all([
          fetch(API_ENDPOINTS.TARGET_TYPES, { headers }),
          fetch(API_ENDPOINTS.DOMAINS_V2, { headers }),
          fetch(API_ENDPOINTS.LANGUAGES_V2, { headers }),
        ]);

      if (typesResponse.ok) {
        const typesData = await typesResponse.json();
        setTargetTypes(Array.isArray(typesData) ? typesData : []);
        if (Array.isArray(typesData) && typesData.length > 0) {
          setType(typesData[0]);
        }
      }

      if (domainsResponse.ok) {
        const domainsData = await domainsResponse.json();
        const domainNames = Array.isArray(domainsData)
          ? domainsData
              .map((d: DomainOption) => d.domain_name)
              .filter((domainName): domainName is string => Boolean(domainName))
          : [];
        setDomainOptions(domainNames);
        if (domainNames.length > 0) {
          setDomain(domainNames[0]);
        }
      }

      if (languagesResponse.ok) {
        const languagesData = await languagesResponse.json();
        const langNames = Array.isArray(languagesData)
          ? languagesData
              .map((l: LanguageOption) => l.lang_name)
              .filter((langName): langName is string => Boolean(langName))
          : [];
        setLanguageOptions(langNames);
      }
    } catch (error) {
      console.error("Error fetching options:", error);
      toast({
        title: "Error",
        description: "Failed to load options",
        variant: "destructive",
      });
    } finally {
      setIsFetchingOptions(false);
    }
  }, [toast]);

  useEffect(() => {
    if (open) {
      fetchOptions();
    } else {
      // Reset form when dialog closes
      setName("");
      setType("");
      setDescription("");
      setUrl("");
      setDomain("");
      setSelectedLanguages([]);
      setNotes("");
      setXpathPages({});
    }
  }, [open, fetchOptions]);

  const handleLanguageToggle = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const hasInvalidNameCharacters =
    name.trim().length > 0 && !isNameUsingAllowedCharacters(name);
  const isNameInvalid =
    isNameOverCharacterLimit(name) || hasInvalidNameCharacters;

  const isFormValid =
    name.trim() &&
    !isNameInvalid &&
    type &&
    description.trim() &&
    url.trim() &&
    domain &&
    selectedLanguages.length > 0 &&
    notes.trim();

  const selectedTargetType = normalizeTargetType(type);
  const requiresXPathConfig =
    selectedTargetType === "whatsapp" || selectedTargetType === "webapp";
  const xpathFieldCount = getXPathFieldCount(xpathPages);
  const missingXPathCount = getMissingXPathCount(xpathPages);
  const isXPathConfigComplete =
    xpathFieldCount > 0 && missingXPathCount === 0;
  const canSubmit =
    Boolean(isFormValid) && (!requiresXPathConfig || isXPathConfigComplete);

  const buildHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }, []);

  const fetchXPathTemplateForType = useCallback(
    async (targetType: string, headers: HeadersInit): Promise<XPathPages> => {
      const templateKey = getXPathTemplateKeyForTargetType(targetType);
      if (!templateKey) return {};

      const response = await fetch(API_ENDPOINTS.TARGET_XPATHS_V2(templateKey), {
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to load XPath template");
      }

      const data = await response.json();
      const templatePages = toXPathPages(data?.pages);
      return normalizeTargetType(targetType) === "webapp"
        ? toBlankXPathPages(templatePages)
        : templatePages;
    },
    [],
  );

  useEffect(() => {
    if (!open || !type) {
      setXpathPages({});
      return;
    }

    let isCancelled = false;
    fetchXPathTemplateForType(type, buildHeaders())
      .then((templatePages) => {
        if (!isCancelled) {
          setXpathPages(templatePages);
        }
      })
      .catch((error) => {
        if (!isCancelled) {
          console.error("Error loading XPath template:", error);
          setXpathPages({});
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [buildHeaders, fetchXPathTemplateForType, open, type]);

  const fetchWebAppXPathTemplate = async (
    headers: HeadersInit,
  ): Promise<XPathPages> => {
    const response = await fetch(
      API_ENDPOINTS.TARGET_XPATHS_V2(WEB_APP_XPATH_TEMPLATE_KEY),
      { headers },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          "Target created, but failed to load the WebApp XPath template",
      );
    }

    const data = await response.json();
    return toBlankXPathPages(toXPathPages(data?.pages));
  };

  const seedWebAppXPaths = async (
    targetName: string,
    headers: HeadersInit,
  ) => {
    const seedPages =
      Object.keys(xpathPages).length > 0
        ? xpathPages
        : await fetchWebAppXPathTemplate(headers);

    const response = await fetch(API_ENDPOINTS.TARGET_XPATH_SEED_V2(targetName), {
      method: "POST",
      headers,
      body: JSON.stringify(seedPages),
    });

    if (response.status === 404) {
      const fallbackResponse = await fetch(API_ENDPOINTS.TARGET_XPATHS_V2(targetName), {
        method: "PUT",
        headers,
        body: JSON.stringify({ pages: seedPages }),
      });

      if (fallbackResponse.ok) {
        return;
      }

      const fallbackErrorData = await fallbackResponse.json().catch(() => ({}));
      throw new Error(
        fallbackErrorData.detail ||
          "Target created, but failed to save the WebApp XPath config",
      );
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          "Target created, but failed to seed the WebApp XPath config",
      );
    }
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast({
        title: "Validation Error",
        description: "Target name is required",
        variant: "destructive",
      });
      return;
    }

    if (isNameOverCharacterLimit(name)) {
      toast({
        title: "Validation Error",
        description: "Target name must be 40 characters or fewer",
        variant: "destructive",
      });
      return;
    }

    if (!isNameUsingAllowedCharacters(name)) {
      toast({
        title: "Validation Error",
        description: NAME_ALLOWED_CHARACTERS_MESSAGE,
        variant: "destructive",
      });
      return;
    }

    if (!type) {
      toast({
        title: "Validation Error",
        description: "Target type is required",
        variant: "destructive",
      });
      return;
    }

    if (!url.trim()) {
      toast({
        title: "Validation Error",
        description: "URL is required",
        variant: "destructive",
      });
      return;
    }

    if (!description.trim()) {
      toast({
        title: "Validation Error",
        description: "Target description is required",
        variant: "destructive",
      });
      return;
    }

    if (!domain) {
      toast({
        title: "Validation Error",
        description: "Domain is required",
        variant: "destructive",
      });
      return;
    }

    if (!selectedLanguages.length) {
      toast({
        title: "Validation Error",
        description: "At least one language is required",
        variant: "destructive",
      });
      return;
    }

    if (!notes.trim()) {
      toast({
        title: "Validation Error",
        description: "Notes field is required",
        variant: "destructive",
      });
      return;
    }

    if (requiresXPathConfig && !isXPathConfigComplete) {
      toast({
        title: "Validation Error",
        description:
          xpathFieldCount === 0
            ? "XPath configuration is required"
            : "All XPath fields are required",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const headers = buildHeaders();

      const payload = {
        target_name: name.trim(),
        target_type: type,
        target_description: description.trim() || null,
        target_url: url.trim(),
        domain_name: domain,
        target_languages: selectedLanguages,
        notes: notes.trim() || null,
      };

      const response = await fetch(API_ENDPOINTS.TARGET_CREATE_V2, {
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
      console.log("Target created successfully:", data);

      const createdTargetName =
        typeof data?.target_name === "string" ? data.target_name : name.trim();

      if (normalizeTargetType(type) === "webapp") {
        await seedWebAppXPaths(createdTargetName, headers);
      }

      toast({
        title: "Success",
        description: "Target created successfully",
      });

      // Reset form
      setName("");
      setType("");
      setDescription("");
      setUrl("");
      setDomain("");
      setSelectedLanguages([]);
      setNotes("");

      // Close dialog
      onOpenChange(false);

      // Trigger refresh in parent component
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error("Error creating target:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to create target",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="sr-only">Add Target</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general">
          <TabsList className="grid w-full grid-cols-2 sm:w-[420px]">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="xpaths">XPath Config</TabsTrigger>
          </TabsList>

          <TabsContent value="general">
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label className="text-base font-semibold">Target</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter target name"
                  required
                  aria-invalid={isNameInvalid}
                  className={`bg-muted ${isNameInvalid ? "border-red-500" : ""}`}
                />
                <NameCharacterCounter value={name} />
                {hasInvalidNameCharacters && (
                  <p className="text-xs font-medium text-red-600">
                    {NAME_ALLOWED_CHARACTERS_MESSAGE}.
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">Description</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-muted min-h-[80px]"
                  placeholder="Enter description..."
                />
              </div>

              <div className="grid gap-4 pb-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label className="text-base font-semibold">Type</Label>
                  <Select
                    value={type}
                    onValueChange={setType}
                    disabled={isFetchingOptions}
                  >
                    <SelectTrigger className="bg-muted">
                      <SelectValue
                        placeholder={isFetchingOptions ? "Loading..." : "Select type"}
                      />
                    </SelectTrigger>
                    <SelectContent className="bg-popover max-h-[300px]">
                      {targetTypes.length === 0 && !isFetchingOptions ? (
                        <SelectItem value="" disabled>
                          No types available
                        </SelectItem>
                      ) : (
                        targetTypes.map((t) => (
                          <SelectItem key={t} value={t}>
                            {t}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-base font-semibold">Domain</Label>
                  <Select
                    value={domain}
                    onValueChange={setDomain}
                    disabled={isFetchingOptions}
                  >
                    <SelectTrigger className="bg-muted capitalize">
                      <SelectValue
                        placeholder={isFetchingOptions ? "Loading..." : "Select domain"}
                      />
                    </SelectTrigger>
                    <SelectContent className="bg-popover max-h-[300px]">
                      {domainOptions.length === 0 && !isFetchingOptions ? (
                        <SelectItem value="" disabled>
                          No domains available
                        </SelectItem>
                      ) : (
                        domainOptions.map((d) => (
                          <SelectItem key={d} value={d} className="capitalize">
                            {d}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">URL</Label>
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Enter URL"
                  required
                  className="bg-muted"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-base font-semibold">Languages</Label>
                <div className="bg-muted p-4 rounded-md max-h-[110px] overflow-y-auto">
                  {isFetchingOptions ? (
                    <div className="text-sm text-muted-foreground">
                      Loading languages...
                    </div>
                  ) : languageOptions.length === 0 ? (
                    <div className="text-sm text-muted-foreground">
                      No languages available
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {languageOptions.map((lang) => (
                        <div key={lang} className="flex items-center space-x-2 capitalize">
                          <Checkbox
                            id={`lang-add-${lang}`}
                            checked={selectedLanguages.includes(lang)}
                            onCheckedChange={() => handleLanguageToggle(lang)}
                          />
                          <label
                            htmlFor={`lang-add-${lang}`}
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                          >
                            {lang}
                          </label>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-center">
                <Label className="text-base font-semibold">Notes</Label>
                <Input
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter notes"
                  className="bg-gray-200 rounded px-4 py-1 sm:mr-4 sm:max-w-md"
                  required
                />

                <Button
                  className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
                  onClick={handleSubmit}
                  disabled={!canSubmit || isSubmitting}
                >
                  {isSubmitting ? "Submitting..." : "Submit"}
                </Button>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="xpaths" className="pt-4">
            <XPathConfigurationEditor
              applicationName={name}
              targetType={type}
              onPagesChange={setXpathPages}
              open={open}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
