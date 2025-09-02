import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Pagination
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { auditService } from '../../services/auditService';

interface AuditLog {
  event_id: string;
  event_type: string;
  timestamp: string;
  user_id?: string;
  session_id?: string;
  ip_address?: string;
  user_agent?: string;
  resource_type?: string;
  resource_id?: string;
  action: string;
  details: Record<string, any>;
  result: string;
  compliance_frameworks: string[];
}

interface AuditFilters {
  startTime?: Date;
  endTime?: Date;
  userId?: string;
  eventType?: string;
  resourceType?: string;
  resourceId?: string;
  result?: string;
}

const AuditLogViewer: React.FC = () => {
  const [filters, setFilters] = useState<AuditFilters>({});
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const queryClient = useQueryClient();

  // Fetch audit logs
  const { data: auditData, isLoading, error } = useQuery({
    queryKey: ['auditLogs', filters, page, pageSize],
    queryFn: () => auditService.queryAuditLogs({
      ...filters,
      limit: pageSize,
      offset: (page - 1) * pageSize
    })
  });

  // Fetch available event types
  const { data: eventTypes } = useQuery({
    queryKey: ['auditEventTypes'],
    queryFn: auditService.getAvailableEventTypes
  });

  // Export audit logs mutation
  const exportMutation = useMutation({
    mutationFn: () => auditService.exportAuditLogs(filters),
    onSuccess: (data) => {
      // Create and download CSV file
      const blob = new Blob([data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Audit logs exported successfully');
    },
    onError: () => {
      toast.error('Failed to export audit logs');
    }
  });

  const handleFilterChange = (field: keyof AuditFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const getEventTypeColor = (eventType: string) => {
    const colorMap: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success'> = {
      'user_login': 'info',
      'user_logout': 'info',
      'document_upload': 'primary',
      'document_download': 'primary',
      'document_delete': 'error',
      'data_access': 'secondary',
      'data_modify': 'warning',
      'data_delete': 'error',
      'admin_action': 'warning',
      'security_event': 'error',
      'error_occurred': 'error'
    };
    return colorMap[eventType] || 'default';
  };

  const getResultColor = (result: string) => {
    switch (result) {
      case 'success': return 'success';
      case 'failure': return 'error';
      case 'partial': return 'warning';
      default: return 'default';
    }
  };

  const formatEventType = (eventType: string) => {
    return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const handleViewDetails = (log: AuditLog) => {
    setSelectedLog(log);
    setDetailsOpen(true);
  };

  if (error) {
    return (
      <Alert severity="error">
        Failed to load audit logs: {error.message}
      </Alert>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AssessmentIcon />
        Audit Log Viewer
      </Typography>

      {/* Filters */}
      <Accordion expanded={filtersOpen} onChange={() => setFiltersOpen(!filtersOpen)}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon />
            Filters
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <DateTimePicker
                label="Start Time"
                value={filters.startTime || null}
                onChange={(value) => handleFilterChange('startTime', value)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <DateTimePicker
                label="End Time"
                value={filters.endTime || null}
                onChange={(value) => handleFilterChange('endTime', value)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="User ID"
                value={filters.userId || ''}
                onChange={(e) => handleFilterChange('userId', e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={filters.eventType || ''}
                  onChange={(e) => handleFilterChange('eventType', e.target.value)}
                  label="Event Type"
                >
                  <MenuItem value="">All</MenuItem>
                  {eventTypes?.event_types?.map((type: any) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Result</InputLabel>
                <Select
                  value={filters.result || ''}
                  onChange={(e) => handleFilterChange('result', e.target.value)}
                  label="Result"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="failure">Failure</MenuItem>
                  <MenuItem value="partial">Partial</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="outlined" onClick={clearFilters}>
                  Clear Filters
                </Button>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => exportMutation.mutate()}
                  disabled={exportMutation.isPending}
                >
                  {exportMutation.isPending ? 'Exporting...' : 'Export CSV'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Audit Logs Table */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Audit Logs ({auditData?.count || 0} results)
            </Typography>
            <Tooltip title="Refresh">
              <IconButton onClick={() => queryClient.invalidateQueries({ queryKey: ['auditLogs'] })}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {isLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Event Type</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Resource</TableCell>
                      <TableCell>Result</TableCell>
                      <TableCell>Compliance</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {auditData?.audit_logs?.map((log: AuditLog) => (
                      <TableRow key={log.event_id} hover>
                        <TableCell>
                          <Typography variant="body2">
                            {formatTimestamp(log.timestamp)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={formatEventType(log.event_type)}
                            color={getEventTypeColor(log.event_type)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {log.user_id || 'Anonymous'}
                          </Typography>
                          {log.ip_address && (
                            <Typography variant="caption" color="text.secondary">
                              {log.ip_address}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {log.action}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {log.resource_type && (
                            <Typography variant="body2">
                              {log.resource_type}
                              {log.resource_id && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {log.resource_id}
                                </Typography>
                              )}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={log.result}
                            color={getResultColor(log.result)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {log.compliance_frameworks?.map((framework) => (
                              <Chip
                                key={framework}
                                label={framework.toUpperCase()}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewDetails(log)}
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              {auditData?.count > pageSize && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={Math.ceil(auditData.count / pageSize)}
                    page={page}
                    onChange={(_, newPage) => setPage(newPage)}
                    color="primary"
                  />
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Audit Log Details
        </DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Event ID</Typography>
                  <Typography variant="body2" gutterBottom>{selectedLog.event_id}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Timestamp</Typography>
                  <Typography variant="body2" gutterBottom>{formatTimestamp(selectedLog.timestamp)}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Event Type</Typography>
                  <Typography variant="body2" gutterBottom>{formatEventType(selectedLog.event_type)}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Result</Typography>
                  <Chip label={selectedLog.result} color={getResultColor(selectedLog.result)} size="small" />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">User ID</Typography>
                  <Typography variant="body2" gutterBottom>{selectedLog.user_id || 'Anonymous'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Session ID</Typography>
                  <Typography variant="body2" gutterBottom>{selectedLog.session_id || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">IP Address</Typography>
                  <Typography variant="body2" gutterBottom>{selectedLog.ip_address || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Action</Typography>
                  <Typography variant="body2" gutterBottom>{selectedLog.action}</Typography>
                </Grid>
                {selectedLog.resource_type && (
                  <>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2">Resource Type</Typography>
                      <Typography variant="body2" gutterBottom>{selectedLog.resource_type}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2">Resource ID</Typography>
                      <Typography variant="body2" gutterBottom>{selectedLog.resource_id || 'N/A'}</Typography>
                    </Grid>
                  </>
                )}
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Compliance Frameworks</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                    {selectedLog.compliance_frameworks?.map((framework) => (
                      <Chip
                        key={framework}
                        label={framework.toUpperCase()}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Grid>
                {selectedLog.user_agent && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2">User Agent</Typography>
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {selectedLog.user_agent}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Details</Typography>
                  <Paper sx={{ p: 2, mt: 1, backgroundColor: 'grey.50' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(selectedLog.details, null, 2)}
                    </pre>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AuditLogViewer;