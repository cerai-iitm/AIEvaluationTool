import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
import { hasPermission } from "@/utils/permissions";
import XPathConfigurationEditor from "@/components/XPathConfigurationEditor";
import TargetCredentialsEditor, {
  type TargetCredentials,
} from "@/components/TargetCredentialsEditor";


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

type XPathPages = Record<string, Record<string, string>>;

const emptyCredentials: TargetCredentials = {
  username: "",
  password: "",
};

const normalizeTargetType = (value: string) => value.trim().toLowerCase();

const areCredentialsComplete = (credentials: TargetCredentials) =>
  Boolean(credentials.username.trim() && credentials.password.trim());

const hasAnyCredentials = (credentials: TargetCredentials) =>
  Boolean(credentials.username.trim() || credentials.password.trim());

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

export default function TargetUpdateDialog({
  target,
  open,
  onOpenChange,
  onUpdateSuccess,
}: TargetUpdateDialogProps) {
  const { toast } = useToast();
  const [name, setName] = useState("");
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
  const [credentials, setCredentials] = useState<TargetCredentials>(emptyCredentials);
  const [xpathPages, setXpathPages] = useState<XPathPages>({});
  const [activeTab, setActiveTab] = useState("general");
  const [hasXPathChanges, setHasXPathChanges] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  const [discardConfirmOpen, setDiscardConfirmOpen] = useState(false);
  const [xpathInitialSignature, setXpathInitialSignature] = useState<string | null>(null);
  const [credentialInitialSignature, setCredentialInitialSignature] = useState<string | null>(null);

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
      setName(target.target_name);
      setType(target.target_type);
      setDescription(target.target_description);
      setUrl(target.target_url);
      setDomain(target.domain_name);
      setSelectedLanguages(target.lang_list || []);
      setNotes(target.notes || "");
      setCredentials(emptyCredentials);
      setCredentialInitialSignature(null);
      setXpathPages({});
      setHasXPathChanges(false);
      setXpathInitialSignature(null);
      setActiveTab("general");
      setDiscardConfirmOpen(false);
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

  const sortedLanguages = (languages: string[] = []) =>
    [...languages].sort((a, b) => a.localeCompare(b)).join(",");

  const hasGeneralChanges = (
    name.trim() !== (targetInitial.target_name) ||
    type.trim() !== (targetInitial.target_type || "") ||
    description.trim() !== (targetInitial.target_description || "") ||
    url.trim() !== (targetInitial.target_url || "") ||
    domain.trim() !== (targetInitial.domain_name || "") ||
    sortedLanguages(selectedLanguages) !== sortedLanguages(targetInitial.lang_list || [])
  );

  const selectedTargetType = normalizeTargetType(type);
  const isWebAppTarget = selectedTargetType === "webapp";
  const hasCredentialChanges =
    credentialInitialSignature !== null &&
    JSON.stringify(credentials) !== credentialInitialSignature;
  const hasChanges = hasGeneralChanges || hasXPathChanges || hasCredentialChanges;

  const requiresXPathConfig = selectedTargetType === "whatsapp" || isWebAppTarget;
  const showXPathTab = requiresXPathConfig;
  const xpathFieldCount = getXPathFieldCount(xpathPages);
  const missingXPathCount = getMissingXPathCount(xpathPages);
  const isXPathConfigComplete =
    xpathFieldCount > 0 && missingXPathCount === 0;

  useEffect(() => {
    if (!open) return;

    if (!showXPathTab && activeTab === "xpaths") {
      setActiveTab("general");
      return;
    }

    if (!isWebAppTarget) {
      setCredentials(emptyCredentials);
      setCredentialInitialSignature(null);
      if (activeTab === "credentials") {
        setActiveTab("general");
      }
    }
  }, [activeTab, isWebAppTarget, open, showXPathTab]);

  useEffect(() => {
    if (
      open &&
      isWebAppTarget &&
      normalizeTargetType(targetInitial.target_type) !== "webapp" &&
      credentialInitialSignature === null
    ) {
      setCredentialInitialSignature(JSON.stringify(emptyCredentials));
    }
  }, [credentialInitialSignature, isWebAppTarget, open, targetInitial.target_type]);

  const handleLanguageToggle = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang],
    );
  };

  const handleCredentialsChange = useCallback((nextCredentials: TargetCredentials) => {
    setCredentials(nextCredentials);
    setCredentialInitialSignature((current) => current ?? JSON.stringify(nextCredentials));
  }, []);

  const handleXPathPagesChange = useCallback((pages: XPathPages) => {
    setXpathPages(pages);
    setXpathInitialSignature((current) => {
      const nextSignature = JSON.stringify(pages);
      if (current === null) {
        setHasXPathChanges(false);
        return nextSignature;
      }

      setHasXPathChanges(nextSignature !== current);
      return current;
    });
  }, []);

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

  const saveTargetXPaths = async (
    targetName: string,
    headers: HeadersInit,
  ) => {
    const response = await fetch(
      API_ENDPOINTS.TARGET_XPATHS_UPDATE_BY_TARGET_V2(targetName),
      {
        method: "POST",
        headers,
        body: JSON.stringify(xpathPages),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save XPath configuration");
    }
  };

  const hasUnsavedChanges = Boolean(
    hasChanges ||
      hasCredentialChanges,
  );

  const handleDialogOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      onOpenChange(true);
      return;
    }

    if (isLoading) {
      return;
    }

    if (hasUnsavedChanges) {
      setDiscardConfirmOpen(true);
      return;
    }

    onOpenChange(false);
  };

  const discardChangesAndClose = () => {
    setDiscardConfirmOpen(false);
    onOpenChange(false);
  };

  const saveTargetCredentials = async (
    targetName: string,
    headers: HeadersInit,
  ) => {
    const payload = JSON.stringify({
      username: credentials.username.trim(),
      password: credentials.password.trim(),
    });
    let response = await fetch(API_ENDPOINTS.TARGET_CREDENTIALS_V2(targetName), {
      method: "POST",
      headers,
      body: payload,
    });

    if (response.status === 405) {
      response = await fetch(API_ENDPOINTS.TARGET_CREDENTIALS_V2(targetName), {
        method: "PUT",
        headers,
        body: payload,
      });
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save credentials");
    }
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

    // if (requiresXPathConfig && !isXPathConfigComplete) {
    //   toast({
    //     title: "Validation Error",
    //     description:
    //       xpathFieldCount === 0
    //         ? "XPath configuration is required"
    //         : "All XPath fields are required",
    //     variant: "destructive",
    //   });
    //   return;
    // }

    // if (isWebAppTarget && !areCredentialsComplete(credentials)) {
    //   toast({
    //     title: "Validation Error",
    //     description: "Username and password are required",
    //     variant: "destructive",
    //   });
    //   return;
    // }

    if (!hasChanges) {
      toast({
        title: "Validation Error",
        description: "Change at least one field before submitting",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      if (hasXPathChanges) {
        await saveTargetXPaths(target.target_name.trim(), buildHeaders());
      }

      const headers = buildHeaders();

      // Send all fields to match backend expectations
      const updatePayload: any = {
        target_name: name || targetInitial.target_name,
        target_type: type || targetInitial.target_type,
        target_description: description || null,
        target_url: url || targetInitial.target_url,
        domain_name: domain || targetInitial.domain_name,
        lang_list:
          selectedLanguages.length > 0
            ? selectedLanguages
            : targetInitial.lang_list || [],
        xpath_config_changed: hasXPathChanges,
        xpath_application_name: target.target_name,
        credential_config_changed: hasCredentialChanges,
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

      const updatedTargetName = target.target_name.trim();
      if (
        isWebAppTarget &&
        hasCredentialChanges &&
        hasAnyCredentials(credentials)
      ) {
        await saveTargetCredentials(updatedTargetName, headers);
      }

      toast({
        title: "Success",
        description: "Target updated successfully",
      });

      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      discardChangesAndClose();
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
    <>
    <Dialog open={open} onOpenChange={handleDialogOpenChange}>
      <DialogContent
        className="max-w-5xl h-[80vh] overflow-y-auto"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="sr-only">Update Target</DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="max-w-5xl h-[65vh] overflow-y-auto">
          <TabsList
            className={`grid w-full ${
              isWebAppTarget
                ? "grid-cols-3 sm:w-[620px]"
                : showXPathTab
                  ? "grid-cols-2 sm:w-[420px]"
                  : "grid-cols-1 sm:w-[220px]"
            }`}
          >
            <TabsTrigger value="general">General</TabsTrigger>
            {showXPathTab ? (
              <TabsTrigger value="xpaths">XPath Config</TabsTrigger>
            ) : null}
            {isWebAppTarget ? (
              <TabsTrigger value="credentials">Credentials</TabsTrigger>
            ) : null}
          </TabsList>

          <TabsContent value="general">
            <div className="overflow-y-auto flex-1 space-y-2 pb-5 p-1 pt-4">
              {/* <div className="flex items-center justify-center gap-2 pb-4">
                <Label className="text-base font-semibold">Target -</Label>
                <Label className="text-xl font-semibold text-primary hover:text-primary/90">
                  {target.target_name}
                </Label>
              </div> */}

              <div className="space-y-1 pb-4">
                <Label className="text-base font-semibold">Target</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  // aria-invalid={isNameInvalid}
                  // className={`bg-muted ${isNameInvalid ? "border-red-500" : ""}`}
                  className="bg-muted"
                  required
                />
                {/* <NameCharacterCounter value={name} />
                {hasInvalidNameCharacters && (
                  <p className="text-xs font-medium text-red-600">
                    {NAME_ALLOWED_CHARACTERS_MESSAGE}.
                  </p>
                )} */}
              </div>

              <div className="space-y-1 pb-4">
                <Label className="text-base font-semibold">Description</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-muted min-h-[60px] max-h-[100px]"
                  required
                  
                />
              </div>
              <div className="grid gap-4 pb-4 sm:grid-cols-2">
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
                <div className="bg-muted p-4 rounded-md max-h-[95px] overflow-y-auto">
                  {isFetchingOptions ? (
                    <div className="text-sm text-muted-foreground">
                      Loading languages...
                    </div>
                  ) : languageOptions.length === 0 ? (
                    <div className="text-sm text-muted-foreground">
                      No languages available
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 space-y-2">
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

            {/* <div className="flex flex-col gap-3 p-4 border-gray-300 bg-white sticky bottom-0 z-10 sm:flex-row sm:items-center sm:justify-center">
              <Label className="text-base font-bold">Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 sm:mr-4 sm:w-96"
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
            </div> */}
          </TabsContent>

          {showXPathTab ? (
          <TabsContent value="xpaths" className="pt-4 data-[state=inactive]:hidden" forceMount>
            <XPathConfigurationEditor
              applicationName={name}
              targetType={type}
              targetName={target.target_name}
              open={open}
              onPagesChange={handleXPathPagesChange}
              disabled={
                !hasPermission(currentUserRole, "canUpdateTables") &&
                !hasPermission(currentUserRole, "canUpdateRecords")
              }
              showSave={false}
            />
          </TabsContent>
          ) : null }

          {isWebAppTarget ? (
            <TabsContent
              value="credentials"
              className="pt-4 data-[state=inactive]:hidden"
              forceMount
            >
              <TargetCredentialsEditor
                targetName={
                  normalizeTargetType(targetInitial.target_type) === "webapp"
                    ? target.target_name
                    : undefined
                }
                open={open}
                value={credentials}
                onChange={handleCredentialsChange}
                // disabled={isTargetUpdateDisabled}
                showSave={false}
              />
            </TabsContent>
          ) : null}
        </Tabs>
            <div className="flex flex-col gap-3 p-4 border-gray-300 bg-white sticky bottom-0 z-10 sm:flex-row sm:items-center sm:justify-center">
              <Label className="text-base font-bold">Notes</Label>
              <Input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 sm:mr-4 sm:w-96"
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
                disabled={!hasChanges || !notes.trim() || isLoading || selectedLanguages.length === 0 ||
                  (!hasPermission(currentUserRole, "canUpdateTables") &&
                    !hasPermission(currentUserRole, "canUpdateRecords"))
                }
              >
                {isLoading ? "Updating..." : "Submit"}
              </Button>
            </div>
      </DialogContent>
    </Dialog>
    <AlertDialog open={discardConfirmOpen} onOpenChange={setDiscardConfirmOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Discard changes?</AlertDialogTitle>
          <AlertDialogDescription>
            You have unsaved target changes. Do you want to discard them and close this dialog?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={discardChangesAndClose}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Discard
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
}

export { TargetUpdateDialog };
