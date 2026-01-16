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

// Types
interface Metric {
  metric_id: number;
  metric_name: string;
  metric_description: string | null;
  metric_source: string | null;
  domain_name: string;
  metric_benchmark: string | null;
}

const Metrics: React.FC = () => {
  const { toast } = useToast();
  const [currentUserRole, setCurrentUserRole] = useState<string>("");
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  
  const filteredMetrics = metrics.filter((metric) => 
    metric.metric_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalItems = filteredMetrics.length;
  const itemsPerPage = 15;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  
  const PaginatedMetrics = filteredMetrics.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  // ADD - Dialog local state
  const [newMetricName, setNewMetricName] = useState("");
  const [newMetricDescription, setNewMetricDescription] = useState("");
  const [newMetricSource, setNewMetricSource] = useState("");
  const [newDomainName, setNewDomainName] = useState("");
  const [newMetricBenchmark, setNewMetricBenchmark] = useState("");
  const [addMessage, setAddMessage] = useState("");

  // UPDATE - Dialog local state
  const [updateName, setUpdateName] = useState("");
  const [updateDescription, setUpdateDescription] = useState("");
  const [updateSource, setUpdateSource] = useState("");
  const [updateDomainName, setUpdateDomainName] = useState("");
  const [updateBenchmark, setUpdateBenchmark] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  const [refreshKey, setRefreshKey] = useState(0);
  const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [isFetchingDomains, setIsFetchingDomains] = useState(false);

  // Fetch domains from API
  const fetchDomains = async () => {
    setIsFetchingDomains(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.DOMAINS_V2, { headers });

      if (response.ok) {
        const domainsData = await response.json();
        const domainNames = Array.isArray(domainsData)
          ? domainsData.map((d: any) => d.domain_name).filter(Boolean)
          : [];
        setDomainOptions(domainNames);
        if (domainNames.length > 0 && !newDomainName) {
          setNewDomainName(domainNames[0]);
        }
      }
    } catch (error) {
      console.error("Error fetching domains:", error);
    } finally {
      setIsFetchingDomains(false);
    }
  };

  // Fetch metrics from API
  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.METRICS_V2, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error("Error fetching metrics:", error);
      toast({
        title: "Error",
        description: "Failed to fetch metrics. Please try again.",
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
    fetchMetrics();
    fetchDomains();
  }, [refreshKey]);

  useEffect(() => {
    if (selectedMetric) {
      setUpdateName(selectedMetric.metric_name);
      setUpdateDescription(selectedMetric.metric_description || "");
      setUpdateSource(selectedMetric.metric_source || "");
      setUpdateDomainName(selectedMetric.domain_name);
      setUpdateBenchmark(selectedMetric.metric_benchmark || "");
    }
  }, [selectedMetric]);

  // ADD handler
  const handleAdd = async () => {
    if (!newMetricName.trim() || !addMessage.trim() || !newDomainName.trim()) {
      toast({
        title: "Validation Error",
        description: "Metric name, domain, and notes are required",
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

      const response = await fetch(API_ENDPOINTS.METRIC_CREATE_V2, {
        method: "POST",
        headers,
        body: JSON.stringify({
          metric_name: newMetricName.trim(),
          metric_description: newMetricDescription.trim() || null,
          metric_source: newMetricSource.trim() || null,
          domain_name: newDomainName.trim(),
          metric_benchmark: newMetricBenchmark.trim() || null,
          notes: addMessage.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast({
        title: "Success",
        description: "Metric created successfully",
        variant: "default",
      });
      
      setNewMetricName("");
      setNewMetricDescription("");
      setNewMetricSource("");
      setNewDomainName("");
      setNewMetricBenchmark("");
      setAddMessage("");
      setAddOpen(false);
      fetchMetrics(); // Refresh the list
      setHighlightedRowId(data.metric_id);
    } catch (error: any) {
      console.error("Error creating metric:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to create metric. Please try again.",
        variant: "destructive",
      });
    }
  };

  // UPDATE handler
  const handleUpdate = async () => {
    if (!selectedMetric || !updateName.trim() || !updateMessage.trim() || !updateDomainName.trim()) {
      toast({
        title: "Validation Error",
        description: "Metric name, domain, and notes are required",
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

      const response = await fetch(API_ENDPOINTS.METRIC_UPDATE_V2(selectedMetric.metric_id), {
        method: "PUT",
        headers,
        body: JSON.stringify({
          metric_name: updateName.trim(),
          metric_description: updateDescription.trim() || null,
          metric_source: updateSource.trim() || null,
          domain_name: updateDomainName.trim(),
          metric_benchmark: updateBenchmark.trim() || null,
          user_note: updateMessage.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Metric updated successfully",
        variant: "default",
      });
      
      setShowUpdateModal(false);
      setSelectedMetric(null);
      fetchMetrics(); // Refresh the list
    } catch (error: any) {
      console.error("Error updating metric:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to update metric. Please try again.",
        variant: "destructive",
      });
    }
  };

  // DELETE handler
  const handleDelete = async () => {
    if (!selectedMetric) return;

    try {
      const token = localStorage.getItem("access_token");
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(API_ENDPOINTS.METRIC_DELETE_V2(selectedMetric.metric_id), {
        method: "DELETE",
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;

        if (errorMessage.includes("Metric") && errorMessage.includes("cannot be deleted")) {
          toast({
            title: "Cannot Delete Metric",
            description: errorMessage,
            variant: "destructive",
          });
        } else {
          throw new Error(errorMessage);
        }
        return;
      }

      toast({
        title: "Success",
        description: "Metric deleted successfully",
        variant: "default",
      });
      
      setShowDeleteConfirm(false);
      setShowEditDialog(false);
      setSelectedMetric(null);
      fetchMetrics(); // Refresh the list
      setHighlightedRowId(null);
      
    } catch (error: any) {
      console.error("Error deleting metric:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to delete metric. Please try again.",
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
          <h1 className="text-2xl md:text-4xl font-bold mb-4 md:mb-8 text-center">Metrics</h1>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Select defaultValue="Metric">
              {/* <SelectTrigger className="w-full sm:w-48">
                <SelectValue/>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Metric">Metric Name</SelectItem>
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
                entityType="Metric"
                title="Metrics"
                idField="testCaseId"
                idLabel="Metric ID"
                entityId={selectedMetric?.metric_id}
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
            <div className="bg-white rounded-lg shadow overflow-hidden max-h-[73vh] max-w-[800px] mx-left overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center p-8">
                  <span>Loading...</span>
                </div>
              ) : (
                <table className="w-full table-fixed">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 z-10 p-4 font-semibold text-left pl-12 w-[15%] ">ID</th>
                      <th className="sticky top-0 z-10 p-2 font-semibold text-left pl-4 w-[30%]">Metric Name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PaginatedMetrics.length === 0 ? (
                      <tr>
                        <td colSpan={2} className="p-4 text-center text-muted-foreground">
                          No metrics found
                        </td>
                      </tr>
                    ) : (
                      PaginatedMetrics.map((row) => (
                        <tr 
                          key={row.metric_id}
                          className={`border-b cursor-pointer transition-colors duration-200 ${
                            highlightedRowId === row.metric_id ? "bg-primary/10 hover:bg-primary/15 border-primary/30" : "hover:bg-muted/50"
                          }`}
                          onClick={() => {
                            setSelectedMetric(row);
                            setShowEditDialog(true);
                            setHighlightedRowId(row.metric_id);
                          }}
                        >
                          <td className="p-2 pl-12">{row.metric_id}</td>
                          <td className="p-2 truncate">{row.metric_name}</td>
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
            <div className="mt-2 md:mt-1 sticky bottom-5">
              <button 
                className="bg-primary hover:bg-primary/90 text-white py-2 px-4 rounded text-sm md:text-base transition-colors" 
                onClick={() => {
                  setAddOpen(true);
                  fetchDomains();
                }}
              >
                + Add Metric
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Edit Dialog - Shows Delete and Update buttons */}
      {showEditDialog && selectedMetric && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick = {() => {
            setShowEditDialog(false);
            setSelectedMetric(null);
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
                setSelectedMetric(null);
              }}
            >
              ×
            </button>
            <div className="flex flex-col items-left justify-center mb-6 md:mb-7 mt-4 md:mt-5 gap-4 ">
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Metric</label>
                <Input className="bg-muted text-sm md:text-base" value={selectedMetric.metric_name} readOnly />
              </div>
              <div className="flex flex-col gap-1">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Domain</label>
                <Input className="bg-muted text-sm md:text-base capitalize" value={selectedMetric.domain_name} readOnly />
              </div>
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
                  className="px-6 md:px-8 py-2 bg-primary hover:bg-primary/90 text-white rounded text-sm md:text-base transition-colors"
                  onClick={() => {
                    setShowEditDialog(false);
                    setShowUpdateModal(true);
                    setUpdateMessage("");
                    fetchDomains();
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
      {showDeleteConfirm && selectedMetric && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4"
          onClick={() => {
            setShowUpdateModal(false);
            setSelectedMetric(null);
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
                Are you sure you want to delete the following Metric? This action cannot be undone.
              </p>
              <div className="mb-6">
                <p className="text-sm md:text-base text-center capitalize font-semibold">
                  <span className="font-medium">Metric Name :</span> {selectedMetric.metric_name}
                </p>
              </div>
              <div className="flex gap-4 justify-center">
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
      {showUpdateModal && selectedMetric && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
          <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[300px]"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              type="button" 
              className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
              onClick={() => {
                setShowUpdateModal(false);
                setSelectedMetric(null);
              }}
            >
              ×
            </button>
            
            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 mt-4 md:mt-5 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Metric</label>
              <Input
                value={updateName}
                onChange={e => setUpdateName(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div>
            
            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Description</label>
              <Textarea
                value={updateDescription}
                onChange={e => setUpdateDescription(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto min-h-[80px] resize-none focus:outline-none focus:ring focus:ring-blue-200"
                placeholder="Enter metric description..."
              />
            </div>

            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Source</label>
              <Input
                value={updateSource}
                onChange={e => setUpdateSource(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                placeholder="Enter metric source..."
              />
            </div>

            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Domain</label>
              <Select
                value={updateDomainName}
                onValueChange={setUpdateDomainName}
                disabled={isFetchingDomains}
              >
                <SelectTrigger className="bg-gray-100 capitalize">
                  <SelectValue placeholder={isFetchingDomains ? "Loading..." : "Select domain"} />
                </SelectTrigger>
                <SelectContent>
                  {domainOptions.map((d) => (
                    <SelectItem key={d} value={d} className="capitalize">
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 gap-2 md:gap-0">
              <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Bench Mark</label>
              <Input
                value={updateBenchmark}
                onChange={e => setUpdateBenchmark(e.target.value)}
                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                placeholder="Enter metric benchmark..."
              />
            </div>
            
            <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[60px]">Notes </label>
              <Input
                value={updateMessage}
                onChange={e => setUpdateMessage(e.target.value)}
                className="bg-gray-100 rounded px-4 py-1 mr-4 w-96"
              />
              <button
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!updateName.trim() || !updateMessage.trim() || !updateDomainName.trim()}
                onClick={handleUpdate}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Metric Dialog */}
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
                setNewMetricDescription("");
                setNewMetricName("");
                setNewMetricSource("");
                setNewDomainName("");
                setNewMetricBenchmark("");
              }}
              aria-label="Close"
            >
              ×
            </button>
            
            <div className="flex flex-col items-center justify-center flex-1">
              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Metric</label>
                <Input
                  value={newMetricName}
                  onChange={e => setNewMetricName(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                  maxLength={150}
                />
              </div>
              
              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Description</label>
                <Textarea
                  value={newMetricDescription}
                  onChange={e => setNewMetricDescription(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto min-h-[80px] resize-none focus:outline-none focus:ring focus:ring-blue-200"
                  placeholder="Enter metric description..."
                />
              </div>

              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Source</label>
                <Input
                  value={newMetricSource}
                  onChange={e => setNewMetricSource(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                  placeholder="Enter metric source..."
                />
              </div>

              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Domain</label>
                <Select
                  value={newDomainName}
                  onValueChange={setNewDomainName}
                  disabled={isFetchingDomains}
                >
                  <SelectTrigger className="bg-gray-100 capitalize">
                    <SelectValue placeholder={isFetchingDomains ? "Loading..." : "Select domain"} />
                  </SelectTrigger>
                  <SelectContent>
                    {domainOptions.map((d) => (
                      <SelectItem key={d} value={d} className="capitalize">
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col md:flex-col items-left mb-4 md:mb-6 w-full gap-2 md:gap-0">
                <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px] mt-2">Bench Mark</label>
                <Input
                  value={newMetricBenchmark}
                  onChange={e => setNewMetricBenchmark(e.target.value)}
                  className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-[17px] flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                  placeholder="Enter metric benchmark..."
                />
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
              <label className="text-base md:text-lg min-w-[60px]">Notes</label>
              <Input
                value={addMessage}
                onChange={e => setAddMessage(e.target.value)}
                className="bg-gray-200 rounded px-4 py-1 mr-4 w-96"
              />
              <button
                type="button"
                className="bg-gradient-to-b from-lime-400 to-green-700 text-white px-6 py-1 rounded shadow font-semibold border border-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleAdd}
                disabled={!newMetricName.trim() || !newDomainName.trim() || !addMessage.trim()}
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

export default Metrics;

