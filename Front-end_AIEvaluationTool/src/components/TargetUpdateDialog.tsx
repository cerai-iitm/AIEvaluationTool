import { useState, useEffect } from 'react';
import  {Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {Label} from '@/components/ui/label';
import {Textarea} from '@/components/ui/textarea';
import  { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import MultiSelect from 'multiselect'; // a custom component for multi-select with check icons

const domains = ['General', 'Education', 'Agriculture', 'Healthcare', 'Learning Disability'];
const languages = [ 'Tamil', 'Hindi', 'Gujarati', 'Bengali', 'Bhojpuri', 'English' ];

interface Target {
  id: number;
  name: string;
  type: string;
  description: string;
  url: string;
  domain: string;
  languages: string[];
//   notes: string;
}

interface TargetUpdateDialogProps {
  target: Target | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate: (target: Target) => void;  //???
  props: any
}

const language = ['Tamil', 'Hindi', 'Gujarati', 'Bengali', 'Bhojpuri', 'English'];

const targetType = ['WhatsApp', 'WebApp', 'Other'];

const Domain = ['General', 'Education', 'Agriculture', 'Healthcare', 'Learning Disability'];

export default function TargetUpdateDialog({ target, open, onOpenChange, onUpdate, props }: TargetUpdateDialogProps) {
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [domain, setDomain] = useState(domains[0]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (target) {
      setType(target.type);
      setDescription(target.description);
      setUrl(target.url);
      setDomain(target.domain);
      setSelectedLanguages(target.languages);
    //   setNotes(target.notes || '');
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
  };
  const isChanged = (
    type !== targetInitial.type ||
    description !== targetInitial.description ||
    url !== targetInitial.url ||
    domain !== targetInitial.domain ||
    selectedLanguages.join(',') !== targetInitial.languages.join(',')
  )

  const handleSubmit = () => {
    if (target) {
      onUpdate({
        ...target,
        type,
        description,
        url,
        domain,
        languages: selectedLanguages,
        // notes,
      });
      onOpenChange(false);
    }
  };

  
  type SelectSharedProps = {
    value: string;
    onValueChange: (value: string) => void;
  };

  type CustomSelectProps = {
    value: string;
    onValueChange: (value: string) => void;
    className: string;
  } & SelectSharedProps;

  const handleSelectChange = (props: CustomSelectProps) => {
    const { onValueChange } = props;
    onValueChange(props.value);
  };


  if (!target) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-w-3xl max-h-[90vh] overflow-y-auto'
        onOpenAutoFocus = { (e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className='sr-only'>Update Target</DialogTitle>
        </DialogHeader>
        <div className='overflow-y-auto flex-1 pr-1 pl-1'>
            <div className='space-y-4 pb-4'>
                <Label className='text-base font-semibold'>Target Name</Label>
                <Input value={target.name} readOnly className="bg-muted" />
            </div>
            <div className='space-y-4 pb-4'>
                <Label className='text-base font-semibold'>Target Type</Label>
                <Select value= {target.type} onValueChange={setType} className="bg-muted" {...(props as CustomSelectProps)}>
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent className='bg-popover max-h-[300px]'>
                        {targetType.map((type) =>(
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
            <div className='space-y-1 pb-4'>
                <Label className='text-base font-semibold'>Description</Label>
                <div className='relative'>
                        <Textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className='bg-muted min-h-[80px] pr-10'
            
                            required
                        />

                        
                </div>
            </div>
            <div className='space-y-1 pb-4'>
                <Label className='text-base font-semibold'>URL</Label>
                <Input value={target.url} className='bg-muted'></Input>
            </div>
            <div className='space-y-1 pb-4'>
                <Label className='text-base font-semibold'>Domain</Label>
                <Select value={target.domain} onValueChange={setDomain} className="bg-muted" {...(props as CustomSelectProps)}>
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent className='bg-popover max-h-[300px]'>
                        {domains.map((domain) =>(
                            <SelectItem key={domain} value={domain}>{domain}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
            <div className='space-y-1 pb-4'>
                <Label className='text-base font-semibold'>Languages</Label>
                <MultiSelect
                    options={languages}
                    value={selectedLanguages}
                    onValueChange={setSelectedLanguages}
                    className='bg-muted'
                />
            </div>
        </div>
 

        <div className='flex justify-center items-center p-4 border-gray-300 bg-white sticky bottom-0 z-10'>
            <Label className='text-base font-bold mr-2'>Notes :</Label>
            <Input value={notes} onChange={e => setNotes(e.target.value)}
                className='bg-gray-200 rounded px-4 py-1 mr-4 w-96'
            />
            <Button onClick={handleSubmit}
                className='bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800'
                disabled={!isChanged}
            >Update
            </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
