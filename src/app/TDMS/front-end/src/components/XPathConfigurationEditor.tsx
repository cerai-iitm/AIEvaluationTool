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
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

interface ElementSpec {
  key: string;
  required: boolean;
  hint: string;
}

interface PageSpec {
  elements: ElementSpec[];
}

// Mirrors what src/app/interface_manager/utils.py actually reads:
// login_app/logout_app for LoginPage/LogoutPage, and
// handle_generic_webapp's three response-capture modes for ChatPage.
// Keeping this in sync with utils.py is what lets a target built purely
// from these picklists work with no backend code changes.
const PAGE_SCHEMA: Record<string, PageSpec> = {
  LoginPage: {
    elements: [
      { key: "email_input_element", required: true, hint: "Username/email input field" },
      { key: "password_input_element", required: true, hint: "Password input field" },
      { key: "login_button_element", required: true, hint: "Sign-in / submit button" },
    ],
  },
  LogoutPage: {
    elements: [
      { key: "profile_pic_element", required: false, hint: "Presence check used to detect an already-logged-in session" },
      { key: "profile_element", required: false, hint: "Opens the account/profile menu before logging out" },
      { key: "logout_button_element", required: true, hint: "Sign-out button" },
    ],
  },
  ChatPage: {
    elements: [
      { key: "prompt_input_box_element", required: true, hint: "Where the prompt text is typed" },
      { key: "agent_response_element", required: true, hint: "Where the agent's reply text appears" },
      { key: "send_button_element", required: false, hint: "Only clicked if submit_via_click is 'true'; otherwise Enter submits" },
      { key: "submit_via_click", required: false, hint: "Set to 'true' to click send_button_element instead of pressing Enter" },
      { key: "shadow_root_element", required: false, hint: "CSS selector for a shadow-DOM host — enables shadow-DOM mode" },
      { key: "message_in_element", required: false, hint: "XPath for incoming chat bubbles — pairs with message_out_element for turn/bubble mode" },
      { key: "message_out_element", required: false, hint: "XPath for outgoing chat bubbles — pairs with message_in_element" },
      { key: "response_timeout", required: false, hint: "Max seconds to wait for a response" },
      { key: "response_stable_time", required: false, hint: "Seconds the response must stop changing before it's considered final" },
      { key: "response_poll_interval", required: false, hint: "Seconds between polls while waiting for a response" },
      { key: "pre_send_wait", required: false, hint: "Shadow-DOM mode only: fixed seconds to wait after sending, before polling" },
    ],
  },
};

