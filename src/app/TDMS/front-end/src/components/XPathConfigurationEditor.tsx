import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useState,
} from "react";
import { FileCode2, Loader2, Plus, Save, Trash2 } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

type XPathPages = Record<string, Record<string, string>>;

interface XPathConfigurationEditorProps {
  applicationName: string;
  applicationType?: string;
  targetType?: string;
  targetId?: number;
  targetName?: string;
  notes?: string;
  open: boolean;
  disabled?: boolean;
  onDirtyChange?: (isDirty: boolean) => void;
  onPagesChange?: (pages: XPathPages) => void;
  showSave?: boolean;
}

export interface XPathConfigurationEditorHandle {
  save: () => Promise<boolean>;
}

const normalizeApplicationName = (value: string) =>
  value.trim().toLowerCase().replace(/\s+/g, "_");

const resolveApplicationKey = (name: string, type?: string) => {
  const normalizedType = normalizeApplicationName(type || "");
  const normalizedName = normalizeApplicationName(name);

  if (
    normalizedType === "whatsapp" ||
    normalizedName === "whatsapp" ||
    normalizedName === "whatsapp_web"
  ) {
    return "whatsapp_web";
  }

  return normalizedName;
};

const sortPages = (pages: XPathPages) =>
  Object.keys(pages).sort((a, b) => a.localeCompare(b));

const XPathConfigurationEditor = forwardRef<
  XPathConfigurationEditorHandle,
  XPathConfigurationEditorProps
