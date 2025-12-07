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

// Types
interface Domain {
  domain_id: number;
  domain_name: string;
}

const DomainList: React.FC = () => {
  const { toast } = useToast();
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  
  const filteredDomains = domains.filter((domain) => 
    domain.domain_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredDomains.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  
  const PaginatedDomains = filteredDomains.slice(
    (currentPage -1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  // ADD - Dialog local state
  const [newDomainName, setNewDomainName] = useState("");
  const [addMessage, setAddMessage] = useState("");

  // UPDATE - Dialog local state
  const [updateName, setUpdateName] = useState("");

  // Fetch domains from API
  const fetchDomains = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.DOMAINS_V2, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Map API response to match our interface
      const mappedDomains: Domain[] = data.map((domain: any) => ({
        domain_id: domain.domain_id,
        domain_name: domain.domain_name
      }));
      setDomains(mappedDomains);
    } catch (error) {
      console.error("Error fetching domains:", error);
      toast({
        title: "Error",
        description: "Failed to fetch domains. Please try again.",
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
    fetchDomains();
  }, []);

  useEffect(() => {
    if (selectedDomain) {
      setUpdateName(selectedDomain.domain_name);
    }
  }, [selectedDomain]);

  // ADD handler
  const handleAdd = async () => {
    if (!newDomainName.trim() || !addMessage.trim()) {
      toast({
        title: "Validation Error",
        description: "Domain name and notes are required",
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

      const response = await fetch(API_ENDPOINTS.DOMAIN_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify({
          domain_name: newDomainName.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast({
        title: "Success",
        description: "Domain created successfully",
        variant: "default",
      });
      
      setNewDomainName("");
      setAddMessage("");
      setAddOpen(false);
      fetchDomains(); // Refresh the list
    } catch (error: any) {
      console.error("Error creating domain:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to create domain. Please try again.",
        variant: "destructive",
      });
    }
  };

  // UPDATE handler
  const handleUpdate = async () => {
    if (!selectedDomain || !updateName.trim() || !addMessage.trim()) {
      toast({
        title: "Validation Error",
        description: "Domain name and notes are required",
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

      const response = await fetch(API_ENDPOINTS.DOMAIN_UPDATE_V2(selectedDomain.domain_id), {
        method: "PUT",
        headers,
        body: JSON.stringify({
          domain_name: updateName.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Domain updated successfully",
        variant: "default",
      });
      
      setShowUpdateModal(false);
      setSelectedDomain(null);
      fetchDomains(); // Refresh the list
    } catch (error: any) {
      console.error("Error updating domain:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to update domain. Please try again.",
        variant: "destructive",
      });
    }
  };

  // DELETE handler
  const handleDelete = async () => {
    if (!selectedDomain) return;

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.DOMAIN_DELETE_V2(selectedDomain.domain_id), {
        method: "DELETE",
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Domain deleted successfully",
        variant: "default",
      });
      
      setShowDeleteConfirm(false);
      setShowEditDialog(false);
      setSelectedDomain(null);
      fetchDomains(); // Refresh the list
    } catch (error: any) {
      console.error("Error deleting domain:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to delete domain. Please try again.",
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
          <h1 className="text-2xl md:text-4xl font-bold mb-4 md:mb-8 text-center">Domains</h1>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Select defaultValue="Domain">
              <SelectTrigger className="w-full sm:w-48">
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
              className="w-full sm:w-64"
            />
            <div className="ml-auto flex items-center gap-2 md:gap-4">
              <span className="text-xs sm:text-sm text-muted-foreground">
                {totalItems === 0 ? "0" : `${(currentPage -1) * itemsPerPage +1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}`}
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
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p+1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4 md:w-5 md:h-5"></ChevronRight>
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] max-w-[60vh] overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center p-8">
                  <span>Loading...</span>
                </div>
              ) : (
                <table className="w-full min-w-[400px] ">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-center text-xs md:text-base">Domain ID</th>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-left text-xs md:text-base">Domain name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PaginatedDomains.length === 0 ? (
                      <tr>
                        <td colSpan={2} className="p-4 text-center text-muted-foreground">
                          No domains found
                        </td>
                      </tr>
                    ) : (
                      PaginatedDomains.map((row) => (
                        <tr 
                          key={row.domain_id}
                          className="border-b hover:bg-muted/50 cursor-pointer transition-colors"
                          onClick={() => {
                            setSelectedDomain(row);
                            setShowEditDialog(true);
                          }}
                        >
                          <td className="p-2 text-center text-xs md:text-base">{row.domain_id}</td>
                          <td className="p-2 text-xs md:text-base">{row.domain_name}</td>
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
                + Add Domain
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Edit Dialog - Similar to original but with delete confirmation */}
      {showEditDialog && selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md">
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowEditDialog(false);
                setSelectedDomain(null);
              }}
            >
              ×
            </button>
            <div className="flex items-center justify-center mb-6 md:mb-7 mt-4 md:mt-5">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Domain Name :</label>
              <span className="text-sm md:text-base">{selectedDomain.domain_name}</span>
            </div>
            <div className="flex gap-4 md:gap-8 justify-center">
              {hasPermission(currentUserRole, "canDeleteTables") && (
                <button
                  className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                  onClick={handleDeleteClick}
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
                  }}
                >
                  Update
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md">
            <button 
              type="button" 
              className="absolute top-3 right-4 w-6 h-6 flex items-center justify-center rounded-full bg-gray-200 hover:bg-gray-300 transition-colors" 
              onClick={() => setShowDeleteConfirm(false)}
            >
              <X className="w-4 h-4" />
            </button>
            <div className="mt-4 md:mt-6">
              <p className="text-base md:text-lg font-semibold mb-4 text-center">
                Are you sure you want to delete the following domain? This action cannot be undone.
              </p>
              <div className="mb-6">
                <p className="text-sm md:text-base">
                  <span className="font-semibold">Domain Name :</span> {selectedDomain.domain_name}
                </p>
              </div>
              <div className="flex gap-4 justify-center">
                <button
                  className="px-6 md:px-8 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded text-sm md:text-base transition-colors"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                  onClick={handleDelete}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Update Modal */}
      {showUpdateModal && selectedDomain && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[220px]">
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowUpdateModal(false);
                setSelectedDomain(null);
              }}
            >
              ×
            </button>
            <div className="flex flex-col md:flex-row items-center mb-6 md:mb-8 mt-4 md:mt-5 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Domain Name :</label>
              <input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div>
            <div className="flex flex-col md:flex-row justify-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[80px]"> Notes :</label>
              <input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                className={`mt-2 md:mt-0 md:ml-4 px-6 py-2 rounded text-sm md:text-lg font-semibold shadow transition ${
                  updateName.trim() && addMessage.trim() 
                    ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" 
                    : "bg-green-300 text-white cursor-not-allowed"
                }`}
                disabled={!updateName.trim() || !addMessage.trim()}
                onClick={handleUpdate}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Domain Dialog */}
      {addOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[220px] flex flex-col justify-between">
            <button
              type="button"
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors focus:outline-none"
              onClick={() => setAddOpen(false)}
              aria-label="Close"
            >
              ×
            </button>
            {/* Domain Name Row */}
            {/* <div className="flex flex-col items-center justify-center flex-1"> */}
            <div className="flex flex-col md:flex-row items-center mb-6 mb:mb-8 mt-4 md:mt-5 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Domain Name</label>
              <input
                value={newDomainName}
                onChange={e => setNewDomainName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                maxLength={150}
              />
            </div>
            {/* </div> */}
            {/* Message Row + Submit Button */}
            <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[80px]"> Notes :</label>
              <input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
              <button
                type="button"
                className={`mt-2 md:mt-0 md:ml-4 px-6 py-2 rounded text-sm md:text-lg font-semibold shadow transition ${
                  newDomainName.trim() && addMessage.trim() 
                    ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" 
                    : "bg-green-300 text-white cursor-not-allowed"
                }`}
                onClick={handleAdd}
                disabled={!newDomainName.trim() || !addMessage.trim()}
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

export default DomainList;