const KNOWN_PAGE_NAMES = Object.keys(PAGE_SCHEMA);

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
  showSave?: boolean;
  onPagesChange?: (pages: XPathPages) => void;
  onDirtyChange?: (isDirty: boolean) => void;
  // onPagesChange?: (pages: XPathPages) => void;
  // showSave?: boolean;
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
  showSave = true,
  onPagesChange,
  onDirtyChange,
}, ref) {
  const { toast } = useToast();
  const resolvedApplicationType = applicationType ?? targetType;
  const appKey = useMemo(
    () => resolveApplicationKey(applicationName, targetType),
    [applicationName, targetType],
  );
  const targetKey = targetName?.trim() || "";
  const [pages, setPages] = useState<XPathPages>({});
  const [activePage, setActivePage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasLoadedConfig, setHasLoadedConfig] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [savedSignature, setSavedSignature] = useState("{}");

  const pageNames = useMemo(() => sortPages(pages), [pages]);
  const activeElements = activePage ? pages[activePage] || {} : {};
  const hasChanges = JSON.stringify(pages) !== savedSignature;

  const activeSchema = PAGE_SCHEMA[activePage];
  const activeSchemaByKey = useMemo(() => {
    const map: Record<string, ElementSpec> = {};
    for (const el of activeSchema?.elements ?? []) {
      map[el.key] = el;
    }
    return map;
  }, [activeSchema]);
  const availableSchemaElements = useMemo(
    () => (activeSchema?.elements ?? []).filter((el) => activeElements[el.key] === undefined),
    [activeSchema, activeElements],
  );
  const missingRequiredElements = useMemo(
    () => (activeSchema?.elements ?? []).filter((el) => el.required && !activeElements[el.key]),
    [activeSchema, activeElements],
  );
  const availablePageNames = useMemo(
    () => KNOWN_PAGE_NAMES.filter((name) => !pages[name]),
    [pages],
  );

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
      setHasLoadedConfig(false);
      return;
    }

    setIsLoading(true);
    setHasLoadedConfig(false);
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
      setHasLoadedConfig(true);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load XPath configuration";
      setLoadError(message);
      setPages({});
      setActivePage("");
      setSavedSignature("{}");
      setHasLoadedConfig(true);
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
    if (!hasLoadedConfig) return;
    onPagesChange?.(pages);
  }, [hasLoadedConfig, onPagesChange, pages]);

  const addPage = (explicitName?: string) => {
    if (explicitName) {
      if (pages[explicitName]) {
        setActivePage(explicitName);
        return;
      }
      setPages((current) => ({ ...current, [explicitName]: {} }));
      setActivePage(explicitName);
      return;
    }

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

  const addElement = (explicitName?: string) => {
    if (!activePage) return;

    if (explicitName) {
      if (activeElements[explicitName] !== undefined) return;
      setPages((current) => ({
        ...current,
        [activePage]: {
          ...(current[activePage] || {}),
          [explicitName]: "",
        },
      }));
      return;
    }

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
                {/* <Label className="text-base font-semibold">Target -</Label>
                <Label className="text-xl font-semibold text-primary hover:text-primary/90">
                  {targetName || "N/A"} */}
                  {/* {target.target_name}{appKey} */}
                  {/* <Badge variant="secondary" className="rounded-md font-mono">
                    {appKey}
                  </Badge> */}
                {/* </Label> */}
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
        {showSave ? (
        <Button
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
        </Button>
        ) : null}
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
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    size="icon"
                    disabled={disabled}
                    aria-label="Add page"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  {availablePageNames.length > 0 ? (
                    <>
                      <DropdownMenuLabel>Standard pages</DropdownMenuLabel>
                      {availablePageNames.map((name) => (
                        <DropdownMenuItem key={name} onSelect={() => addPage(name)}>
                          {name}
                        </DropdownMenuItem>
                      ))}
                      <DropdownMenuSeparator />
                    </>
                  ) : null}
                  <DropdownMenuItem onSelect={() => addPage()}>
                    Custom page…
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
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
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    disabled={disabled || !activePage}
                    className="gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Add Element
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-80">
                  {availableSchemaElements.length > 0 ? (
                    <>
                      <DropdownMenuLabel>{activePage} fields</DropdownMenuLabel>
                      <div className="max-h-[320px] overflow-y-auto">
                        {availableSchemaElements.map((el) => (
                          <DropdownMenuItem
                            key={el.key}
                            onSelect={() => addElement(el.key)}
                            className="flex flex-col items-start gap-1 py-2"
                          >
                            <span className="font-mono text-xs">
                              {el.key}
                              {el.required ? (
                                <span className="ml-1 font-sans text-[10px] font-semibold text-red-600">
                                  * required
                                </span>
                              ) : null}
                            </span>
                            <span className="text-xs text-muted-foreground whitespace-normal">
                              {el.hint}
                            </span>
                          </DropdownMenuItem>
                        ))}
                      </div>
                      <DropdownMenuSeparator />
                    </>
                  ) : null}
                  <DropdownMenuItem onSelect={() => addElement()}>
                    Custom element…
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {activePage && missingRequiredElements.length > 0 ? (
              <div className="mx-3 mt-3 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800">
                Missing required for {activePage}:{" "}
                {missingRequiredElements.map((el) => el.key).join(", ")}
              </div>
            ) : null}

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
                        <Label className="flex items-center gap-2 text-xs text-muted-foreground">
                          Element Name
                          {activeSchemaByKey[elementName]?.required ? (
                            <span className="text-[10px] font-semibold text-red-600">
                              * required
                            </span>
                          ) : null}
                        </Label>
                        <Input
                          defaultValue={elementName}
                          onBlur={(event) =>
                            renameElement(elementName, event.target.value)
                          }
                          disabled={disabled}
                          className="bg-background font-mono text-sm"
                        />
                        {activeSchemaByKey[elementName]?.hint ? (
                          <p className="text-xs text-muted-foreground">
                            {activeSchemaByKey[elementName].hint}
                          </p>
                        ) : null}
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
