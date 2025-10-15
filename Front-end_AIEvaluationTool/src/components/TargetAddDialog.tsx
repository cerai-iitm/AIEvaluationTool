import { useState } from 'react';
import  {Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {Input} from '@/components/ui/input';
import {Button }from '@/components/ui/button';
import {Label} from '@/components/ui/label';
import {Textarea} from '@/components/ui/textarea';
import  {Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import MultiSelect from 'multiselect'

const domains = ['General', 'Education', 'Agriculture', 'Healthcare', 'Learning Disability'];
const languages = [ 'Tamil', 'Hindi', 'Gujarati', 'Bengali', 'Bhojpuri', 'English' ];

interface Target {
  id?: number;
  name: string;
  type: string;
  description: string;
  url: string;
  domain: string;
  languages: string[];
  notes: string;
}

interface TargetAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (target: Target) => void;
  existingNames: string[];
}

export default function TargetAddDialog({ open, onOpenChange, onAdd, existingNames }: TargetAddDialogProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [domain, setDomain] = useState(domains[0]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [notes, setNotes] = useState('');

  // Unique name validation
  const isNameValid = name && !existingNames.includes(name);

  const handleSubmit = () => {
    if (isNameValid) {
      onAdd({
        name,
        type,
        description,
        url,
        domain,
        languages: selectedLanguages,
        notes,
      });
      setName('');
      setType('');
      setDescription('');
      setUrl('');
      setDomain(domains[0]);
      setSelectedLanguages([]);
      setNotes('');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Target</DialogTitle>
        </DialogHeader>
        <Label>Target Name</Label>
        <Input value={name} onChange={e => setName(e.target.value)} placeholder="Enter unique name" />
        {!isNameValid && name && <span style={{ color: 'red' }}>Name already exists or is invalid</span>}

        <Label>Target Type</Label>
        <Input value={type} onChange={e => setType(e.target.value)} placeholder="Type (e.g. WhatsApp)" />

        <Label>Description</Label>
        <Textarea value={description} onChange={e => setDescription(e.target.value)} />

        <Label>URL</Label>
        <Input value={url} onChange={e => setUrl(e.target.value)} />

        <Label>Domain Name</Label>
        <Select value={domain} onValueChange={setDomain}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {domains.map(d => (
              <SelectItem key={d} value={d}>{d}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Label>Languages</Label>
        <MultiSelect
          options={languages}
          selected={selectedLanguages}
          onChange={setSelectedLanguages}
          withCheckIcon
        />

        <Label>Notes</Label>
        <Input value={notes} onChange={e => setNotes(e.target.value)} />

        <div className="flex justify-end gap-4 mt-4">
          <Button onClick={handleSubmit} disabled={!isNameValid}>Add</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
