import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";



// Types
interface Domain {
  id: number;
  name: string;
}

const DomainList: React.FC = () => {
  const [domains, setDomains] = useState<Domain[]>([
    { id: 1, name: "General" },
    { id: 2, name: "Education" },
    { id: 3, name: "Agriculture" },
    { id: 4, name: "Healthcare" },
    { id: 5, name: "Learning Disability" }
  ]);

  const [searchQuery, setSearchQuery] = useState("");
  const [ currentPage, setCurrentPage ] = useState(1);
  const filteredDomains = domains.filter((domain) => 
    domain.name.toLowerCase().includes(searchQuery.toLowerCase()))

  const totalItems = filteredDomains.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  
  const PaginatedDomains = filteredDomains.slice(
    (currentPage -1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);



  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  // ADD - Dialog local state
  const [newDomainName, setNewDomainName] = useState("");
  const [addMessage, setAddMessage] = useState("");

  // UPDATE - Dialog local state
  const [updateName, setUpdateName] = useState("");

  useEffect(() => {
    if (selectedDomain) {
      setUpdateName(selectedDomain.name);
    }
  }, [selectedDomain]);

  // ADD handler
  const handleAdd = () => {
    if (newDomainName.trim() && addMessage.trim()) {
      setDomains([...domains, { id: domains.length + 1, name: newDomainName.trim() }]);
      setNewDomainName("");
      setAddMessage("");
      setAddOpen(false);
    }
  };

  // UPDATE handler
  const handleUpdate = () => {
    if (selectedDomain && updateName.trim()) {
      setDomains(domains.map(d =>
        d.id === selectedDomain.id ? { ...d, name: updateName.trim() } : d
      ));
      setSelectedDomain(null);
    }
  };

  // DELETE handler
  const handleDelete = () => {
    if (selectedDomain) {
      setDomains(domains.filter(d => d.id !== selectedDomain.id));
      setSelectedDomain(null);
    }
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Domains</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="Domain">
              <SelectTrigger className="w-48">
                <SelectValue/>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Domain">Domain Name</SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e)=> setSearchQuery(e.target.value)}
              className="w-64"
            />
            <div  className="ml-auto flex items-center gap-4">
              <span  className="text-sm text-muted-foreground">
                {totalItems === 0  ? "0" : `${(currentPage -1) * itemsPerPage +1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}`}
              </span>
              <div>
                <Button
                variant="ghost"
                size="icon"
                onClick ={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled = {currentPage === 1}
                >
                  <ChevronLeft className="w-5 h-5"></ChevronLeft>
                </Button>
                <Button
                variant='ghost'
                size='icon'
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p+1))}
                disabled = {currentPage === totalPages}
                >
                  <ChevronRight className="w-5 h-5"></ChevronRight>
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] max-w-[60vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">Domain ID</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Domain name</th>
                  </tr>
                </thead>
                <tbody>
                  {PaginatedDomains.map((row) => (
                    <tr 
                      key={row.id}
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => {setSelectedDomain(row);
                        setShowEditDialog(true);
                      }}
                    >
                      <td className="p-2 text-center">{row.id}</td>
                      <td className="p-2">{row.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="mt-6 sticky bottom-5">
            <button className="bg-primary hover:bg-primary/90 text-white  py-2 px-4 rounded" onClick={() => setAddOpen(true)} >
              + Add Domain
            </button>
          </div>

        </div>

      </main>

      {showEditDialog && selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[400px]">
            <button type="button" className="absolute top-3 right-4" onClick={() => setShowEditDialog(false)}>×</button>
            <div className="flex items-center justify-center mb-7 mt-5">
              <label className="font-semibold text-lg min-w-[165px]">Domain Name :</label>
              <span>{selectedDomain.name}</span>
            </div>
            <div className="flex gap-8 justify-center">
              <button
                className="px-8 py-2 bg-red-600 text-white rounded"
                onClick={() => {
                  handleDelete();
                  setShowEditDialog(false);
                }}
              >Delete</button>
              <button
                className="px-8 py-2 bg-blue-600 text-white rounded"
                onClick={() => {
                  setShowEditDialog(false);  // First close the action dialog
                  setShowUpdateModal(true);  // Then open the edit modal
                }}
              >Update</button>
            </div>
          </div>
        </div>
      )}


      {showUpdateModal && selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[500px] min-h-[220px]">
            <button type="button" className="absolute top-3 right-4" onClick={() => setShowUpdateModal(false)}>×</button>
            <div className="flex items-center mb-8 mt-5">
              <label className="font-semibold text-lg min-w-[165px]">Domain Name :</label>
              <input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-lg flex-1"
              />
            </div>
            <div className="flex justify-center">
              <label className=" text-lg min-w-[80px]"> Notes :</label>
              <input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                className={`ml-4 px-6 py-2 rounded text-lg font-semibold shadow transition ${updateName.trim() && addMessage.trim() ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" : "bg-green-300 text-white cursor-not-allowed"}`}
                disabled={!updateName.trim()}
                onClick={() => {
                  handleUpdate();
                  setShowUpdateModal(false);
                }}
              >Submit</button>
            </div>
          </div>
        </div>
      )}


      {/* Add Domain Dialog */}
      {addOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[500px] min-h-[300px] flex flex-col justify-between">
            <button
              type="button"
              className="absolute top-3 right-4 text-2xl font-bold  focus:outline-none"
              onClick={() => setAddOpen(false)}
              aria-label="Close"
            >
              ×
            </button>
            {/* Domain Name Row */}
            <div className="flex flex-col items-center justify-center flex-1">
            <div className="flex items-center mb-8">
              <label className="font-semibold text-lg min-w-[165px]">Domain Name </label>
              <input
                value={newDomainName}
                onChange={e => setNewDomainName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
                maxLength={150}
              />
            </div>
            </div>
            {/* Message Row + Submit Button */}
            <div className="flex items-center">
              <label className=" text-lg min-w-[80px]"> Notes :</label>
              <input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                type="button"
                className={`ml-4 px-6 py-2 rounded text-lg font-semibold shadow transition ${newDomainName.trim() && addMessage.trim() ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" : "bg-green-300 text-white cursor-not-allowed"}`}
                onClick={handleAdd}
              >
                Submit
              </button>
            </div>
          </div>
        </div>


      )}



      {/* Update/Delete Domain Dialog */}
      {/* {selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[400px] min-h-[180px]">
            <button
              type="button"
              className="absolute top-3 right-4 text-2xl font-bold  focus:outline-none"
              onClick={() => setSelectedDomain(null)}
              aria-label="Close"
            >×</button> */}
            {/* Domain Name Row */}
            {/* <div className="flex items-center justify-center mb-12 mt-7">
              <label className="font-semibold text-lg min-w-[165px]">Domain Name : </label>
              <input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div> */}
            {/* Action Buttons */}
            {/* <div className="flex gap-8 justify-center">
              <button
                className="px-8 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-base font-semibold shadow"
                onClick={handleDelete}
              >
                Delete
              </button>
              <button
                className={`px-8 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-base font-semibold shadow
                ${updateName.trim() ? "cursor-pointer" : "bg-blue-300 cursor-not-allowed"}`}
                onClick={handleUpdate}
                disabled={!updateName.trim()}
              >
                Update
              </button>
            </div>
          </div>
        </div>
      )} */}

      {/* Modal Styles */}
      <style>{`
        .modal {
          position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,.2);
          display: flex; align-items: center; justify-content: center; z-index: 1000;
        }
        .modal-content {
          background: #fff; border-radius: 8px; padding: 32px 32px 24px 32px; min-width: 350px; min-height: 190px; box-shadow: 0 2px 10px #0003;
          position: relative;
        }
        .close-btn {
          position: absolute; top: 12px; right: 18px; font-size: 22px; font-weight: bold; cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default DomainList;
