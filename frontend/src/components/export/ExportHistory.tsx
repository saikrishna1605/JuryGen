import React, { useState, useEffect } from 'react';
import {
  Download,
  FileText,
  File,
  FileSpreadsheet,
  Trash2,
  RefreshCw,
  Calendar,
  Filter,
  Search,
} from 'lucide-react';
import { exportService, ExportResponse } from '../../services/exportService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { AccessibleTable } from '../accessibility/ScreenReaderUtils';
import { cn } from '../../utils';

interface ExportHistoryProps {
  className?: string;
  limit?: number;
}

interface FilterOptions {
  format: string;
  status: string;
  dateRange: string;
}

export const ExportHistory: React.FC<ExportHistoryProps> = ({
  className,
  limit = 50,
}) => {
  const [exports, setExports] = useState<ExportResponse[]>([]);
  const [filteredExports, setFilteredExports] = useState<ExportResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    format: 'all',
    status: 'all',
    dateRange: 'all',
  });
  const [sortBy, setSortBy] = useState<'date' | 'filename' | 'format' | 'status'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { announceSuccess, announceError } = useAriaAnnouncements();

  // Load export history
  useEffect(() => {
    loadExportHistory();
  }, [limit]);

  // Apply filters and search
  useEffect(() => {
    let filtered = [...exports];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(exp =>
        exp.filename.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply format filter
    if (filters.format !== 'all') {
      filtered = filtered.filter(exp => {
        const format = exp.filename.split('.').pop()?.toLowerCase();
        return format === filters.format;
      });
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(exp => exp.status === filters.status);
    }

    // Apply date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date();
      const filterDate = new Date();
      
      switch (filters.dateRange) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          filterDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          filterDate.setMonth(now.getMonth() - 1);
          break;
      }

      filtered = filtered.filter(exp => new Date(exp.expiresAt) >= filterDate);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'filename':
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
          break;
        case 'format':
          aValue = a.filename.split('.').pop()?.toLowerCase() || '';
          bValue = b.filename.split('.').pop()?.toLowerCase() || '';
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'date':
        default:
          aValue = new Date(a.expiresAt).getTime();
          bValue = new Date(b.expiresAt).getTime();
          break;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    setFilteredExports(filtered);
  }, [exports, searchTerm, filters, sortBy, sortOrder]);

  const loadExportHistory = async () => {
    setLoading(true);
    try {
      const history = await exportService.getExportHistory(limit);
      setExports(history);
    } catch (error) {
      announceError('Failed to load export history');
      console.error('Error loading export history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (exportItem: ExportResponse) => {
    try {
      const blob = await exportService.downloadExport(exportItem.exportId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exportItem.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      announceSuccess(`Downloaded ${exportItem.filename}`);
    } catch (error) {
      announceError(`Failed to download ${exportItem.filename}`);
      console.error('Download error:', error);
    }
  };

  const handleDelete = async (exportId: string, filename: string) => {
    try {
      await exportService.cancelExport(exportId);
      setExports(prev => prev.filter(exp => exp.exportId !== exportId));
      announceSuccess(`Deleted ${filename}`);
    } catch (error) {
      announceError(`Failed to delete ${filename}`);
      console.error('Delete error:', error);
    }
  };

  const getFormatIcon = (filename: string) => {
    const format = filename.split('.').pop()?.toLowerCase();
    switch (format) {
      case 'pdf':
        return <FileText className="w-4 h-4" />;
      case 'docx':
        return <File className="w-4 h-4" />;
      case 'csv':
        return <FileSpreadsheet className="w-4 h-4" />;
      case 'json':
        return <File className="w-4 h-4" />;
      default:
        return <File className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    switch (status) {
      case 'ready':
        return <span className={`${baseClasses} bg-green-100 text-green-800`}>Ready</span>;
      case 'generating':
        return <span className={`${baseClasses} bg-blue-100 text-blue-800`}>Generating</span>;
      case 'failed':
        return <span className={`${baseClasses} bg-red-100 text-red-800`}>Failed</span>;
      default:
        return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>{status}</span>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Loading export history...</span>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Export History</h2>
        <button
          onClick={loadExportHistory}
          className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
          aria-label="Refresh export history"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search exports..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <select
            value={filters.format}
            onChange={(e) => setFilters(prev => ({ ...prev, format: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Formats</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>

          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="ready">Ready</option>
            <option value="generating">Generating</option>
            <option value="failed">Failed</option>
          </select>

          <select
            value={filters.dateRange}
            onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
      </div>

      {/* Export Table */}
      {filteredExports.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {exports.length === 0 ? 'No exports found' : 'No exports match your filters'}
        </div>
      ) : (
        <AccessibleTable
          caption="Export history table"
          summary="List of document exports with download and management options"
          rowCount={filteredExports.length}
          columnCount={6}
        >
          <thead>
            <tr className="bg-gray-50">
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('filename')}
              >
                <div className="flex items-center space-x-1">
                  <span>File</span>
                  {sortBy === 'filename' && (
                    <span className="text-blue-500">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('format')}
              >
                <div className="flex items-center space-x-1">
                  <span>Format</span>
                  {sortBy === 'format' && (
                    <span className="text-blue-500">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center space-x-1">
                  <span>Status</span>
                  {sortBy === 'status' && (
                    <span className="text-blue-500">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('date')}
              >
                <div className="flex items-center space-x-1">
                  <span>Created</span>
                  {sortBy === 'date' && (
                    <span className="text-blue-500">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredExports.map((exportItem) => (
              <tr key={exportItem.exportId} className="hover:bg-gray-50">
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-3">
                    {getFormatIcon(exportItem.filename)}
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {exportItem.filename}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900 uppercase">
                    {exportItem.filename.split('.').pop()}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatFileSize(exportItem.size)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {getStatusBadge(exportItem.status)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span>{formatDate(exportItem.expiresAt)}</span>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center space-x-2">
                    {exportItem.status === 'ready' && (
                      <button
                        onClick={() => handleDownload(exportItem)}
                        className="text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-1"
                        aria-label={`Download ${exportItem.filename}`}
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(exportItem.exportId, exportItem.filename)}
                      className="text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded-md p-1"
                      aria-label={`Delete ${exportItem.filename}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </AccessibleTable>
      )}

      {/* Results Summary */}
      <div className="text-sm text-gray-600">
        Showing {filteredExports.length} of {exports.length} exports
      </div>
    </div>
  );
};

export default ExportHistory;