>(function XPathConfigurationEditor({
  applicationName,
  applicationType,
  targetType,
  targetId,
  targetName,
  notes,
  open,
  disabled = false,
  onDirtyChange,
  onPagesChange,
}, ref) {
  const { toast } = useToast();
  const resolvedApplicationType = applicationType ?? targetType;
  const appKey = useMemo(
    () => resolveApplicationKey(applicationName, resolvedApplicationType),
    [applicationName, resolvedApplicationType],
  );
  const targetKey = targetName?.trim() || "";
  const [pages, setPages] = useState<XPathPages>({});
  const [activePage, setActivePage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [savedSignature, setSavedSignature] = useState("{}");

  const pageNames = useMemo(() => sortPages(pages), [pages]);
  const activeElements = activePage ? pages[activePage] || {} : {};
  const hasChanges = JSON.stringify(pages) !== savedSignature;

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
    if (!open || !appKey) {
      setPages({});
      setActivePage("");
      setLoadError(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      // Existing targets must be resolved by the backend. In particular, the
      // target name and the key used in xpaths.json are not always identical
      // (for example WhatsApp targets use the shared `whatsapp_web` key).
      const response = await fetch(
        targetKey
          ? API_ENDPOINTS.TARGET_XPATHS_BY_TARGET_V2(targetKey)
          : API_ENDPOINTS.TARGET_XPATHS_V2(appKey),
        {
        headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to load XPath configuration");
      }

      const data = await response.json();
      const responsePages = targetKey ? data : data?.pages;
      const nextPages = responsePages && typeof responsePages === "object"
        ? responsePages
        : {};
      const nextPageNames = sortPages(nextPages);
      setPages(nextPages);
      setActivePage(nextPageNames[0] || "");
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
  }, [appKey, authHeaders, open, targetKey]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  useEffect(() => {
    onDirtyChange?.(hasChanges);
  }, [hasChanges, onDirtyChange]);

  useEffect(() => {
    onPagesChange?.(pages);
  }, [onPagesChange, pages]);

  const addPage = () => {
    let index = pageNames.length + 1;
    let nextName = `Page${index}`;
    while (pages[nextName]) {
      index += 1;
      nextName = `Page${index}`;
    }

    setPages((current) => ({ ...current, [nextName]: {} }));
    setActivePage(nextName);
  };

  const renamePage = (oldName: string, newName: string) => {
    const trimmedName = newName.trim();
    if (!trimmedName || trimmedName === oldName || pages[trimmedName]) return;

    setPages((current) => {
      const { [oldName]: pageConfig, ...remaining } = current;
      return { ...remaining, [trimmedName]: pageConfig };
    });
    setActivePage(trimmedName);
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

  const addElement = () => {
    if (!activePage) return;

    setPages((current) => {
      const pageConfig = current[activePage] || {};
      let index = Object.keys(pageConfig).length + 1;
      let nextName = `element_${index}`;
      while (pageConfig[nextName]) {
        index += 1;
        nextName = `element_${index}`;
      }

      return {
        ...current,
        [activePage]: {
          ...pageConfig,
          [nextName]: "",
        },
      };
    });
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

  const saveConfig = useCallback(async (showToast = true) => {
    if (!appKey || disabled) return false;

    setIsSaving(true);
    try {
      const response = await fetch(API_ENDPOINTS.TARGET_XPATHS_V2(appKey), {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({
          pages,
          target_id: targetId,
          target_name: targetName || applicationName,
          notes: notes?.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save XPath configuration");
      }

      setSavedSignature(JSON.stringify(pages));
      onDirtyChange?.(false);
      if (showToast) {
        toast({
          title: "Success",
          description: `XPath configuration saved for ${appKey}`,
        });
      }
      return true;
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to save XPath configuration",
        variant: "destructive",
      });
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [appKey, applicationName, authHeaders, disabled, notes, onDirtyChange, pages, targetId, targetName, toast]);

  useImperativeHandle(
    ref,
    () => ({
      save: () => saveConfig(false),
    }),
    [saveConfig],
  );

  if (!appKey) {
    return (
      <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
        Target name required.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 border-b pb-4 sm:flex-row sm:items-center sm:justify-center">
              <div className="flex items-center justify-center gap-2 pb-4">
                <Label className="text-base font-semibold">Target -</Label>
                <Label className="text-xl font-semibold text-primary hover:text-primary/90">
                  {/* {target.target_name} */}{appKey}
                  {/* <Badge variant="secondary" className="rounded-md font-mono">
                    {appKey}
                  </Badge> */}
                </Label>
              </div>
        <div className="min-w-0 space-y-1">
          {/* <div className="flex items-center gap-2">
            <FileCode2 className="h-4 w-4 text-primary" />
            <Label className="text-base font-semibold">XPath Configuration</Label>
          </div>
          {/* <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>
              {usesTargetConfig
                ? "Target"
                : usesTypeTemplate
                  ? "XPath template"
                  : "Shared application key"}
            </span>
            <Badge variant="secondary" className="rounded-md font-mono">
              {appKey}
            </Badge>
          </div> */}
        </div>
        {/* <Button
          type="button"
          onClick={() => saveConfig()}
          disabled={disabled || isLoading || isSaving || !hasChanges}
          className="gap-2"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save XPaths
        </Button> */}
      </div>

      {loadError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {loadError}
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
            <div className="flex items-center justify-between border-b p-3 bg-white">
              <Label className="font-semibold">Pages</Label>
              <Button
                type="button"
                size="icon"
                // variant="outline"
                onClick={addPage}
                disabled={disabled}
                aria-label="Add page"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="h-[380px]">
              <div className="space-y-2 p-3">
                {pageNames.length === 0 ? (
                  <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                    No pages configured.
                  </div>
                ) : (
                  pageNames.map((pageName) => (
                    <div
                      key={pageName}
                      className={`flex items-center gap-2 rounded-md border p-2 bg-white ${
                        activePage === pageName ? "border-primary bg-primary/5 bg-white" : ""
                      }`}
                    >
                      <div
                        className="min-w-0 flex-1"
                        onFocus={() => setActivePage(pageName)}
                        onClick={() => setActivePage(pageName)}
                      >
                        <Input
                          defaultValue={pageName}
                          onBlur={(event) =>
                            renamePage(pageName, event.target.value)
                          }
                          disabled={disabled}
                          className="h-8 bg-background"
                        />
                      </div>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        onClick={() => deletePage(pageName)}
                        disabled={disabled}
                        aria-label={`Delete ${pageName}`}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>

          <div className="rounded-md border">
            <div className="flex flex-col gap-3 border-b p-3 sm:flex-row sm:items-center sm:justify-between bg-white">
              <div>
                <Label className="text-base font-semibold">
                  {activePage || "Select a page"}
                </Label>
              </div>
              <Button
                type="button"
                // variant="outline"
                onClick={addElement}
                disabled={disabled || !activePage}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Element
              </Button>
            </div>

            <ScrollArea className="h-[380px]">
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
                      className="grid gap-3 rounded-md border p-3 xl:grid-cols-[220px_minmax(0,1fr)_40px] bg-white"
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
                          disabled={disabled}
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
                          disabled={disabled}
                          className="min-h-[48px] max-h-[73px] bg-background font-mono text-sm"
                        />
                      </div>
                      <div className="flex items-end">
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={() => deleteElement(elementName)}
                          disabled={disabled}
                          aria-label={`Delete ${elementName}`}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
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
});

export default XPathConfigurationEditor;
