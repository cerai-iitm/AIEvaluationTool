import { useCallback, useEffect, useMemo, useState } from "react";
import { FileCode2, Loader2, Pencil, Plus, Save, Trash2 } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

type XPathPages = Record<string, Record<string, string>>;

interface XPathConfigurationEditorProps {
  applicationName: string;
  open: boolean;
  disabled?: boolean;
  targetName?: string;
  targetType?: string;
  onPagesChange?: (pages: XPathPages) => void;
  onValidityChange?: (isValid: boolean) => void;
  showSave?: boolean;
}

const normalizeApplicationName = (value: string) =>
  value.trim().toLowerCase().replace(/\s+/g, "_");

const normalizeTargetType = (value?: string) => value?.trim().toLowerCase() || "";

const getTemplateKeyForTargetType = (targetType?: string) => {
  const normalizedType = normalizeTargetType(targetType);
  if (normalizedType === "whatsapp") return "whatsapp_web";
  if (normalizedType === "webapp") return "cpgrams";
  return "";
};

const sortPages = (pages: XPathPages) =>
  Object.keys(pages).sort((a, b) => a.localeCompare(b));

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

export default function XPathConfigurationEditor({
  applicationName,
  open,
  disabled = false,
  targetName,
  targetType,
  onPagesChange,
  onValidityChange,
  showSave = true,
}: XPathConfigurationEditorProps) {
  const { toast } = useToast();
  const appKey = useMemo(
    () => normalizeApplicationName(applicationName),
    [applicationName],
  );
  const targetKey = useMemo(() => targetName?.trim() || "", [targetName]);
  const usesTargetConfig = Boolean(targetKey);
  const usesTypeTemplate = !usesTargetConfig && targetType !== undefined;
  const selectedTargetType = normalizeTargetType(targetType);
  const shouldBlankTemplateValues =
    usesTypeTemplate && selectedTargetType === "webapp";
  const templateKey = useMemo(
    () => getTemplateKeyForTargetType(targetType),
    [targetType],
  );
  const configKey = usesTypeTemplate ? templateKey : appKey;
  const configLabel = usesTargetConfig ? targetKey : configKey;
  const [pages, setPages] = useState<XPathPages>({});
  const [activePage, setActivePage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isAddingElement, setIsAddingElement] = useState(false);
  const [deletingPage, setDeletingPage] = useState("");
  const [deletingElement, setDeletingElement] = useState("");
  const [editingPage, setEditingPage] = useState("");
  const [editingPageName, setEditingPageName] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [savedSignature, setSavedSignature] = useState("{}");

  const pageNames = useMemo(() => sortPages(pages), [pages]);
  const activeElements = activePage ? pages[activePage] || {} : {};
  const savedPages = useMemo(() => {
    try {
      return toXPathPages(JSON.parse(savedSignature));
    } catch {
      return {};
    }
  }, [savedSignature]);
  const hasChanges = JSON.stringify(pages) !== savedSignature;
  const isDeleting = Boolean(deletingPage || deletingElement);
  const isMutating = isDeleting || isAddingElement || isSaving;
  const xpathFieldCount = useMemo(() => getXPathFieldCount(pages), [pages]);
  const missingXPathCount = useMemo(() => getMissingXPathCount(pages), [pages]);
  const isXPathConfigComplete = xpathFieldCount > 0 && missingXPathCount === 0;
  const canSaveTypeTemplate =
    usesTypeTemplate && Boolean(appKey) && pageNames.length > 0;

  const authHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }, []);

  const loadConfig = useCallback(async () => {
    if (
      !open ||
      !configLabel ||
      (usesTypeTemplate && (!selectedTargetType || selectedTargetType === "api"))
    ) {
      setPages({});
      setActivePage("");
      setLoadError(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const response = await fetch(
        usesTargetConfig
          ? API_ENDPOINTS.TARGET_XPATHS_BY_TARGET_V2(targetKey)
          : API_ENDPOINTS.TARGET_XPATHS_V2(configKey),
        {
          headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to load XPath configuration");
      }

      const data = await response.json();
      const responsePages = usesTargetConfig ? data : data?.pages;
      const nextPages = shouldBlankTemplateValues
        ? toBlankXPathPages(toXPathPages(responsePages))
        : toXPathPages(responsePages);
      const nextPageNames = sortPages(nextPages);
      setPages(nextPages);
      setActivePage(nextPageNames[0] || "");
      setEditingPage("");
      setEditingPageName("");
      setSavedSignature(JSON.stringify(nextPages));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load XPath configuration";
      setLoadError(message);
      setPages({});
      setActivePage("");
    } finally {
      setIsLoading(false);
    }
  }, [
    authHeaders,
    configKey,
    configLabel,
    open,
    selectedTargetType,
    shouldBlankTemplateValues,
    targetKey,
    usesTargetConfig,
    usesTypeTemplate,
  ]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  useEffect(() => {
    onPagesChange?.(pages);
  }, [onPagesChange, pages]);

  useEffect(() => {
    onValidityChange?.(isXPathConfigComplete);
  }, [isXPathConfigComplete, onValidityChange]);

  const addPage = () => {
    let index = pageNames.length + 1;
    let nextName = `Page${index}`;
    while (pages[nextName]) {
      index += 1;
      nextName = `Page${index}`;
    }

    setPages((current) => ({ ...current, [nextName]: {} }));
    setActivePage(nextName);
    setEditingPage(nextName);
    setEditingPageName(nextName);
  };

  const startEditingPage = (pageName: string) => {
    if (disabled || isMutating) return;

    setActivePage(pageName);
    setEditingPage(pageName);
    setEditingPageName(pageName);
  };

  const cancelPageEdit = () => {
    setEditingPage("");
    setEditingPageName("");
  };

  const persistPageRename = async (nextPages: XPathPages) => {
    if (!usesTargetConfig) return true;

    setIsSaving(true);
    try {
      const response = await fetch(
        API_ENDPOINTS.TARGET_XPATHS_UPDATE_BY_TARGET_V2(targetKey),
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(nextPages),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to rename page");
      }

      setSavedSignature(JSON.stringify(nextPages));
      return true;
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to rename page",
        variant: "destructive",
      });
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const commitPageRename = async (oldName: string) => {
    const trimmedName = editingPageName.trim();
    if (!trimmedName || trimmedName === oldName) {
      cancelPageEdit();
      return;
    }

    if (pages[trimmedName]) {
      toast({
        title: "Validation Error",
        description: "A page with this name already exists",
        variant: "destructive",
      });
      return;
    }

    const pageConfig = pages[oldName];
    if (!pageConfig) {
      cancelPageEdit();
      return;
    }

    const { [oldName]: _renamed, ...remaining } = pages;
    const nextPages = { ...remaining, [trimmedName]: pageConfig };
    const didPersist = await persistPageRename(nextPages);
    if (!didPersist) return;

    setPages(nextPages);
    onPagesChange?.(nextPages);
    setActivePage(trimmedName);
    cancelPageEdit();
  };

  const deletePage = (pageName: string) => {
    setPages((current) => {
      const { [pageName]: _deleted, ...remaining } = current;
      const remainingPages = sortPages(remaining);
      if (activePage === pageName) {
        setActivePage(remainingPages[0] || "");
      }
      return remaining;
    });
  };

  const persistDeletedPage = async (pageName: string) => {
    if (!usesTargetConfig || savedPages[pageName] === undefined) {
      deletePage(pageName);
      return;
    }

    setDeletingPage(pageName);
    try {
      const response = await fetch(
        API_ENDPOINTS.TARGET_XPATH_PAGE_DELETE_BY_TARGET_V2(targetKey, pageName),
        {
          method: "DELETE",
          headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete page");
      }

      const nextSavedPages = toXPathPages(await response.json());
      setSavedSignature(JSON.stringify(nextSavedPages));
      deletePage(pageName);
      toast({
        title: "Success",
        description: `Deleted page ${pageName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete page",
        variant: "destructive",
      });
    } finally {
      setDeletingPage("");
    }
  };

  const getNextElementName = (pageConfig: Record<string, string>) => {
    let index = Object.keys(pageConfig).length + 1;
    let nextName = `element_${index}`;
    while (pageConfig[nextName]) {
      index += 1;
      nextName = `element_${index}`;
    }
    return nextName;
  };

  const addElementToPage = (pageName: string, elementName: string) => {
    setPages((current) => ({
      ...current,
      [pageName]: {
        ...(current[pageName] || {}),
        [elementName]: "",
      },
    }));
  };

  const addElement = async () => {
    if (!activePage) return;

    const pageName = activePage;
    const nextName = getNextElementName(pages[pageName] || {});
    if (!usesTargetConfig || savedPages[pageName] === undefined) {
      addElementToPage(pageName, nextName);
      return;
    }

    setIsAddingElement(true);
    try {
      const response = await fetch(
        API_ENDPOINTS.TARGET_XPATH_ELEMENT_ADD_BY_TARGET_V2(
          targetKey,
          pageName,
          nextName,
        ),
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ xpath: "" }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to add element");
      }

      const nextSavedPages = toXPathPages(await response.json());
      setSavedSignature(JSON.stringify(nextSavedPages));
      addElementToPage(pageName, nextName);
      toast({
        title: "Success",
        description: `Added element ${nextName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to add element",
        variant: "destructive",
      });
    } finally {
      setIsAddingElement(false);
    }
  };

  const renameElement = (oldName: string, newName: string) => {
    const trimmedName = newName.trim();
    if (
      !activePage ||
      !trimmedName ||
      trimmedName === oldName ||
      activeElements[trimmedName] !== undefined
    ) {
      return;
    }

    setPages((current) => {
      const pageConfig = current[activePage] || {};
      const { [oldName]: value, ...remaining } = pageConfig;
      return {
        ...current,
        [activePage]: {
          ...remaining,
          [trimmedName]: value,
        },
      };
    });
  };

  const updateElementValue = (elementName: string, value: string) => {
    if (!activePage) return;

    setPages((current) => ({
      ...current,
      [activePage]: {
        ...(current[activePage] || {}),
        [elementName]: value,
      },
    }));
  };

  const deleteElement = (elementName: string) => {
    if (!activePage) return;

    setPages((current) => {
      const pageConfig = current[activePage] || {};
      const { [elementName]: _deleted, ...remaining } = pageConfig;
      return {
        ...current,
        [activePage]: remaining,
      };
    });
  };

  const persistDeletedElement = async (elementName: string) => {
    if (!activePage) return;

    const pageName = activePage;
    if (
      !usesTargetConfig ||
      savedPages[pageName]?.[elementName] === undefined
    ) {
      deleteElement(elementName);
      return;
    }

    const deletingKey = `${pageName}/${elementName}`;
    setDeletingElement(deletingKey);
    try {
      const response = await fetch(
        API_ENDPOINTS.TARGET_XPATH_ELEMENT_DELETE_BY_TARGET_V2(
          targetKey,
          pageName,
          elementName,
        ),
        {
          method: "DELETE",
          headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete element");
      }

      const nextSavedPages = toXPathPages(await response.json());
      setSavedSignature(JSON.stringify(nextSavedPages));
      deleteElement(elementName);
      toast({
        title: "Success",
        description: `Deleted element ${elementName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete element",
        variant: "destructive",
      });
    } finally {
      setDeletingElement("");
    }
  };

  const saveConfig = async () => {
    if (!configLabel || disabled || (!usesTargetConfig && !appKey)) return;
    if (!isXPathConfigComplete) {
      toast({
        title: "Validation Error",
        description:
          xpathFieldCount === 0
            ? "At least one XPath field is required"
            : "All XPath fields are required",
        variant: "destructive",
      });
      return;
    }

    const saveApplicationKey =
      usesTypeTemplate && selectedTargetType === "whatsapp" ? configKey : appKey;

    setIsSaving(true);
    try {
      const response = await fetch(
        usesTargetConfig
          ? API_ENDPOINTS.TARGET_XPATHS_UPDATE_BY_TARGET_V2(targetKey)
          : API_ENDPOINTS.TARGET_XPATHS_V2(saveApplicationKey),
        {
          method: usesTargetConfig ? "POST" : "PUT",
          headers: authHeaders(),
          body: JSON.stringify(usesTargetConfig ? pages : { pages }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save XPath configuration");
      }

      setSavedSignature(JSON.stringify(pages));
      toast({
        title: "Success",
        description: `XPath configuration saved for ${configLabel}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to save XPath configuration",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!configLabel) {
    const emptyMessage =
      usesTypeTemplate && selectedTargetType === "api"
        ? "XPath configuration is not required for API targets."
        : usesTypeTemplate
          ? "Select WhatsApp or WebApp to load XPath fields."
          : "Target name required.";

    return (
      <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <FileCode2 className="h-4 w-4 text-primary" />
            <Label className="text-base font-semibold">XPath Configuration</Label>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>
              {usesTargetConfig
                ? "Target"
                : usesTypeTemplate
                  ? "XPath template"
                  : "Shared application key"}
            </span>
            <Badge variant="secondary" className="rounded-md font-mono">
              {configLabel}
            </Badge>
          </div>
        </div>
        {showSave ? (
          <Button
            type="button"
            onClick={saveConfig}
            disabled={
              disabled ||
              (!usesTargetConfig && !appKey) ||
              !isXPathConfigComplete ||
              isLoading ||
              isSaving ||
              isMutating ||
              (!hasChanges && !canSaveTypeTemplate)
            }
            className="gap-2"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save XPaths
          </Button>
        ) : null}
      </div>

      {loadError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {loadError}
        </div>
      ) : null}

      {!isLoading && !loadError && !isXPathConfigComplete ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {xpathFieldCount === 0
            ? "At least one XPath field is required."
            : `All XPath fields are required. ${missingXPathCount} field${
                missingXPathCount === 1 ? "" : "s"
              } empty.`}
        </div>
      ) : null}

      {isLoading ? (
        <div className="flex min-h-[240px] items-center justify-center text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading XPath configuration...
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
          <div className="rounded-md border">
            <div className="flex items-center justify-between border-b p-3">
              <Label className="font-semibold">Pages</Label>
              <Button
                type="button"
                size="icon"
                variant="outline"
                onClick={addPage}
                disabled={disabled || isMutating}
                aria-label="Add page"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="h-[320px]">
              <div className="space-y-2 p-3">
                {pageNames.length === 0 ? (
                  <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                    No pages configured.
                  </div>
                ) : (
                  pageNames.map((pageName) => (
                    <div
                      key={pageName}
                      role="button"
                      tabIndex={disabled || isMutating ? -1 : 0}
                      aria-pressed={activePage === pageName}
                      onClick={() => setActivePage(pageName)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setActivePage(pageName);
                        }
                      }}
                      className={`flex cursor-pointer items-center gap-2 rounded-md border p-2 transition hover:border-primary/60 hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        activePage === pageName
                          ? "border-primary bg-primary/5"
                          : ""
                      }`}
                    >
                      {editingPage === pageName ? (
                        <Input
                          autoFocus
                          value={editingPageName}
                          onChange={(event) =>
                            setEditingPageName(event.target.value)
                          }
                          onClick={(event) => event.stopPropagation()}
                          onKeyDown={(event) => {
                            event.stopPropagation();
                            if (event.key === "Enter") {
                              commitPageRename(pageName);
                            }
                            if (event.key === "Escape") {
                              cancelPageEdit();
                            }
                          }}
                          onBlur={() => commitPageRename(pageName)}
                          disabled={disabled || isMutating}
                          className="h-8 min-w-0 flex-1 bg-background text-sm"
                        />
                      ) : (
                        <>
                          <div className="flex h-8 min-w-0 flex-1 items-center rounded-md bg-background px-3 text-sm">
                            <span className="truncate">{pageName}</span>
                          </div>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            onClick={(event) => {
                              event.stopPropagation();
                              startEditingPage(pageName);
                            }}
                            disabled={disabled || isMutating}
                            aria-label={`Edit ${pageName}`}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            onClick={(event) => event.stopPropagation()}
                            disabled={disabled || isMutating}
                            aria-label={`Delete ${pageName}`}
                          >
                            {deletingPage === pageName ? (
                              <Loader2 className="h-4 w-4 animate-spin text-destructive" />
                            ) : (
                              <Trash2 className="h-4 w-4 text-destructive" />
                            )}
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete page?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Do you want to delete the page "{pageName}" and all
                              of its XPath elements?
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => persistDeletedPage(pageName)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Confirm Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>

          <div className="rounded-md border">
            <div className="flex flex-col gap-3 border-b p-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <Label className="text-base font-semibold">
                  {activePage || "Select a page"}
                </Label>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={addElement}
                disabled={disabled || isMutating || !activePage}
                className="gap-2"
              >
                {isAddingElement ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                Add Element
              </Button>
            </div>

            <ScrollArea className="h-[320px]">
              <div className="space-y-3 p-3">
                {!activePage ? (
                  <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
                    Add or select a page to edit elements.
                  </div>
                ) : Object.keys(activeElements).length === 0 ? (
                  <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
                    No elements configured for this page.
                  </div>
                ) : (
                  Object.entries(activeElements).map(([elementName, xpath]) => (
                    <div
                      key={elementName}
                      className="grid gap-3 rounded-md border p-3 xl:grid-cols-[220px_minmax(0,1fr)_40px]"
                    >
                      <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">
                          Element Name
                        </Label>
                        <Input
                          defaultValue={elementName}
                          onBlur={(event) =>
                            renameElement(elementName, event.target.value)
                          }
                          disabled={disabled || isMutating}
                          className="bg-background font-mono text-sm"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">
                          XPath
                        </Label>
                        <Textarea
                          value={xpath}
                          onChange={(event) =>
                            updateElementValue(elementName, event.target.value)
                          }
                          disabled={disabled || isMutating}
                          required
                          aria-invalid={!xpath.trim()}
                          className={`min-h-[76px] bg-background font-mono text-sm ${
                            !xpath.trim()
                              ? "border-red-500 focus-visible:ring-red-500"
                              : ""
                          }`}
                        />
                      </div>
                      <div className="flex items-end">
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              type="button"
                              size="icon"
                              variant="ghost"
                              disabled={disabled || isMutating}
                              aria-label={`Delete ${elementName}`}
                            >
                              {deletingElement ===
                              `${activePage}/${elementName}` ? (
                                <Loader2 className="h-4 w-4 animate-spin text-destructive" />
                              ) : (
                                <Trash2 className="h-4 w-4 text-destructive" />
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete element?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Do you want to delete the XPath element
                                "{elementName}" from "{activePage}"?
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => persistDeletedElement(elementName)}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                Confirm Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      )}
    </div>
  );
}
