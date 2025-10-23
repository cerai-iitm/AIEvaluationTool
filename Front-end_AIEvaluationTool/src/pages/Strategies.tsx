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
interface Strategy {
  id: number;
  name: string;
  description: string;
}

const StrategyList: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([
    { id: 1, name: "robustness_advins", description: "" },
    { id: 2, name: "fairness_sterotype_query", description: "" },
    { id: 3, name: "language_detect_langdetect", description: "" },
    { id: 4, name: "safety_strategy", description: "" },
    { id: 5, name: "language_similarity_sarvam", description: "" },
    { id: 6, name: "String Matching - Wrong - Not implemented", description: "" },
    { id: 7, name: "robustness_advglue_mnli", description: "" },
    { id: 8, name: "hallucination_mc", description: "" },
    { id: 9, name: "grammatical_strategies", description: "" },
    { id: 10, name: "tat_tpm_mvh", description: "" },
    { id: 11, name: "language_detect_gt", description: "" },
    { id: 12, name: "detect_toxicity_using_perspective_api", description: "" },
    { id: 13, name: "indian_lang_grammatical_check", description: "" },
    { id: 14, name: "entity_recognition", description: "" },
    { id: 15, name: "truthfulness_internal_hotpot", description: "" },
    { id: 16, name: "compute_mtbf", description: "" },
    { id: 17, name: "strategy_17", description: "" },
    { id: 18, name: "strategy_18", description: "" },
    { id: 19, name: "strategy_19", description: "" },
    { id: 20, name: "strategy_20", description: "" },
    { id: 21, name: "strategy_21", description: "" },
    { id: 22, name: "strategy_22", description: "" },
    { id: 23, name: "strategy_23", description: "" },
    { id: 24, name: "strategy_24", description: "" },
    { id: 25, name: "strategy_25", description: "" },
    { id: 26, name: "strategy_26", description: "" },
    { id: 27, name: "strategy_27", description: "" },
    { id: 28, name: "strategy_28", description: "" },
    { id: 29, name: "strategy_29", description: "" },
    { id: 30, name: "strategy_30", description: "" },
    { id: 31, name: "strategy_31", description: "" },
    { id: 32, name: "strategy_32", description: "" },
    { id: 33, name: "strategy_33", description: "" },
    { id: 34, name: "strategy_34", description: "" },
    { id: 35, name: "strategy_35", description: "" },
    { id: 36, name: "strategy_36", description: "" },
    { id: 37, name: "strategy_37", description: "" },
    { id: 38, name: "strategy_38", description: "" },
    { id: 39, name: "strategy_39", description: "" },
    { id: 40, name: "strategy_40", description: "" },
    { id: 41, name: "strategy_41", description: "" },
    { id: 42, name: "strategy_42", description: "" },
    { id: 43, name: "strategy_43", description: "" },
    { id: 44, name: "strategy_44", description: "" },
  ]);

  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const filteredStrategies = strategies.filter((strategy) => 
    strategy.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredStrategies.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  
  const PaginatedStrategies = filteredStrategies.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  // ADD - Dialog local state
  const [newStrategyName, setNewStrategyName] = useState("");
  const [newStrategyDescription, setNewStrategyDescription] = useState("");
  const [addMessage, setAddMessage] = useState("");

  // UPDATE - Dialog local state
  const [updateName, setUpdateName] = useState("");
  const [updateDescription, setUpdateDescription] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  useEffect(() => {
    if (selectedStrategy) {
      setUpdateName(selectedStrategy.name);
      setUpdateDescription(selectedStrategy.description);
    }
  }, [selectedStrategy]);

  // ADD handler
  const handleAdd = () => {
    if (newStrategyName.trim() && addMessage.trim()) {
      setStrategies([...strategies, { 
        id: strategies.length + 1, 
        name: newStrategyName.trim(),
        description: newStrategyDescription.trim()
      }]);
      setNewStrategyName("");
      setNewStrategyDescription("");
      setAddMessage("");
      setAddOpen(false);
    }
  };

  // UPDATE handler
  const handleUpdate = () => {
    if (selectedStrategy && updateName.trim()) {
      setStrategies(strategies.map(s =>
        s.id === selectedStrategy.id ? { 
          ...s, 
          name: updateName.trim(),
          description: updateDescription.trim()
        } : s
      ));
      setSelectedStrategy(null);
    }
  };

  // DELETE handler
  const handleDelete = () => {
    if (selectedStrategy) {
      setStrategies(strategies.filter(s => s.id !== selectedStrategy.id));
      setSelectedStrategy(null);
    }
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[224px]">
        <div className="p-8 flex flex-col h-screen">
          <h1 className="text-4xl font-bold mb-8 text-center">Strategies</h1>

          <div className="flex gap-4 mb-6">
            <Select defaultValue="Strategy">
              <SelectTrigger className="w-48">
                <SelectValue/>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Strategy">Strategy Name</SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e)=> setSearchQuery(e.target.value)}
              className="w-64"
            />
            <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {totalItems === 0 ? "0" : `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}`}
              </span>
              <div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-5 h-5"></ChevronLeft>
                </Button>
                <Button
                  variant='ghost'
                  size='icon'
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-5 h-5"></ChevronRight>
                </Button>
              </div>
            </div>
          </div>
          
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] overflow-y-auto">
              <table className="w-full">
                <thead className="border-b-2">
                  <tr>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-center">Strategy ID</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Strategy Name</th>
                    <th className="sticky top-0 bg-white z-10 p-4 font-semibold text-left">Strategy Description</th>
                  </tr>
                </thead>
                <tbody>
                  {PaginatedStrategies.map((row) => (
                    <tr 
                      key={row.id}
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => {
                        setSelectedStrategy(row);
                        setShowEditDialog(true);
                      }}
                    >
                      <td className="p-2 text-center">{row.id}</td>
                      <td className="p-2">{row.name}</td>
                      <td className="p-2">{row.description || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="mt-6 sticky bottom-5">
            <button className="bg-primary hover:bg-primary/90 text-white py-2 px-4 rounded" onClick={() => setAddOpen(true)}>
              + Add Strategy
            </button>
          </div>
        </div>
      </main>

      {/* Edit Dialog - Shows Delete and Update buttons */}
      {showEditDialog && selectedStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[400px]">
            <button type="button" className="absolute top-3 right-4" onClick={() => setShowEditDialog(false)}>×</button>
            <div className="flex items-center justify-center mb-7 mt-5">
              <label className="font-semibold text-lg min-w-[165px]">Strategy Name :</label>
              <span>{selectedStrategy.name}</span>
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
                  setShowEditDialog(false);
                  setShowUpdateModal(true);
                }}
              >Update</button>
            </div>
          </div>
        </div>
      )}

      {/* Update Modal */}
      {showUpdateModal && selectedStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[500px] min-h-[300px]">
            <button type="button" className="absolute top-3 right-4" onClick={() => setShowUpdateModal(false)}>×</button>
            
            <div className="flex items-center mb-6 mt-5">
              <label className="font-semibold text-lg min-w-[165px]">Strategy Name :</label>
              <input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-lg flex-1"
              />
            </div>
            
            <div className="flex items-start mb-6">
              <label className="font-semibold text-lg min-w-[165px] mt-2">Strategy Description :</label>
              <textarea
                value={updateDescription}
                onChange={e => setUpdateDescription(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-lg flex-1 min-h-[80px] resize-none"
                placeholder="Enter strategy description..."
              />
            </div>
            
            <div className="flex items-center">
              <label className="text-lg min-w-[80px]">Notes :</label>
              <input
                value={updateMessage}
                onChange={e => setUpdateMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                className={`ml-4 px-6 py-2 rounded text-lg font-semibold shadow transition ${updateName.trim() && updateMessage.trim() ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" : "bg-green-300 text-white cursor-not-allowed"}`}
                disabled={!updateName.trim() || !updateMessage.trim()}
                onClick={() => {
                  handleUpdate();
                  setShowUpdateModal(false);
                }}
              >Submit</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Strategy Dialog */}
      {addOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50">
          <div className="relative bg-white rounded-lg shadow-xl px-8 pt-8 pb-6 min-w-[500px] min-h-[350px] flex flex-col justify-between">
            <button
              type="button"
              className="absolute top-3 right-4 text-2xl font-bold focus:outline-none"
              onClick={() => setAddOpen(false)}
              aria-label="Close"
            >
              ×
            </button>
            
            <div className="flex flex-col items-center justify-center flex-1">
              <div className="flex items-center mb-6">
                <label className="font-semibold text-lg min-w-[165px]">Strategy Name :</label>
                <input
                  value={newStrategyName}
                  onChange={e => setNewStrategyName(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
                  maxLength={150}
                />
              </div>
              
              <div className="flex items-start mb-6">
                <label className="font-semibold text-lg min-w-[165px] mt-2">Strategy Description :</label>
                <textarea
                  value={newStrategyDescription}
                  onChange={e => setNewStrategyDescription(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 min-h-[80px] resize-none focus:outline-none focus:ring focus:ring-blue-200"
                  placeholder="Enter strategy description..."
                />
              </div>
            </div>
            
            <div className="flex items-center">
              <label className="text-lg min-w-[80px]">Message :</label>
              <input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-4 py-2 text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                type="button"
                className={`ml-4 px-6 py-2 rounded text-lg font-semibold shadow transition ${newStrategyName.trim() && addMessage.trim() ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" : "bg-green-300 text-white cursor-not-allowed"}`}
                onClick={handleAdd}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

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

export default StrategyList;
