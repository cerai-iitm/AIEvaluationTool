import { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { API_ENDPOINTS } from '@/config/api';
import { useToast } from '@/hooks/use-toast';

interface Target {
  id: number;
  name: string;
  type: string;
  description: string;
  url: string;
  domain: string;
  languages: string[];
  notes?: string;
}

interface TargetUpdateDialogProps {
  target: Target | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateSuccess?: () => void;
}

export default function TargetUpdateDialog({ target, open, onOpenChange, onUpdateSuccess }: TargetUpdateDialogProps) {
  const { toast } = useToast();
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [domain, setDomain] = useState('');
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [targetTypes, setTargetTypes] = useState<string[]>([]);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isFetchingOptions, setIsFetchingOptions] = useState(false);

  // Fetch options from API
  const fetchOptions = useCallback(async () => {
    setIsFetchingOptions(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const [typesResponse, domainsResponse, languagesResponse] = await Promise.all([
        fetch(API_ENDPOINTS.TARGET_TYPES, { headers }),
        fetch(API_ENDPOINTS.DOMAINS, { headers }),
        fetch(API_ENDPOINTS.LANGUAGES, { headers }),
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
      console.error('Error fetching options:', error);
    } finally {
      setIsFetchingOptions(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchOptions();
    }
  }, [open, fetchOptions]);

  useEffect(() => {
    if (target) {
      setType(target.type);
      setDescription(target.description);
      setUrl(target.url);
      setDomain(target.domain);
      setSelectedLanguages(target.languages || []);
      setNotes(target.notes || '');
    }
  }, [target]);

  const targetInitial: Target = target || {
    id: 0,
    name: '',
    type: '',
    description: '',
    url: '',
    domain: '',
    languages: [],
    notes: '',
  };

  const isChanged = (
    type !== (targetInitial.type || '') ||
    description !== (targetInitial.description || '') ||
    url !== (targetInitial.url || '') ||
    domain !== (targetInitial.domain || '') ||
    selectedLanguages.join(',') !== (targetInitial.languages || []).join(',') ||
    notes !== (targetInitial.notes || '')
  );

  const handleLanguageToggle = (lang: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const handleSubmit = async () => {
    if (!target?.id) {
      toast({
        title: 'Error',
        description: 'Target ID is missing',
        variant: 'destructive',
      });
      return;
    }

    if (!notes || !notes.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Notes field is required',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Send all fields to match backend expectations
      const updatePayload: any = {
        target_name: target.name,
        target_type: type || targetInitial.type,
        target_description: description || null,
        target_url: url || targetInitial.url,
        domain_name: domain || targetInitial.domain,
        lang_list: selectedLanguages.length > 0 ? selectedLanguages : (targetInitial.languages || []),
      };

      console.log('Updating target with payload:', updatePayload);
      console.log('Target ID:', target.id);

      const response = await fetch(API_ENDPOINTS.TARGET_UPDATE(target.id), {
        method: 'PUT',
        headers,
        body: JSON.stringify(updatePayload),
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          // Handle different error response formats
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // Pydantic validation errors
              errorMessage = errorData.detail.map((err: any) => {
                if (typeof err === 'string') return err;
                if (err.msg) return `${err.loc?.join('.') || 'field'}: ${err.msg}`;
                return JSON.stringify(err);
              }).join(', ');
            } else if (typeof errorData.detail === 'string') {
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
        title: 'Success',
        description: 'Target updated successfully',
      });

      if (onUpdateSuccess) {
        onUpdateSuccess();
      }

      onOpenChange(false);
    } catch (error) {
      console.error('Error updating target:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update target',
        variant: 'destructive',
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
        <div className="overflow-y-auto flex-1 pr-1 pl-1">
          <div className="space-y-4 pb-4">
            <Label className="text-base font-semibold">Target Name</Label>
            <Input value={target.name} className="bg-muted" />
          </div>
          <div className="space-y-4 pb-4">
            <Label className="text-base font-semibold">Target Type</Label>
            <Select value={type} onValueChange={setType} disabled={isFetchingOptions}>
              <SelectTrigger>
                <SelectValue placeholder={isFetchingOptions ? 'Loading...' : 'Select type'} />
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
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Description</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-muted min-h-[80px]"
              required
            />
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">URL</Label>
            <Input value={url} onChange={(e) => setUrl(e.target.value)} className="bg-muted" />
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Domain</Label>
            <Select value={domain} onValueChange={setDomain} disabled={isFetchingOptions}>
              <SelectTrigger>
                <SelectValue placeholder={isFetchingOptions ? 'Loading...' : 'Select domain'} />
              </SelectTrigger>
              <SelectContent className="bg-popover max-h-[300px]">
                {domainOptions.length === 0 && !isFetchingOptions ? (
                  <SelectItem value="" disabled>
                    No domains available
                  </SelectItem>
                ) : (
                  domainOptions.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1 pb-4">
            <Label className="text-base font-semibold">Languages</Label>
            <div className="bg-muted p-4 rounded-md max-h-[200px] overflow-y-auto">
              {isFetchingOptions ? (
                <div className="text-sm text-muted-foreground">Loading languages...</div>
              ) : languageOptions.length === 0 ? (
                <div className="text-sm text-muted-foreground">No languages available</div>
              ) : (
                <div className="space-y-2">
                  {languageOptions.map((lang) => (
                    <div key={lang} className="flex items-center space-x-2">
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
          />
          <Button
            onClick={handleSubmit}
            className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!isChanged || !notes || isLoading}
          >
            {isLoading ? 'Updating...' : 'Submit'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { TargetUpdateDialog };
