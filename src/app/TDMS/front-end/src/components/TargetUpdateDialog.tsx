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
import { hasPermission } from "@/utils/permissions";


interface Target {
  target_id: number;
  target_name: string;
  target_type: string;
  target_description: string;
  target_url: string;
  domain_name: string;
  lang_list: string[];
  notes?: string;
}

interface TargetUpdateDialogProps {
  target: Target | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateSuccess?: () => void;
}

export default function TargetUpdateDialog({
  target,
  open,
  onOpenChange,
  onUpdateSuccess,
}: TargetUpdateDialogProps) {
  const { toast } = useToast();
  const [type, setType] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [domain, setDomain] = useState("");
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [targetTypes, setTargetTypes] = useState<string[]>([]);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingOptions, setIsFetchingOptions] = useState(false);

  const [currentUserRole, setCurrentUserRole] = useState<string>("");

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
      }

      if (domainsResponse.ok) {
        const domainsData = await domainsResponse.json();
        const domainNames = Array.isArray(domainsData)
          ? domainsData.map((d: any) => d.domain_name).filter(Boolean)
          : [];
        setDomainOptions(domainNames);
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
    } finally {
      setIsFetchingOptions(false);
    }
  }, []);

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
    if (open) {
      fetchOptions();
      fetchUserRole();
    }
  }, [open, fetchOptions]);

  useEffect(() => {
    if (target) {
      setType(target.target_type);
      setDescription(target.target_description);
      setUrl(target.target_url);
      setDomain(target.domain_name);
      setSelectedLanguages(target.lang_list || []);
      setNotes(target.notes || "");
    }
  }, [target]);

  const targetInitial: Target = target || {
    target_id: 0,
    target_name: "",
    target_type: "",
    target_description: "",
    target_url: "",
    domain_name: "",
    lang_list: [],
    notes: "",
  };

  const isChanged =
    type !== (targetInitial.target_type || "") ||
    description !== (targetInitial.target_description || "") ||
    url !== (targetInitial.target_url || "") ||
    domain !== (targetInitial.domain_name || "") ||
    selectedLanguages.join(",") !== (targetInitial.lang_list || []).join(",") ||
    notes !== (targetInitial.notes || "");

  const handleLanguageToggle = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang],
    );
  };

  const handleSubmit = async () => {

    if (!hasPermission(currentUserRole, "canUpdateTables") && !hasPermission(currentUserRole, "canUpdateRecords")) {
      toast({
        title: "Access Denied",
        description: "You don't have permission to update targets",
        variant: "destructive",
      });
      return;
    }

    if (!target?.target_id) {
      toast({
        title: "Error",
        description: "Target ID is missing",
        variant: "destructive",
      });
      return;
    }

    if (!description || !description.trim()) {
      toast({
        title: "Validation Error",
        description: "Description field is required",
        variant: "destructive",
      });
      return;
    }

    if (!url || !url.trim()) {
      toast({
        title: "Validation Error",
        description: "URL field is required",
        variant: "destructive",
      });
      return;
    }

    if (!type || !type.trim()) {
      toast({
        title: "Validation Error",
        description: "Type field is required",
        variant: "destructive",
      });
      return;
    }

    if (!domain || !domain.trim()) {
      toast({
        title: "Validation Error",
        description: "Domain field is required",
        variant: "destructive",
      });
      return;
    }

    if (selectedLanguages.length === 0) {
      toast({
        title: "Validation Error",
        description: "At least one language must be selected",
        variant: "destructive",
      });
      return;
    }

    if (!notes || !notes.trim()) {
      toast({
        title: "Validation Error",
        description: "Notes field is required",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // Send all fields to match backend expectations
      const updatePayload: any = {
        target_name: target.target_name,
        target_type: type || targetInitial.target_type,
        target_description: description || null,
        target_url: url || targetInitial.target_url,
        domain_name: domain || targetInitial.domain_name,
        lang_list:
          selectedLanguages.length > 0
            ? selectedLanguages
            : targetInitial.lang_list || [],
        notes: notes.trim() || null,
      };

      console.log("Updating target with payload:", updatePayload);
      console.log("Target ID:", target.target_id);

      const response = await fetch(
        API_ENDPOINTS.TARGET_UPDATE_V2(target.target_id),
        {
          method: "PUT",
          headers,
          body: JSON.stringify(updatePayload),
        },
      );

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          // Handle different error response formats
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // Pydantic validation errors
              errorMessage = errorData.detail
                .map((err: any) => {
                  if (typeof err === "string") return err;
                  if (err.msg)
                    return `${err.loc?.join(".") || "field"}: ${err.msg}`;
                  return JSON.stringify(err);
                })
                .join(", ");
            } else if (typeof errorData.detail === "string") {
              errorMessage = errorData.detail;
            } else {
              errorMessage = JSON.stringify(errorData.detail);
            }
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (parseError) {
          // If JSON parsing fails, try to get text
          try {
            const errorText = await response.text();
            errorMessage = errorText || errorMessage;
          } catch {
            // Keep default error message
          }
        }
        throw new Error(errorMessage);
      }

      toast({
        title: "Success",
        description: "Target updated successfully",
      });

      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      onOpenChange(false);
    } catch (error) {
      console.error("Error updating target:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to update target",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!target) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[90vh] overflow-y-auto"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="sr-only">Update Target</DialogTitle>
        </DialogHeader>
        <div className="overflow-y-auto flex-1  space-y-2 pb-5 p-1">
          <div className="flex items-center justify-center gap-2 pb-4">
            <Label className="text-base font-semibold">Target -</Label>
            <Label className="text-xl font-semibold text-primary hover:text-primary/90">
              {target.target_name}
            </Label>
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Description</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-muted min-h-[80px]"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4 pb-4">
            <div className="space-y-1 ">
              <Label className="text-base font-semibold">Type</Label>
              <Select
                value={type}
                onValueChange={setType}
                disabled={isFetchingOptions}
              >
                <SelectTrigger className="bg-muted capitalize">
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


            <div className="space-y-1">
              <Label className="text-base font-semibold">Domain</Label>
              <Select
                value={domain}
                onValueChange={setDomain}
                disabled={isFetchingOptions}
              >
                <SelectTrigger className="bg-muted capitalize">
                  <SelectValue
                    placeholder={
                      isFetchingOptions ? "Loading..." : "Select domain"
                    }
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
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">URL</Label>
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="bg-muted"
            />
          </div>
          <div className="space-y-1 pb-4">
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
                        id={`lang-${lang}`}
                        checked={selectedLanguages.includes(lang)}
                        onCheckedChange={() => handleLanguageToggle(lang)}
                      />
                      <label
                        htmlFor={`lang-${lang}`}
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
        </div>

        <div className="flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10">
          <Label className="text-base font-bold mr-2">Notes :</Label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
            required
            placeholder="Enter notes"
            disabled={
              !hasPermission(currentUserRole, "canUpdateTables") &&
              !hasPermission(currentUserRole, "canUpdateRecords")
            }
          />
          <Button
            onClick={handleSubmit}
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!isChanged || !notes.trim() || isLoading ||
              (!hasPermission(currentUserRole, "canUpdateTables") &&
                !hasPermission(currentUserRole, "canUpdateRecords"))
            }
          >
            {isLoading ? "Updating..." : "Submit"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { TargetUpdateDialog };
