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
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";

interface TargetAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

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
          ? domainsData.map((d: any) => d.domain_name).filter(Boolean)
          : [];
        setDomainOptions(domainNames);
        if (domainNames.length > 0) {
          setDomain(domainNames[0]);
        }
      }

      if (languagesResponse.ok) {
        const languagesData = await languagesResponse.json();
        const langNames = Array.isArray(languagesData)
          ? languagesData.map((l: any) => l.lang_name).filter(Boolean)
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
    }
  }, [open, fetchOptions]);

  const handleLanguageToggle = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const isFormValid =
    name.trim() && type && url.trim() && domain && notes.trim();

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast({
        title: "Validation Error",
        description: "Target name is required",
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
        target_name: name.trim(),
        target_type: type,
        target_description: description.trim() || null,
        target_url: url.trim(),
        domain_name: domain,
        target_languages: selectedLanguages,
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
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="sr-only">Add Target</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label className="text-base font-semibold">Target Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter target name"
              required
              className="bg-muted"
            />
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

          <div className="grid grid-cols-2 gap-4 pb-4">
            <div className="space-y-2">
              <Label className="text-base font-semibold">Target Type</Label>
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
              <Label className="text-base font-semibold">Domain Name</Label>
              <Select
                
                value={domain}
                onValueChange={setDomain}
                disabled={isFetchingOptions}
              >
                <SelectTrigger className= "bg-muted capitalize">
                  <SelectValue placeholder= {isFetchingOptions ? "Loading..." : "Select domain"}/>
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
                    <div key={lang} className="flex items-center space-x-2">
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

          <div className="flex justify-center items-center p-4 ">
            <Label className="text-base font-semibold mr-2">Notes</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Enter notes"
              className="bg-gray-200 rounded px-4 py-1 mr-4 "
              required
            />

            <Button
              className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
              onClick={handleSubmit}
              disabled={!isFormValid || isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Submit"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
