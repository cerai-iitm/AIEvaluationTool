import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import  {Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import  {Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Label } from '@/components/ui/label';


interface Language {
    id : number;
    name : string;
}


// seed data - you can fetch this from an API instead
const initialLanguages: Language[] = [
    {id:1, name: "Auto"},
    {id:2, name: "English"},
    {id:3, name: "Telugu"},
    {id:4, name: "Bhojpuri"},
    {id:5, name: "Hindi"},
    {id:6, name: "Kannada"},
    {id:7, name: "Bengali"},
    {id:8, name: "Gujarati"},
    {id:9, name: "Marathi"}
];

const itemsPerPage = 20;

const LanguageList: React.FC = () => {
    const [languages, setLanguages] = useState<Language[]>(initialLanguages);
    const [searchQuery, setSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);


    // Filter and pagination data
    const filteredLanguages = languages.filter(lang => 
        lang.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    const totalItems = filteredLanguages.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

    const paginatedLanguages = filteredLanguages.slice(
        (currentPage -1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    const [showEditDialog, setShowEditDialog] = useState(false);
    const [ showUpdateModal, setShowUpdateModal ] = useState(false);

    const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null);
    const [addOpen, setAddOpen] = useState(false);

    // Add - Dialog local state
    const [newLanguageName, setNewLanguageName] = useState("");
    const [ addMessage, setAddMessage ] = useState("");

    // Update - Dialog local state
    const [ updateName, setUpdateName ] = useState("");


    useEffect(() => {
        if (selectedLanguage) {
            setUpdateName(selectedLanguage.name);

        }
    },[selectedLanguage]);

    // add handler
    const handleAdd = () =>{
        if (newLanguageName.trim() && addMessage.trim()){
            setLanguages([
                ...languages,
                {id: languages.length +1, name: newLanguageName.trim()}
            ]);
            setNewLanguageName("");
            setAddMessage("");
            setAddOpen(false);
        }
    };

    // update handler
    const handleUpdate = () => {
        if (selectedLanguage && updateName.trim()) {
            setLanguages(languages.map(l =>
                l.id === selectedLanguage.id ? { ...l, name: updateName.trim() } : l
            ));
            setSelectedLanguage(null);
        }
    };

    // delete handler
    const handleDelete = () => {
        if (selectedLanguage) {
            setLanguages(languages.filter(l => l.id !== selectedLanguage.id));
            setSelectedLanguage(null);
        }
    }


    const handleAddLanguage = () => {
        if (newLanguageName.trim() ){
            setLanguages([
                ...languages,
                {id: languages.length +1, name: newLanguageName.trim()}
            ]);
            setAddOpen(false);
            setNewLanguageName("");
        }
    };

    return (
        
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Languages</h1>

          {/* Filter/Search Bar */}
          <div className="flex gap-4 mb-6">
            <Select defaultValue="Language Name">
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Language Name">Language Name</SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder="search"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-64"
            />
            <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {totalItems ? `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}` : "0"}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Table */}
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] max-w-[60vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">Language ID</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Language Name</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLanguages.map(lang => (
                    <tr key={lang.id} className="border-b hover:bg-muted50 cursor-pointer">
                      <td className="p-2 text-center">{lang.id}</td>
                      <td className="p-2">{lang.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Add Language Button */}
            <div className="mt-6 sticky bottom-5">
              <button className="bg-primary hover:bg-primary90 text-white py-2 px-4 rounded" onClick={() => setAddOpen(true)}>
                + Add Language
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Add Language Dialog */}
      {addOpen && (
        <Dialog open={addOpen} onOpenChange={setAddOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Language</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-6">
              <Label>Language Name</Label>
              <Input value={newLanguageName} onChange={e => setNewLanguageName(e.target.value)} placeholder="Enter language name..." maxLength={100} />
              <Button onClick={handleAddLanguage} disabled={!newLanguageName.trim()}>
                Submit
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  
    )
};

export default LanguageList;