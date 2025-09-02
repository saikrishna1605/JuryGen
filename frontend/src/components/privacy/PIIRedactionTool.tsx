import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Chip, 
  Switch, 
  FormControlLabel,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  Security, 
  Warning, 
  CheckCircle,
  Info
} from '@mui/icons-material';

interface PIIFinding {
  start: number;
  end: number;
  type: string;
  text: string;
  likelihood: string;
  confidence: number;
  suggested_masking: string;
}

interface PIIPreview {
  original_content: string;
  pii_locations: PIIFinding[];
  summary: {
    total_findings: number;
    by_type: Record<string, number>;
    risk_level: 'low' | 'medium' | 'high';
  };
}

interface MaskingConfig {
  [piiType: string]: 'redact' | 'mask' | 'hash' | 'replace' | 'partial';
}

interface PIIRedactionToolProps {
  content: string;
  onRedactionComplete: (maskedContent: string, findings: PIIFinding[]) => void;
  onCancel: () => void;
  isOpen: boolean;
}

const PIIRedactionTool: React.FC<PIIRedactionToolProps> = ({
  content,
  onRedactionComplete,
  onCancel,
  isOpen
}) => {
  const [preview, setPreview] = useState<PIIPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [maskingConfig, setMaskingConfig] = useState<MaskingConfig>({});
  const [showPreview, setShowPreview] = useState(false);
  const [maskedContent, setMaskedContent] = useState('');
  const [selectedFindings, setSelectedFindings] = useState<Set<number>>(new Set());

  // Load PII preview when dialog opens
  useEffect(() => {
    if (isOpen && content) {
      detectPII();
    }
  }, [isOpen, content]);

  const detectPII = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/pii/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          content,
          create_preview: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to detect PII');
      }

      const previewData: PIIPreview = await response.json();
      setPreview(previewData);
      
      // Initialize masking config with suggestions
      const config: MaskingConfig = {};
      previewData.pii_locations.forEach(finding => {
        config[finding.type] = finding.suggested_masking as any;
      });
      setMaskingConfig(config);

      // Select all findings by default
      setSelectedFindings(new Set(previewData.pii_locations.map((_, index) => index)));

    } catch (error) {
      console.error('Error detecting PII:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyMasking = async () => {
    if (!preview) return;

    setLoading(true);
    try {
      // Filter selected findings
      const selectedPIIFindings = preview.pii_locations.filter((_, index) => 
        selectedFindings.has(index)
      );

      const response = await fetch('/api/v1/pii/mask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          content,
          findings: selectedPIIFindings,
          masking_config: maskingConfig
        })
      });

      if (!response.ok) {
        throw new Error('Failed to apply masking');
      }

      const result = await response.json();
      setMaskedContent(result.masked_content);
      onRedactionComplete(result.masked_content, result.findings);

    } catch (error) {
      console.error('Error applying masking:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFinding = (index: number) => {
    const newSelected = new Set(selectedFindings);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedFindings(newSelected);
  };

  const updateMaskingType = (piiType: string, maskingType: string) => {
    setMaskingConfig(prev => ({
      ...prev,
      [piiType]: maskingType as any
    }));
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getPIITypeIcon = (piiType: string) => {
    const highRiskTypes = ['US_SOCIAL_SECURITY_NUMBER', 'CREDIT_CARD_NUMBER', 'PASSPORT'];
    return highRiskTypes.includes(piiType) ? <Warning color="error" /> : <Info color="info" />;
  };

  const renderHighlightedContent = () => {
    if (!preview) return null;

    let highlightedContent = preview.original_content;
    const highlights: Array<{ start: number; end: number; type: string; index: number }> = [];

    preview.pii_locations.forEach((finding, index) => {
      highlights.push({
        start: finding.start,
        end: finding.end,
        type: finding.type,
        index
      });
    });

    // Sort by start position (descending) to avoid offset issues
    highlights.sort((a, b) => b.start - a.start);

    highlights.forEach(highlight => {
      const isSelected = selectedFindings.has(highlight.index);
      const className = isSelected ? 'pii-highlight selected' : 'pii-highlight';
      
      highlightedContent = 
        highlightedContent.slice(0, highlight.start) +
        `<span class="${className}" data-pii-type="${highlight.type}" data-index="${highlight.index}">` +
        highlightedContent.slice(highlight.start, highlight.end) +
        '</span>' +
        highlightedContent.slice(highlight.end);
    });

    return (
      <Box
        sx={{
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          p: 2,
          maxHeight: 400,
          overflow: 'auto',
          backgroundColor: 'background.paper',
          '& .pii-highlight': {
            backgroundColor: 'warning.light',
            padding: '2px 4px',
            borderRadius: '4px',
            cursor: 'pointer',
            border: '1px solid transparent'
          },
          '& .pii-highlight.selected': {
            backgroundColor: 'error.light',
            border: '1px solid',
            borderColor: 'error.main'
          }
        }}
        dangerouslySetInnerHTML={{ __html: highlightedContent }}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.classList.contains('pii-highlight')) {
            const index = parseInt(target.dataset.index || '0');
            toggleFinding(index);
          }
        }}
      />
    );
  };

  if (!isOpen) return null;

  return (
    <Dialog
      open={isOpen}
      onClose={onCancel}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Security />
          <Typography variant="h6">PII Detection & Redaction</Typography>
          {preview && (
            <Chip
              label={`${preview.summary.total_findings} PII items found`}
              color={getRiskColor(preview.summary.risk_level) as any}
              size="small"
            />
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {preview && (
          <>
            {/* Risk Summary */}
            <Alert 
              severity={preview.summary.risk_level === 'high' ? 'error' : 
                       preview.summary.risk_level === 'medium' ? 'warning' : 'info'}
              sx={{ mb: 2 }}
            >
              <Typography variant="subtitle2">
                Risk Level: {preview.summary.risk_level.toUpperCase()}
              </Typography>
              <Typography variant="body2">
                Found {preview.summary.total_findings} PII items across {Object.keys(preview.summary.by_type).length} categories.
                Review and configure masking options below.
              </Typography>
            </Alert>

            {/* PII Types Summary */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  PII Categories Detected
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {Object.entries(preview.summary.by_type).map(([type, count]) => (
                    <Chip
                      key={type}
                      icon={getPIITypeIcon(type)}
                      label={`${type.replace(/_/g, ' ')}: ${count}`}
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>

            {/* Masking Configuration */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Masking Configuration
                </Typography>
                <List dense>
                  {Object.keys(preview.summary.by_type).map(piiType => (
                    <ListItem key={piiType}>
                      <ListItemText
                        primary={piiType.replace(/_/g, ' ')}
                        secondary={`${preview.summary.by_type[piiType]} occurrences`}
                      />
                      <ListItemSecondaryAction>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <InputLabel>Masking</InputLabel>
                          <Select
                            value={maskingConfig[piiType] || 'mask'}
                            onChange={(e) => updateMaskingType(piiType, e.target.value)}
                            label="Masking"
                          >
                            <MenuItem value="redact">Redact (Remove)</MenuItem>
                            <MenuItem value="mask">Mask (***)</MenuItem>
                            <MenuItem value="hash">Hash</MenuItem>
                            <MenuItem value="replace">Replace with Label</MenuItem>
                            <MenuItem value="partial">Partial (Show First/Last)</MenuItem>
                          </Select>
                        </FormControl>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Content Preview */}
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="subtitle1">
                    Content Preview
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showPreview}
                        onChange={(e) => setShowPreview(e.target.checked)}
                        icon={<VisibilityOff />}
                        checkedIcon={<Visibility />}
                      />
                    }
                    label="Show Content"
                  />
                </Box>

                {showPreview && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Click on highlighted PII items to toggle masking. Selected items will be masked.
                    </Typography>
                    {renderHighlightedContent()}
                    
                    <Box mt={2}>
                      <Typography variant="caption" color="text.secondary">
                        Selected: {selectedFindings.size} of {preview.pii_locations.length} PII items
                      </Typography>
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={applyMasking}
          variant="contained"
          disabled={loading || !preview || selectedFindings.size === 0}
          startIcon={<CheckCircle />}
        >
          Apply Masking ({selectedFindings.size} items)
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PIIRedactionTool;