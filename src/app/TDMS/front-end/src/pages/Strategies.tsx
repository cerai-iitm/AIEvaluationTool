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
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";
import { hasPermission } from "@/utils/permissions";
import { HistoryButton } from "@/components/HistoryButton";
import { set } from "date-fns";

// Types
interface Strategy {
  strategy_id: number;
  strategy_name: string;
  strategy_description: string | null;
}

const StrategyList: React.FC = () => {
  const { toast } = useToast();
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  
  const filteredStrategies = strategies.filter((strategy) => 
    strategy.strategy_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredStrategies.length;
  const itemsPerPage = 15;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  
  const PaginatedStrategies = filteredStrategies.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
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

  const [refreshKey, setRefreshKey] = useState(0);

  const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);

  // Fetch strategies from API
  const fetchStrategies = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.STRATEGIES_V2, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Map API response to match our interface
      const mappedStrategies: Strategy[] = data.map((strategy: any) => ({
        strategy_id: strategy.strategy_id,
        strategy_name: strategy.strategy_name,
        strategy_description: strategy.strategy_description || ""
      }));
      setStrategies(mappedStrategies);
    } catch (error) {
      console.error("Error fetching strategies:", error);
      toast({
        title: "Error",
        description: "Failed to fetch strategies. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const response = await fetch(API_ENDPOINTS.CURRENT_USER, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCurrentUserRole(userData.role || "");
        }
      } catch (error) {
        console.error("Error fetching user role:", error);
      }
    };

    fetchUserRole();
    fetchStrategies();
  }, [refreshKey]);

  // const handleUpdateSuccess = () => {
  //   setRefreshKey((prev) => prev + 1); // Trigger refresh
  // };

  useEffect(() => {
    if (selectedStrategy) {
      setUpdateName(selectedStrategy.strategy_name);
      setUpdateDescription(selectedStrategy.strategy_description || "");
    }
  }, [selectedStrategy]);

  // ADD handler
  const handleAdd = async () => {
    if (!newStrategyName.trim() || !addMessage.trim()) {
      toast({
        title: "Validation Error",
        description: "Strategy name and notes are required",
        variant: "destructive",
      });
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.STRATEGY_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify({
          strategy_name: newStrategyName.trim(),
          strategy_description: newStrategyDescription.trim() || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast({
        title: "Success",
        description: "Strategy created successfully",
        variant: "default",
      });
      
      setNewStrategyName("");
      setNewStrategyDescription("");
      setAddMessage("");
      setAddOpen(false);
      fetchStrategies(); // Refresh the list
      setHighlightedRowId(data.strategy_id);
    } catch (error: any) {
      console.error("Error creating strategy:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to create strategy. Please try again.",
        variant: "destructive",
      });
    }
  };

  // UPDATE handler
  const handleUpdate = async () => {
    if (!selectedStrategy || !updateName.trim() || !updateMessage.trim()) {
      toast({
        title: "Validation Error",
        description: "Strategy name and notes are required",
        variant: "destructive",
      });
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.STRATEGY_UPDATE_V2(selectedStrategy.strategy_id), {
        method: "PUT",
        headers,
        body: JSON.stringify({
          strategy_name: updateName.trim(),
          strategy_description: updateDescription.trim() || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Strategy updated successfully",
        variant: "default",
      });
      
      setShowUpdateModal(false);
      setSelectedStrategy(null);
      fetchStrategies(); // Refresh the list
      // setAddMessage("");
      //setHighlightedRowId(selectedStrategy.strategy_id);
    } catch (error: any) {
      console.error("Error updating strategy:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to update strategy. Please try again.",
        variant: "destructive",
      });
    }
  };

  // DELETE handler
  const handleDelete = async () => {
    if (!selectedStrategy) return;

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.STRATEGY_DELETE_V2(selectedStrategy.strategy_id), {
        method: "DELETE",
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Strategy deleted successfully",
        variant: "default",
      });
      
      setShowDeleteConfirm(false);
      setShowEditDialog(false);
      setSelectedStrategy(null);
      fetchStrategies(); // Refresh the list
      setHighlightedRowId(null);
      
    } catch (error: any) {
      console.error("Error deleting strategy:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to delete strategy. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[220px] md:ml-[224px]">
        <div className="p-4 md:p-8 flex flex-col h-screen">
          <h1 className="text-2xl md:text-4xl font-bold mb-4 md:mb-8 text-center">Strategies</h1>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Select defaultValue="Strategy">
              {/* <SelectTrigger className="w-full sm:w-48">
                <SelectValue/>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Strategy">Strategy Name</SelectItem>
              </SelectContent> */}
            </Select>
            <Input
              placeholder="search"
              value={searchQuery}
              onChange={(e)=> {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full sm:w-64"
            />
            <div className="ml-auto flex items-center gap-2 md:gap-4">
              <HistoryButton
                entityType="Strategy"
                title="Strategies"
                idField="strategyId"
                idLabel="Strategy ID"
              />
              <span className="text-xs sm:text-sm text-muted-foreground">
                {totalItems === 0 ? "0" : `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}`}
              </span>
              <div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4 md:w-5 md:h-5"></ChevronLeft>
                </Button>
                <Button
                  variant='ghost'
                  size='icon'
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4 md:w-5 md:h-5"></ChevronRight>
                </Button>
              </div>
            </div>
          </div>
          
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[70vh] max-w-[120vh] overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center p-8">
                  <span>Loading...</span>
                </div>
              ) : (
                <table className="w-full table-fixed">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 z-10 p-4 font-semibold text-left w-[15%] ">Strategy ID</th>
                      <th className="sticky top-0 z-10 p-2 font-semibold text-left w-[30%]">Strategy Name</th>
                      <th className="sticky top-0 z-10 pl-8 p-2 font-semibold text-left ">Strategy Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PaginatedStrategies.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="p-4 text-center text-muted-foreground">
                          No strategies found
                        </td>
                      </tr>
                    ) : (
                      PaginatedStrategies.map((row) => (
                        <tr 
                          key={row.strategy_id}
                          className={`border-b cursor-pointer transition-colors duration-200 ${
                            highlightedRowId === row.strategy_id ? "bg-primary/10 hover:bg-primary/15 border-primary/30" : "hover:bg-muted/50"
                          }`}
                          onClick={() => {
                            setSelectedStrategy(row);
                            setShowEditDialog(true);
                            setHighlightedRowId(row.strategy_id);
                          }}
                        >
                          <td className="p-2 pl-12">{row.strategy_id}</td>
                          <td className="p-2 truncate">{row.strategy_name}</td>
                          <td className="p-2 max-w-md truncate">{row.strategy_description || ""}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>
          
          {(hasPermission(currentUserRole, "canCreateTables") ||
            hasPermission(currentUserRole, "canCreateRecords")) && (
            <div className="mt-4 md:mt-6 sticky bottom-5">
              <button 
                className="bg-primary hover:bg-primary/90 text-white py-2 px-4 rounded text-sm md:text-base transition-colors" 
                onClick={() => setAddOpen(true)}
              >
                + Add Strategy
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Edit Dialog - Shows Delete and Update buttons */}
      {showEditDialog && selectedStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick = {() => {
            setShowEditDialog(false);
            setSelectedStrategy(null);
            setUpdateMessage("");
          }}
        >
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowEditDialog(false);
                setSelectedStrategy(null);
              }}
            >
              ×
            </button>
            <div className="flex flex-col items-left justify-center mb-6 md:mb-7 mt-4 md:mt-5 gap-4 ">
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Strategy Name</label>
                <Input className="bg-muted text-sm md:text-base" value={selectedStrategy.strategy_name} readOnly />
              </div>
              {/* if strategy description is null, don't render it */}
              {selectedStrategy.strategy_description && (
                <div className="flex flex-col gap-1">
                  <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Strategy Description</label>
                  <Textarea className="text-sm md:text-base min-h-[80px] flex-1 w-full md:w-auto resize-none bg-muted" readOnly>{selectedStrategy.strategy_description}</Textarea>
                </div>
              )}
              {/* <div className="flex flex-col gap-2 md:gap-3">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Strategy Description :</label>
                
                <Textarea className="text-sm md:text-base min-h-[80px] flex-1 w-full md:w-auto resize-none bg-muted" readOnly>{selectedStrategy.strategy_description}</Textarea>
              </div> */}
            </div>
            <div className="flex gap-4 md:gap-8 justify-center">
              {hasPermission(currentUserRole, "canDeleteTables") && (
                <button
                  className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                  onClick={() =>{
                    handleDeleteClick;
                    setShowEditDialog(false);
                    setShowDeleteConfirm(true);
                  }}
                >
                  Delete
                </button>
              )}
              {(hasPermission(currentUserRole, "canUpdateTables") ||
                hasPermission(currentUserRole, "canUpdateRecords")) && (
                <button
                  className="px-6 md:px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm md:text-base transition-colors"
                  onClick={() => {
                    setShowEditDialog(false);
                    setShowUpdateModal(true);
                    setUpdateMessage("");
                  }}
                >
                  <p className="text-white px-2.5">Edit</p>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && selectedStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick={() => {
            setShowUpdateModal(false);
            setSelectedStrategy(null);
            setShowDeleteConfirm(false);
          }}
        >
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowDeleteConfirm(false);
                setShowUpdateModal(false);
              }}
            >
              x
            </button>
            <div className="mt-4 md:mt-6">
              <p className="text-base md:text-lg font-normal mb-4 text-center">
                Are you sure you want to delete the following Strategy? This action cannot be undone.
              </p>
              <div className="mb-6">
                <p className="text-sm md:text-base text-center capitalize font-semibold">
                  <span className="font-medium">Strategy Name :</span> {selectedStrategy.strategy_name}
                </p>
              </div>
              <div className="flex gap-4 justify-center">
                {/* <button
                  className="px-6 md:px-8 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded text-sm md:text-base transition-colors"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </button> */}
                <button
                  className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                  onClick={handleDelete}
                >
                  Confirm Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Update Modal */}
      {showUpdateModal && selectedStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick = {() => {
            setShowUpdateModal(false);
            setSelectedStrategy(null);
            setUpdateMessage("");
          }}
        >
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[300px]"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowUpdateModal(false);
                setSelectedStrategy(null);
                
              }}
            >
              ×
            </button>
            
            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 mt-4 md:mt-5 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Strategy Name :</label>
              <Input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div>
            
            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Strategy Description :</label>
              <Textarea
                value={updateDescription}
                onChange={e => setUpdateDescription(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto min-h-[80px] resize-none focus:outline-none focus:ring focus:ring-blue-200"
                placeholder="Enter strategy description..."
              />
            </div>
            
            <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[60px]">Notes </label>
              <Input
                value={updateMessage}
                onChange={e => setUpdateMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                className={`mt-2 md:mt-0 md:ml-4 px-6 py-2 rounded text-sm md:text-lg font-semibold shadow transition ${
                  updateName.trim() && updateMessage.trim() 
                    ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" 
                    : "bg-green-300 text-white cursor-not-allowed"
                }`}
                disabled={!updateName.trim() || !updateMessage.trim()}
                onClick={handleUpdate}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Strategy Dialog */}
      {addOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick={() => {
            setAddOpen(false);
            setAddMessage("");
          }}
        >
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[350px] flex flex-col justify-between"
            onClick={e => e.stopPropagation()}
          >
            <button
              type="button"
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors focus:outline-none"
              onClick={() => {
                setAddOpen(false);
                setNewStrategyDescription("");
                setNewStrategyName("");
              }}
              aria-label="Close"
            >
              ×
            </button>
            
            <div className="flex flex-col items-center justify-center flex-1">
              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Strategy Name :</label>
                <Input
                  value={newStrategyName}
                  onChange={e => setNewStrategyName(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                  maxLength={150}
                />
              </div>
              
              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Strategy Description :</label>
                <Textarea
                  value={newStrategyDescription}
                  onChange={e => setNewStrategyDescription(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto min-h-[80px] resize-none focus:outline-none focus:ring focus:ring-blue-200"
                  placeholder="Enter strategy description..."
                />
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[60px]">Notes</label>
              <Input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                type="button"
                className={`mt-2 md:mt-0 md:ml-4 px-6 py-2 rounded text-sm md:text-lg font-semibold shadow transition ${
                  newStrategyName.trim() && addMessage.trim() && newStrategyDescription.trim()
                    ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" 
                    : "bg-green-300 text-white cursor-not-allowed"
                }`}
                onClick={handleAdd}
                disabled={!newStrategyName.trim() || !newStrategyDescription.trim() || !addMessage.trim()}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyList;
