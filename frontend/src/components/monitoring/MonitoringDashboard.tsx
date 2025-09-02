import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { monitoringService } from '../../services/monitoringService';

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  error?: string;
}

interface SystemMetrics {
  cpu: {
    usage_percent: number;
    count: number;
    count_logical: number;
  };
  memory: {
    total: number;
    available: number;
    percent: number;
    used: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  timestamp: string;
}

interface PerformanceSummary {
  time_range_hours: number;
  request_metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    average_response_time_ms: number;
    p95_response_time_ms: number;
    p99_response_time_ms: number;
  };
  error_metrics: {
    total_errors: number;
    error_rate: number;
    top_errors: Array<{ type: string; count: number }>;
  };
  resource_usage: {
    avg_cpu_percent: number;
    max_cpu_percent: number;
    avg_memory_percent: number;
    max_memory_percent: number;
  };
  ai_model_metrics: {
    total_calls: number;
    average_latency_ms: number;
    success_rate: number;
    cost_estimate_usd: number;
  };
  generated_at: string;
}

interface Alert {
  id: string;
  name: string;
  severity: 'CRITICAL' | 'ERROR' | 'WARNING' | 'INFO';
  status: 'ACTIVE' | 'RESOLVED';
  triggered_at: string;
  condition: string;
  current_value: string;
  threshold: string;
}

