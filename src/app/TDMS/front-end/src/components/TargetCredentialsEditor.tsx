import { useCallback, useEffect, useState } from "react";
import { Eye, EyeOff, Loader2, Save } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface TargetCredentials {
  username: string;
  password: string;
}

interface TargetCredentialsEditorProps {
  targetName?: string;
  open: boolean;
  disabled?: boolean;
  value: TargetCredentials;
  onChange: (credentials: TargetCredentials) => void;
  showSave?: boolean;
}

const areCredentialsComplete = (credentials: TargetCredentials) =>
  Boolean(credentials.username.trim() && credentials.password.trim());

const hasAnyCredentials = (credentials: TargetCredentials) =>
  Boolean(credentials.username.trim() || credentials.password.trim());

const emptyCredentials: TargetCredentials = {
  username: "",
  password: "",
};

export default function TargetCredentialsEditor({
  targetName,
  open,
  disabled = false,
  value,
  onChange,
  showSave = true,
}: TargetCredentialsEditorProps) {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  

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

  const loadCredentials = useCallback(async () => {
    if (!open || !targetName) {
      setLoadError(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const response = await fetch(API_ENDPOINTS.TARGET_CREDENTIALS_V2(targetName), {
        headers: authHeaders(),
      });

      if (response.status === 404) {
        onChange(emptyCredentials);
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to load credentials");
      }

      const data = await response.json();
      onChange({
        username: typeof data?.username === "string" ? data.username : "",
        password: typeof data?.password === "string" ? data.password : "",
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load credentials";
      setLoadError(message);
    } finally {
      setIsLoading(false);
    }
  }, [authHeaders, onChange, open, targetName]);

  useEffect(() => {
    loadCredentials();
  }, [loadCredentials]);

  const updateField = (field: keyof TargetCredentials, fieldValue: string) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  };

  const saveCredentials = async () => {
    if (!targetName || disabled) return;

    // if (!areCredentialsComplete(value)) {
    //   toast({
    //     title: "Validation Error",
    //     description: "Username and password are required",
    //     variant: "destructive",
    //   });
    //   return;
    // }

    setIsSaving(true);
    try {
      const payload = JSON.stringify({
        username: value.username.trim(),
        password: value.password.trim(),
      });
      const headers = authHeaders();
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

      toast({
        title: "Success",
        description: "Credentials saved successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to save credentials",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const isComplete = areCredentialsComplete(value);

  return (
    <div className="space-y-4 px-1">
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
        {/* <div>
          <Label className="text-base font-semibold">Credentials</Label>
          <p className="text-sm text-muted-foreground">
            WebApp login credentials (optional)
          </p>
        </div> */}
        {showSave ? (
          <Button
            type="button"
            onClick={saveCredentials}
            disabled={disabled || isLoading || isSaving || !targetName || !isComplete}
            className="gap-2"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save Credentials
          </Button>
        ) : null}
      </div>

      {loadError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {loadError}
        </div>
      ) : null}

      {/* {!isLoading && !isComplete ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          Enter both username and password, or leave both blank.
        </div>
      ) : null} */}

      {isLoading ? (
        <div className="flex min-h-[160px] items-center justify-center text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading credentials...
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-base font-semibold">Username</Label>
            <Input
              // name="target-credential-username"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="none"
              spellCheck={false}
              value={value.username}
              onChange={(event) => updateField("username", event.target.value)}
              disabled={disabled}
              // required
              aria-invalid={!value.username.trim()}
              // className={`bg-muted ${
              //   !value.username.trim() ? "border-red-500" : ""
              // }`}
            />
          </div>
          <div className="space-y-2">
            <Label className="text-base font-semibold">Password</Label>
            <div className="relative">
              <Input
                type={isPasswordVisible ? "text" : "password"}
                // name="target-credential-password"
                autoComplete="new-password"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                value={value.password}
                onChange={(event) => updateField("password", event.target.value)}
                disabled={disabled}
                // required
                aria-invalid={!value.password.trim()}
                // className={`bg-muted pr-10 ${
                //   !value.password.trim() ? "border-red-500" : ""
                // }`}
              />
              <Button
                type="button"
                variant="link"
                size="icon"
                onClick={() => setIsPasswordVisible((current) => !current)}
                className="absolute right-1 top-1/2 h-8 w-8 -translate-y-1/2 text-muted-foreground"
                aria-label={isPasswordVisible ? "Hide password" : "Show password"}
              >
                {isPasswordVisible ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
