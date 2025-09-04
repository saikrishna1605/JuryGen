import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid2 as Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Tooltip,
  IconButton
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  Security,
  Warning,
  CheckCircle,
  Info,
  Download,
  Refresh,
  FilterList
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker as MUIDatePicker } from '@mui/x-date-pickers/DatePicker';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

import { piiService, ComplianceReport } from '../../services/piiService';

interface ComplianceDashboardProps {
  userId?: string;
}

const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({ userId }) => {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({
    start: startOfDay(subDays(new Date(), 30)),
    end: endOfDay(new Date())
  });
  const [filterUserId, setFilterUserId] = useState(userId || '');

  useEffect(() => {
    loadComplianceReport();
  }, [dateRange, filterUserId]);

  const loadComplianceReport = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const reportData = await piiService.getComplianceReport({
        user_id: filterUserId || undefined,
        start_date: dateRange.start.toISOString(),
        end_date: dateRange.end.toISOString()
      });
      
      setReport(reportData);
    } catch (err) {
      setError('Failed to load compliance report');
      console.error('Error loading compliance report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDateRangeChange = (field: 'start' | 'end', date: Date | null) => {
    if (date) {
      setDateRange(prev => ({
        ...prev,
        [field]: field === 'start' ? startOfDay(date) : endOfDay(date)
      }));
    }
  };

  const exportReport = async () => {
    if (!report) return;
    
    const csvContent = generateCSVReport(report);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pii-compliance-report-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const generateCSVReport = (reportData: ComplianceReport): string => {
    const headers = [
      'Metric',
      'Value',
      'Period Start',
      'Period End'
    ];
    
    const rows = [
      ['Total Operations', reportData.summary.total_operations.toString()],
      ['Unique Users', reportData.summary.unique_users.toString()],
      ['Unique Documents', reportData.summary.unique_documents.toString()],
      ['Total PII Findings', reportData.summary.total_pii_findings.toString()],
      ...Object.entries(reportData.by_action).map(([action, count]) => 
        [`Action: ${action}`, count.toString()]
      ),
      ...Object.entries(reportData.by_pii_type).map(([type, count]) => 
        [`PII Type: ${type}`, count.toString()]
      )
    ];
    
    const csvRows = [
      headers.join(','),
      ...rows.map(row => [
        ...row,
        reportData.period.start || '',
        reportData.period.end || ''
      ].join(','))
    ];
    
    return csvRows.join('\n');
  };

  const getRiskLevelColor = (count: number) => {
    if (count === 0) return 'success';
    if (count < 5) return 'warning';
    return 'error';
  };

  const formatPIIType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading && !report) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" mt={2}>
          Loading compliance report...
        </Typography>
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box p={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center" gap={1}>
            <Security color="primary" />
            <Typography variant="h5">
              PII Compliance Dashboard
            </Typography>
          </Box>
          
          <Box display="flex" gap={1}>
            <Tooltip title="Refresh Report">
              <IconButton onClick={loadComplianceReport} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Button
              startIcon={<Download />}
              onClick={exportReport}
              disabled={!report}
              variant="outlined"
            >
              Export CSV
            </Button>
          </Box>
        </Box>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <FilterList />
              <Typography variant="h6">Filters</Typography>
            </Box>
            
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={3}>
                <MUIDatePicker
                  label="Start Date"
                  value={dateRange.start}
                  onChange={(date) => handleDateRangeChange('start', date)}
                  slotProps={{
                    textField: { size: 'small', fullWidth: true }
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={3}>
                <MUIDatePicker
                  label="End Date"
                  value={dateRange.end}
                  onChange={(date) => handleDateRangeChange('end', date)}
                  slotProps={{
                    textField: { size: 'small', fullWidth: true }
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={4}>
                <FormControl size="small" fullWidth>
                  <InputLabel>User Filter</InputLabel>
                  <Select
                    value={filterUserId}
                    onChange={(e) => setFilterUserId(e.target.value)}
                    label="User Filter"
                  >
                    <MenuItem value="">All Users</MenuItem>
                    {/* Add user options dynamically */}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={2}>
                <Button
                  variant="contained"
                  onClick={loadComplianceReport}
                  disabled={loading}
                  fullWidth
                >
                  Apply
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {report && (
          <>
            {/* Summary Cards */}
            <Grid container spacing={3} mb={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Info color="primary" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Total Operations
                      </Typography>
                    </Box>
                    <Typography variant="h4">
                      {report.summary.total_operations.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Security color="primary" />
                      <Typography variant="subtitle2" color="text.secondary">
                        PII Findings
                      </Typography>
                    </Box>
                    <Typography variant="h4">
                      {report.summary.total_pii_findings.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <CheckCircle color="success" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Unique Users
                      </Typography>
                    </Box>
                    <Typography variant="h4">
                      {report.summary.unique_users}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Warning color={getRiskLevelColor(report.high_risk_activities.length) as any} />
                      <Typography variant="subtitle2" color="text.secondary">
                        High Risk Activities
                      </Typography>
                    </Box>
                    <Typography variant="h4">
                      {report.high_risk_activities.length}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Actions Breakdown */}
            <Grid container spacing={3} mb={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Operations by Action
                    </Typography>
                    <Box>
                      {Object.entries(report.by_action).map(([action, count]) => (
                        <Box key={action} display="flex" justifyContent="space-between" alignItems="center" py={1}>
                          <Typography variant="body2">
                            {action.replace(/_/g, ' ').toUpperCase()}
                          </Typography>
                          <Chip 
                            label={count} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                          />
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      PII Types Detected
                    </Typography>
                    <Box>
                      {Object.entries(report.by_pii_type)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 10)
                        .map(([type, count]) => (
                        <Box key={type} display="flex" justifyContent="space-between" alignItems="center" py={1}>
                          <Typography variant="body2">
                            {formatPIIType(type)}
                          </Typography>
                          <Chip 
                            label={count} 
                            size="small" 
                            color="secondary" 
                            variant="outlined"
                          />
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* High Risk Activities */}
            {report.high_risk_activities.length > 0 && (
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Warning color="error" />
                    <Typography variant="h6">
                      High Risk Activities
                    </Typography>
                  </Box>
                  
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Timestamp</TableCell>
                          <TableCell>User ID</TableCell>
                          <TableCell>Document ID</TableCell>
                          <TableCell>Action</TableCell>
                          <TableCell align="right">High Confidence Findings</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {report.high_risk_activities.map((activity, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              {format(new Date(activity.timestamp), 'MMM dd, yyyy HH:mm')}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontFamily="monospace">
                                {activity.user_id.slice(0, 8)}...
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontFamily="monospace">
                                {activity.document_id.slice(0, 8)}...
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={activity.action.replace(/_/g, ' ')} 
                                size="small"
                                color="warning"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={activity.high_confidence_findings} 
                                size="small"
                                color="error"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </Box>
    </LocalizationProvider>
  );
};

export default ComplianceDashboard;