const MonitoringDashboard: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [timeRange, setTimeRange] = useState(24); // hours

  const queryClient = useQueryClient();

  // Fetch health status
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['healthStatus'],
    queryFn: monitoringService.getHealthStatus,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false
  });

  // Fetch system metrics
  const { data: systemMetrics, isLoading: metricsLoading } = useQuery<{ system_metrics: SystemMetrics }>({
    queryKey: ['systemMetrics'],
    queryFn: monitoringService.getSystemMetrics,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false
  });

  // Fetch performance summary
  const { data: performanceData, isLoading: performanceLoading } = useQuery<{ performance_summary: PerformanceSummary }>({
    queryKey: ['performanceSummary', timeRange],
    queryFn: () => monitoringService.getPerformanceSummary(timeRange),
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false
  });

  // Fetch active alerts
  const { data: alertsData, isLoading: alertsLoading } = useQuery<{ active_alerts: Alert[] }>({
    queryKey: ['activeAlerts'],
    queryFn: monitoringService.getActiveAlerts,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false
  });

  // Fetch dashboard metrics
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboardMetrics', timeRange],
    queryFn: () => monitoringService.getDashboardMetrics(timeRange),
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false
  });

  // Manual refresh mutation
  const refreshMutation = useMutation({
    mutationFn: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['healthStatus'] }),
        queryClient.invalidateQueries({ queryKey: ['systemMetrics'] }),
        queryClient.invalidateQueries({ queryKey: ['performanceSummary'] }),
        queryClient.invalidateQueries({ queryKey: ['activeAlerts'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboardMetrics'] })
      ]);
    },
    onSuccess: () => {
      toast.success('Dashboard refreshed');
    },
    onError: () => {
      toast.error('Failed to refresh dashboard');
    }
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return 'success';
      case 'degraded':
      case 'warning':
        return 'warning';
      case 'unhealthy':
      case 'critical':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return <CheckCircleIcon color="success" />;
      case 'degraded':
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'unhealthy':
      case 'critical':
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat().format(num);
  };

  if (healthLoading && metricsLoading && performanceLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon />
          System Monitoring Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small">
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              label="Time Range"
            >
              <MenuItem value={1}>1 Hour</MenuItem>
              <MenuItem value={6}>6 Hours</MenuItem>
              <MenuItem value={24}>24 Hours</MenuItem>
              <MenuItem value={168}>7 Days</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          
          <Tooltip title="Refresh Dashboard">
            <IconButton 
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Active Alerts */}
      {alertsData?.active_alerts && alertsData.active_alerts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <NotificationsIcon />
            <Typography variant="subtitle1">
              {alertsData.active_alerts.length} Active Alert{alertsData.active_alerts.length !== 1 ? 's' : ''}
            </Typography>
          </Box>
          <List dense>
            {alertsData.active_alerts.map((alert) => (
              <ListItem key={alert.id}>
                <ListItemIcon>
                  {getStatusIcon(alert.severity)}
                </ListItemIcon>
                <ListItemText
                  primary={alert.name}
                  secondary={`${alert.condition} - Current: ${alert.current_value}`}
                />
                <Chip 
                  label={alert.severity} 
                  color={getStatusColor(alert.severity) as any}
                  size="small"
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* System Health Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon />
            System Health Status
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color={getStatusColor(healthData?.status || 'unknown')}>
                  {getStatusIcon(healthData?.status || 'unknown')}
                </Typography>
                <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                  {healthData?.status || 'Unknown'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Overall Status
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={9}>
              <Grid container spacing={2}>
                {healthData?.checks && Object.entries(healthData.checks).map(([service, check]: [string, any]) => (
                  <Grid item xs={6} sm={4} md={3} key={service}>
                    <Box sx={{ textAlign: 'center', p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      {getStatusIcon(check.status)}
                      <Typography variant="body2" sx={{ textTransform: 'capitalize', mt: 0.5 }}>
                        {service.replace('_', ' ')}
                      </Typography>
                      <Chip 
                        label={check.status} 
                        color={getStatusColor(check.status) as any}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* System Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SpeedIcon />
                CPU Usage
              </Typography>
              <Typography variant="h4" color={systemMetrics?.system_metrics.cpu.usage_percent > 80 ? 'error' : 'primary'}>
                {systemMetrics?.system_metrics.cpu.usage_percent.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics?.system_metrics.cpu.usage_percent || 0}
                color={systemMetrics?.system_metrics.cpu.usage_percent > 80 ? 'error' : 'primary'}
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {systemMetrics?.system_metrics.cpu.count} cores ({systemMetrics?.system_metrics.cpu.count_logical} logical)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MemoryIcon />
                Memory Usage
              </Typography>
              <Typography variant="h4" color={systemMetrics?.system_metrics.memory.percent > 85 ? 'error' : 'primary'}>
                {systemMetrics?.system_metrics.memory.percent.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics?.system_metrics.memory.percent || 0}
                color={systemMetrics?.system_metrics.memory.percent > 85 ? 'error' : 'primary'}
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {formatBytes(systemMetrics?.system_metrics.memory.used || 0)} / {formatBytes(systemMetrics?.system_metrics.memory.total || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StorageIcon />
                Disk Usage
              </Typography>
              <Typography variant="h4" color={systemMetrics?.system_metrics.disk.percent > 90 ? 'error' : 'primary'}>
                {systemMetrics?.system_metrics.disk.percent.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics?.system_metrics.disk.percent || 0}
                color={systemMetrics?.system_metrics.disk.percent > 90 ? 'error' : 'primary'}
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {formatBytes(systemMetrics?.system_metrics.disk.used || 0)} / {formatBytes(systemMetrics?.system_metrics.disk.total || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <NetworkIcon />
                Network I/O
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="success.main">
                    <TrendingUpIcon fontSize="small" /> Sent
                  </Typography>
                  <Typography variant="body2">
                    {formatBytes(systemMetrics?.system_metrics.network.bytes_sent || 0)}
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="info.main">
                    <TrendingDownIcon fontSize="small" /> Received
                  </Typography>
                  <Typography variant="body2">
                    {formatBytes(systemMetrics?.system_metrics.network.bytes_recv || 0)}
                  </Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Packets: {formatNumber(systemMetrics?.system_metrics.network.packets_sent || 0)} sent, {formatNumber(systemMetrics?.system_metrics.network.packets_recv || 0)} received
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Summary */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Performance Summary ({timeRange}h)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>Request Metrics</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Total Requests</Typography>
                      <Typography variant="h6">{formatNumber(performanceData?.performance_summary.request_metrics.total_requests || 0)}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                      <Typography variant="h6" color={performanceData?.performance_summary.request_metrics.success_rate > 95 ? 'success.main' : 'error.main'}>
                        {performanceData?.performance_summary.request_metrics.success_rate.toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Avg Response Time</Typography>
                      <Typography variant="h6">{performanceData?.performance_summary.request_metrics.average_response_time_ms.toFixed(0)}ms</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">P95 Response Time</Typography>
                      <Typography variant="h6">{performanceData?.performance_summary.request_metrics.p95_response_time_ms.toFixed(0)}ms</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>AI Model Metrics</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Total Calls</Typography>
                      <Typography variant="h6">{formatNumber(performanceData?.performance_summary.ai_model_metrics.total_calls || 0)}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                      <Typography variant="h6" color="success.main">
                        {performanceData?.performance_summary.ai_model_metrics.success_rate.toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Avg Latency</Typography>
                      <Typography variant="h6">{performanceData?.performance_summary.ai_model_metrics.average_latency_ms.toFixed(0)}ms</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Cost Estimate</Typography>
                      <Typography variant="h6">${performanceData?.performance_summary.ai_model_metrics.cost_estimate_usd.toFixed(2)}</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          {/* Error Summary */}
          {performanceData?.performance_summary.error_metrics.top_errors && performanceData.performance_summary.error_metrics.top_errors.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Top Errors</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Error Type</TableCell>
                        <TableCell align="right">Count</TableCell>
                        <TableCell align="right">Percentage</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {performanceData.performance_summary.error_metrics.top_errors.map((error, index) => (
                        <TableRow key={index}>
                          <TableCell>{error.type}</TableCell>
                          <TableCell align="right">{error.count}</TableCell>
                          <TableCell align="right">
                            {((error.count / performanceData.performance_summary.error_metrics.total_errors) * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Last Updated */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Last updated: {new Date().toLocaleString()}
          {autoRefresh && ` • Auto-refresh every ${refreshInterval}s`}
        </Typography>
      </Box>
    </Box>
  );
};

export default MonitoringDashboard;