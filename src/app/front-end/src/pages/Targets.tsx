import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import {Input} from '@/components/ui/input';
import {Textarea} from '@/components/ui/textarea';
import {Button} from '@/components/ui/button';
import  {Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import  {Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Label } from '@/components/ui/label';
import TargetUpdateDialog from '@/components/TargetUpdateDialog';
// import TargetAddDialog from '@/components/TargetAddDialog';

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

// Example target data
const initialTargets: Target[] = [
  { 
    id: 1, 
    name: 'Gooey', 
    type: 'WhatsApp', 
    description: 'Gooey AI is a WhatsApp-based AI assistant for farmers, providing information and assistance on agricultural practices and crop management.', 
    url: 'https://wa.me/88220323028', 
    domain: 'General', 
    languages: ['Tamil', 'Hindi', 'Gujarati'] 
},
  { id: 2, 
    name: 'Vaidya AI', 
    type: 'WhatsApp', 
    description: 'Vaidya AI is a WhatsApp-based AI assistant for providing healthcare advices.', 
    url: 'https://wa.me/8828808350', 
    domain: 'Healthcare', 
    languages: ['Tamil', 'Hindi', 'Gujarati', 'Bengali', 'English'] 
},
  // ...Add more objects as needed
];

const Targets = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);
  const [updateTarget, setUpdateTarget] = useState<Target | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [targets, setTargets] = useState<Target[]>(initialTargets);
  const [ currentPage, setCurrentPage ] = useState(1);

  const filteredTargets = targets.filter(
    t =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.domain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredTargets.length;
  const itemsPerPage = 20;
  const TotalPages = Math.ceil(totalItems / itemsPerPage);

  //Pagination logic: get items for current page
  const paginatedTargets = filteredTargets.slice(
    (currentPage -1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const handleUrlClick = (url: string) => {
    window.open(url, '_blank');
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-224px bg-[#5252c2] z-20">
        <Sidebar />
      </aside>
      <main className="flex-1 bg-background ml-[224px] ">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Targets</h1>
          <div className="flex gap-4 mb-6">
            <Select defaultValue="target">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="target">Target Name</SelectItem>
                <SelectItem value="type">Target Type</SelectItem>
                <SelectItem value="domain">Domain Name</SelectItem>
              </SelectContent>
            </Select>
            <Input placeholder="search" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-64" />
            {/* <Button className="ml-auto" onClick={() => setAddDialogOpen(true)}>+ Add Target</Button> */}
            <div className="ml-auto flex items-center gap-4">
                <span className='test-sm text-muted-foreground'>
                    { 
                        totalItems === 0
                        ? "0"
                        : `${(currentPage -1) * itemsPerPage +1} - ${Math.min(
                            currentPage * itemsPerPage,
                            totalItems
                        )} of ${totalItems}`
                    }
                </span>
                <div className="flex gap-1">
                    <Button
                        variant="ghost"
                        size ="icon"
                        onClick={()=> setCurrentPage((p) => Math.max(1, p-1))}
                        disabled={currentPage === 1}
                    >
                        <ChevronLeft className="w-5 h-5"/>
                    </Button>
                    <Button
                        variant='ghost'
                        size='icon'
                        onClick={()=>
                            setCurrentPage((p) => Math.min(TotalPages, p+1))
                        }
                        disabled = { currentPage === TotalPages}
                    >
                        <ChevronRight className="w-5 h-5"/>
                    </Button>
                </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] overflow-y-auto">
            <table className="w-full">
              <thead className="border-b-2">
                <tr>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Target ID</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Target Name</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Target Type & URL</th>
                  <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Domain Name</th>
                </tr>
              </thead>
              <tbody>
                {filteredTargets.map(target => (
                  <tr key={target.id} className="border-b-2 cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedTarget(target)}>
                    <td className="p-2">{target.id}</td>
                    <td className="p-2">{target.name}</td>
                    <td className="p-2">
                      <span onClick={e => { e.stopPropagation(); handleUrlClick(target.url); }} style={{ color: '#3b82f6', textDecoration: 'underline', cursor: 'pointer' }}>
                        {target.type}
                      </span>
                    </td>
                    <td className="p-2">{target.domain}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className='mt-6 sticky bottom-5'>
                <Button
                    className='bg-primary hover:bg-primary/90'
                    onClick={() => setAddDialogOpen(true)}
                >
                    + Add Target
                </Button>
        </div>
        </div>
      </main>

        {/* Details/Edit Dialog */}
        <Dialog open={!!selectedTarget} onOpenChange={() => setSelectedTarget(null)}>
          <DialogContent
            className="max-w-3xl max-h-[90vh] overflow-y-auto"
            onOpenAutoFocus = {(e) => e.preventDefault()}
          >
            <DialogHeader>
                <DialogTitle className='sr-only'>
                    Target Details
                </DialogTitle>
            </DialogHeader>
            {/* ...show target details... */}
            {selectedTarget && (
              <div className='flex-1 p-1 overflow-y-auto space-y-6 pb-5'>
                <div className="space-y-1">
                    <Label className = 'text-base font-semibold'>Target Name</Label>
                    <Input value={selectedTarget.name} readOnly className='bg-muted'></Input>
                </div>
                <div className="space-y-1">
                    <Label className = 'text-base font-semibold'>Type</Label>
                    <Input value={selectedTarget.type} readOnly className='bg-muted'></Input>
                </div>
                <div className='space-y-1'>
                    <Label className = 'text-base font-semibold'>Description</Label>
                    <Textarea value={selectedTarget.description} readOnly className='bg-muted min-h-[80px]'></Textarea>
                </div>
                <div className="space-y-1">
                    <Label className = 'text-base font-semibold'>URL</Label>
                    <Input value={selectedTarget.url} readOnly className='bg-muted'></Input>
                </div>
                <div className="space-y-1">
                    <Label className = 'text-base font-semibold'>Domain</Label>
                    <Input value={selectedTarget.domain} readOnly className='bg-muted'></Input>
                </div>
                <div className="space-y-1">
                    <Label className = 'text-base font-semibold'>Languages</Label>
                    <Input value={selectedTarget.languages.join(', ')} readOnly className='bg-muted'></Input>
                </div>
                

              </div>
              
            )}
            <div className="sticky bottom-0 pt-4 flex justify-center gap-4 border-gray-200 z-10">
                <Button
                    variant='destructive'
                >
                    Delete
                </Button>
                <Button
                    className="bg-primary hover:bg-primary/90"
                    onClick={() => {
                        setUpdateTarget(selectedTarget);
                        setSelectedTarget(null);

                    }}
                >
                    Update
                </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* // Update Target Dialog */}
        {/* <TargetUpdateDialog
          target={updateTarget}
          open={!!updateTarget}
          onOpenChange={(open) => !open && setUpdateTarget(null)}
          onUpdate={updated => {
            setTargets(ts => ts.map(t => t.id === updated.id ? updated : t));
            setUpdateTarget(null);
          }}
        /> */}

        {/* Add Target Dialog
        <TargetAddDialog
          open={addDialogOpen}
          onOpenChange={setAddDialogOpen}
          onAdd={newTarget => {
            setTargets(ts => [...ts, { ...newTarget, id: ts.length ? ts[ts.length - 1].id + 1 : 1 }]);
            setAddDialogOpen(false);
          }}
          existingNames={targets.map(t => t.name)}
        /> */}
      
    </div>
  );
};

export default Targets;
