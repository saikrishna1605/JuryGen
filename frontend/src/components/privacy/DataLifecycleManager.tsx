import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  Gavel as GavelIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { dataLifecycleService } from '../../services/dataLifecycleService';

interface DataSummary {
  user_id: string;
  data_residency: string;
  total_documents: number;
  storage_usage_bytes: number;
  storage_by_category: Record<string, number>;
  retention_policies: Record<string, any>;
  consents: Record<string, any>;
  generated_at: string;
}

interface RetentionPolicy {
  data_category: string;
  retention_period: string;
  custom_days?: number;
}

interface ConsentSettings {
  consent_type: string;
  granted: boolean;
}

const DataLifecycleManager: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [customDays, setCustomDays] = useState<number | ''>('');
  const [selectedResidency, setSelectedResidency] = useState<string>('');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const queryClient = useQueryClient();

  // Fetch data summary
  const { data: dataSummary, isLoading: summaryLoading } = useQuery<DataSummary>({
    queryKey: ['dataSummary'],
    queryFn: dataLifecycleService.getDataSummary
  });

  // Fetch available options
  const { data: options, isLoading: optionsLoading } = useQuery({
    queryKey: ['lifecycleOptions'],
    queryFn: dataLifecycleService.getAvailableOptions
  });

  // Fetch consent status
  const { data: consentStatus, isLoading: consentLoading } = useQuery({
    queryKey: ['consentStatus'],
    queryFn: dataLifecycleService.getConsentStatus
  });

  // Create retention policy mutation
  const createPolicyMutation = useMutation({
    mutationFn: (policy: RetentionPolicy) => 
      dataLifecycleService.createRetentionPolicy(policy),
    onSuccess: () => {
      toast.success('Retention policy updated successfully');
      queryClient.invalidateQueries({ queryKey: ['dataSummary'] });
      setSelectedCategory('');
      setSelectedPeriod('');
      setCustomDays('');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update retention policy');
    }
  });

  // Update consent mutation
  const updateConsentMutation = useMutation({
    mutationFn: (consent: ConsentSettings) => 
      dataLifecycleService.updateConsent(consent),
    onSuccess: () => {
      toast.success('Consent preferences updated');
      queryClient.invalidateQueries({ queryKey: ['consentStatus'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update consent');
    }
  });

  // Set data residency mutation
  const setResidencyMutation = useMutation({
    mutationFn: (residency: string) => 
      dataLifecycleService.setDataResidency(residency),
    onSuccess: () => {
      toast.success('Data residency preference updated');
      queryClient.invalidateQueries({ queryKey: ['dataSummary'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update data residency');
    }
  });

  // Export data mutation
  const exportDataMutation = useMutation({
    mutationFn: dataLifecycleService.exportUserData,
    onSuccess: (data) => {
      // Create and download JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `user-data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Data export downloaded successfully');
      setExportDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to export data');
    }
  });

  // Delete all data mutation
  const deleteAllDataMutation = useMutation({
    mutationFn: () => dataLifecycleService.deleteAllUserData(true),
    onSuccess: (data) => {
      toast.success(`Successfully deleted ${data.total_items_deleted} items`);
      setDeleteConfirmOpen(false);
      setConfirmText('');
      // Redirect to logout or home page
      window.location.href = '/';
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to delete data');
    }
  });

  const handleCreatePolicy = () => {
    if (!selectedCategory || !selectedPeriod) {
      toast.error('Please select both category and retention period');
      return;
    }

    const policy: RetentionPolicy = {
      data_category: selectedCategory,
      retention_period: selectedPeriod,
      ...(customDays && { custom_days: Number(customDays) })
    };

    createPolicyMutation.mutate(policy);
  };

  const handleConsentChange = (consentType: string, granted: boolean) => {
    updateConsentMutation.mutate({ consent_type: consentType, granted });
  };

  const handleResidencyChange = () => {
    if (selectedResidency) {
      setResidencyMutation.mutate(selectedResidency);
    }
  };

  const handleDeleteConfirm = () => {
    if (confirmText !== 'DELETE ALL MY DATA') {
      toast.error('Please type the confirmation text exactly');
      return;
    }
    deleteAllDataMutation.mutate();
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatRetentionPeriod = (period: string): string => {
    return period.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (summaryLoading || optionsLoading || consentLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SecurityIcon />
        Data Lifecycle Management
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage your data retention policies, consent preferences, and privacy settings.
      </Typography>

      {/* Data Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StorageIcon />
            Data Overview
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Total Documents: <strong>{dataSummary?.total_documents || 0}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Storage Used: <strong>{formatBytes(dataSummary?.storage_usage_bytes || 0)}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Data Residency: <strong>{dataSummary?.data_residency?.toUpperCase() || 'GLOBAL'}</strong>
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>Storage by Category:</Typography>
              {dataSummary?.storage_by_category && Object.entries(dataSummary.storage_by_category).map(([category, bytes]) => (
                <Box key={category} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2">{formatRetentionPeriod(category)}:</Typography>
                  <Typography variant="body2">{formatBytes(bytes as number)}</Typography>
                </Box>
              ))}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Retention Policies */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon />
            Retention Policies
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>Current Policies:</Typography>
              <List dense>
                {dataSummary?.retention_policies && Object.entries(dataSummary.retention_policies).map(([category, policy]: [string, any]) => (
                  <ListItem key={category}>
                    <ListItemText
                      primary={formatRetentionPeriod(category)}
                      secondary={`${formatRetentionPeriod(policy.retention_period)} (${policy.retention_days === -1 ? 'Permanent' : `${policy.retention_days} days`})`}
                    />
                    <ListItemSecondaryAction>
                      <Chip 
                        size="small" 
                        label={policy.expiration_date ? 'Expires' : 'Permanent'}
                        color={policy.expiration_date ? 'warning' : 'success'}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>Create/Update Policy:</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl fullWidth>
                  <InputLabel>Data Category</InputLabel>
                  <Select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    label="Data Category"
                  >
                    {options?.data_categories?.map((category: any) => (
                      <MenuItem key={category.value} value={category.value}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl fullWidth>
                  <InputLabel>Retention Period</InputLabel>
                  <Select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value)}
                    label="Retention Period"
                  >
                    {options?.retention_periods?.map((period: any) => (
                      <MenuItem key={period.value} value={period.value}>
                        {period.name} {period.days !== -1 && `(${period.days} days)`}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                {selectedPeriod === 'custom' && (
                  <TextField
                    label="Custom Days"
                    type="number"
                    value={customDays}
                    onChange={(e) => setCustomDays(e.target.value ? Number(e.target.value) : '')}
                    fullWidth
                  />
                )}
                
                <Button
                  variant="contained"
                  onClick={handleCreatePolicy}
                  disabled={createPolicyMutation.isPending}
                >
                  {createPolicyMutation.isPending ? 'Updating...' : 'Update Policy'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Consent Management */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GavelIcon />
            Consent Management
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" paragraph>
            Control how your data can be used by our services.
          </Typography>
          
          <List>
            {options?.consent_types?.map((consentType: any) => (
              <ListItem key={consentType.value}>
                <ListItemText
                  primary={consentType.name}
                  secondary={consentType.description}
                />
                <ListItemSecondaryAction>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={consentStatus?.consent_status?.[consentType.value] || false}
                        onChange={(e) => handleConsentChange(consentType.value, e.target.checked)}
                        disabled={updateConsentMutation.isPending}
                      />
                    }
                    label=""
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>

      {/* Data Residency */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Data Residency</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose where your data is stored geographically.
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Data Region</InputLabel>
              <Select
                value={selectedResidency || dataSummary?.data_residency || 'global'}
                onChange={(e) => setSelectedResidency(e.target.value)}
                label="Data Region"
              >
                {options?.data_residency_options?.map((option: any) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.name} - {option.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Button
              variant="contained"
              onClick={handleResidencyChange}
              disabled={setResidencyMutation.isPending || !selectedResidency}
            >
              {setResidencyMutation.isPending ? 'Updating...' : 'Update Region'}
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Data Export and Deletion */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Data Portability & Deletion</Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={() => setExportDialogOpen(true)}
                fullWidth
                disabled={exportDataMutation.isPending}
              >
                {exportDataMutation.isPending ? 'Exporting...' : 'Export My Data'}
              </Button>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Download all your data in JSON format (GDPR compliance)
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => setDeleteConfirmOpen(true)}
                fullWidth
                disabled={deleteAllDataMutation.isPending}
              >
                {deleteAllDataMutation.isPending ? 'Deleting...' : 'Delete All My Data'}
              </Button>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Permanently delete all your data (Right to be forgotten)
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Export Confirmation Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Your Data</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            This will download all your data in JSON format, including:
          </Typography>
          <ul>
            <li>User profile information</li>
            <li>Uploaded documents and analysis results</li>
            <li>Processing jobs and history</li>
            <li>Consent records and preferences</li>
            <li>Audit logs and activity history</li>
          </ul>
          <Alert severity="info" sx={{ mt: 2 }}>
            The export may take a few moments to generate for large datasets.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => exportDataMutation.mutate()} 
            variant="contained"
            disabled={exportDataMutation.isPending}
          >
            {exportDataMutation.isPending ? 'Exporting...' : 'Download Export'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Delete All Your Data</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <strong>Warning:</strong> This action cannot be undone!
          </Alert>
          
          <Typography paragraph>
            This will permanently delete all your data, including:
          </Typography>
          <ul>
            <li>All uploaded documents and files</li>
            <li>Analysis results and summaries</li>
            <li>Processing history and jobs</li>
            <li>User preferences and settings</li>
            <li>Export history and shared links</li>
          </ul>
          
          <Typography paragraph sx={{ mt: 2 }}>
            To confirm, please type: <strong>DELETE ALL MY DATA</strong>
          </Typography>
          
          <TextField
            fullWidth
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="Type confirmation text here"
            error={confirmText !== '' && confirmText !== 'DELETE ALL MY DATA'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setDeleteConfirmOpen(false);
            setConfirmText('');
          }}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteAllDataMutation.isPending || confirmText !== 'DELETE ALL MY DATA'}
          >
            {deleteAllDataMutation.isPending ? 'Deleting...' : 'Delete All Data'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataLifecycleManager;
  