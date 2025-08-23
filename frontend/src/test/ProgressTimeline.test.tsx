import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressTimeline } from '../components/progress/ProgressTimeline';
import { ProcessingStage, ProcessingStatus } from '../types/job';

describe('ProgressTimeline', () => {
  it('renders progress timeline with stages', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={45}
      />
    );

    // Check if main elements are present
    expect(screen.getByText('Document Processing')).toBeInTheDocument();
    expect(screen.getByText('Processing your document...')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('shows completed status correctly', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.EXPORT_GENERATION}
        status={ProcessingStatus.COMPLETED}
        progress={100}
      />
    );

    expect(screen.getAllByText('Processing completed successfully!')).toHaveLength(2);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('shows failed status with error message', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.OCR}
        status={ProcessingStatus.FAILED}
        progress={25}
        error="OCR processing failed"
      />
    );

    expect(screen.getByText('OCR processing failed')).toBeInTheDocument();
  });

  it('displays estimated time remaining', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={45}
        estimatedTimeRemaining={120}
      />
    );

    expect(screen.getByText('~2m remaining')).toBeInTheDocument();
  });

  it('shows stage labels correctly', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={45}
      />
    );

    // Check for stage labels
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Text Extraction')).toBeInTheDocument();
    expect(screen.getByText('Clause Analysis')).toBeInTheDocument();
    expect(screen.getByText('Summarization')).toBeInTheDocument();
  });

  it('highlights current stage', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={45}
      />
    );

    // The current stage should have "Processing..." indicator
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('shows completed stages', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.SUMMARIZATION}
        status={ProcessingStatus.PROCESSING}
        progress={75}
      />
    );

    // Previous stages should show as complete
    const completeIndicators = screen.getAllByText('Complete');
    expect(completeIndicators.length).toBeGreaterThan(0);
  });

  it('filters stages based on provided stages array', () => {
    const limitedStages = [
      ProcessingStage.UPLOAD,
      ProcessingStage.OCR,
      ProcessingStage.ANALYSIS,
    ];

    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={67}
        stages={limitedStages}
      />
    );

    // Should only show the limited stages
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Text Extraction')).toBeInTheDocument();
    expect(screen.getByText('Clause Analysis')).toBeInTheDocument();
    
    // Should not show other stages
    expect(screen.queryByText('Summarization')).not.toBeInTheDocument();
    expect(screen.queryByText('Risk Assessment')).not.toBeInTheDocument();
  });

  it('shows progress bar with correct width', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.ANALYSIS}
        status={ProcessingStatus.PROCESSING}
        progress={45}
      />
    );

    // Find progress bar (there might be multiple, get the main one)
    const progressBars = document.querySelectorAll('[style*="width: 45%"]');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('handles queued status', () => {
    render(
      <ProgressTimeline
        currentStage={ProcessingStage.UPLOAD}
        status={ProcessingStatus.QUEUED}
        progress={0}
      />
    );

    expect(screen.getByText('Waiting to start processing...')).toBeInTheDocument();
  });
});