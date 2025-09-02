import React, { useState, useEffect } from 'react';
import {
  Volume2,
  Download,
  Play,
  Pause,
  Settings,
  FileAudio,
  FileText,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
} from 'lucide-react';
import {
  audioExportService,
  AudioExportOptions,
  TranscriptExportOptions,
  VoiceOption,
  AudioExportResponse,
} from '../../services/audioExportService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { AccessibleModal } from '../accessibility';
import { cn } from '../../lib/utils';

interface AudioExportCenterProps {
  documentId: string;
  jobId: string;
  className?: string;
}

interface AudioExportJob {
  id: string;
  content: string;
  status: 'generating' | 'ready' | 'failed';
  progress: number;
  audioFilename?: string;
  transcriptFilename?: string;
  audioUrl?: string;
  transcriptUrl?: string;
  duration?: number;
  error?: string;
  createdAt: string;
}

export const AudioExportCenter: React.FC<AudioExportCenterProps> = ({
  documentId,
  jobId,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [audioOptions, setAudioOptions] = useState<AudioExportOptions>({
    format: 'mp3',
    quality: 'high',
    voice: '',
    speed: 1.0,
    includeTimestamps: true,
    includeChapters: true,
  });
  const [transcriptOptions, setTranscriptOptions] = useState<TranscriptExportOptions>({
    format: 'srt',
    includeTimestamps: true,
    includeMetadata: true,
    chapterMarkers: true,
  });
  const [selectedContent, setSelectedContent] = useState<'summary' | 'full_document' | 'risk_analysis'>('summary');
  const [audioJobs, setAudioJobs] = useState<AudioExportJob[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const { announceSuccess, announceError, announceStatus } = useAriaAnnouncements();

  // Load available voices
  useEffect(() => {
    loadVoices();
  }, []);

  // Set default voice when voices are loaded
  useEffect(() => {
    if (voices.length > 0 && !selectedVoice) {
      const defaultVoice = voices.find(v => v.language === 'en-US') || voices[0];
      setSelectedVoice(defaultVoice.id);
      setAudioOptions(prev => ({ ...prev, voice: defaultVoice.id }));
    }
  }, [voices, selectedVoice]);

  // Poll for audio export status updates
  useEffect(() => {
    if (audioJobs.length === 0) return;

    const interval = setInterval(async () => {
      const updatedJobs = await Promise.all(
        audioJobs.map(async (job) => {
          if (job.status === 'generating') {
            try {
              const status = await audioExportService.getAudioExportStatus(job.id);
              return {
                ...job,
                status: status.status,
                progress: status.status === 'ready' ? 100 : job.progress,
                audioUrl: status.audioUrl,
                transcriptUrl: status.transcriptUrl,
                duration: status.duration,
                audioFilename: status.filename,
                transcriptFilename: status.transcriptFilename,
              };
            } catch (error) {
              return {
                ...job,
                status: 'failed' as const,
                error: 'Failed to get export status',
              };
            }
          }
          return job;
        })
      );

      setAudioJobs(updatedJobs);

      // Announce completed exports
      updatedJobs.forEach((job, index) => {
        const oldJob = audioJobs[index];
        if (oldJob?.status === 'generating' && job.status === 'ready') {
          announceSuccess(`Audio export completed: ${job.audioFilename}`);
        } else if (oldJob?.status === 'generating' && job.status === 'failed') {
          announceError('Audio export failed');
        }
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [audioJobs, announceSuccess, announceError]);

  const loadVoices = async () => {
    try {
      const availableVoices = await audioExportService.getAvailableVoices();
      setVoices(availableVoices);
    } catch (error) {
      announceError('Failed to load available voices');
      console.error('Error loading voices:', error);
    }
  };

  const handleVoicePreview = async (voiceId: string) => {
    try {
      const sampleText = "This is a preview of how your document will sound when narrated.";
      const audioBlob = await audioExportService.previewVoice(voiceId, sampleText);
      
      if (previewAudio) {
        previewAudio.pause();
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        announceError('Failed to play voice preview');
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      setPreviewAudio(audio);
      setIsPlaying(true);
      audio.play();
      
      announceStatus('Playing voice preview');
    } catch (error) {
      announceError('Failed to preview voice');
      console.error('Voice preview error:', error);
    }
  };

  const stopPreview = () => {
    if (previewAudio) {
      previewAudio.pause();
      setIsPlaying(false);
    }
  };

  const handleGenerateAudio = async () => {
    setIsGenerating(true);
    announceStatus('Starting audio generation');

    try {
      const response = await audioExportService.requestAudioExport({
        documentId,
        jobId,
        content: selectedContent,
        audioOptions: { ...audioOptions, voice: selectedVoice },
        transcriptOptions,
      });

      const newJob: AudioExportJob = {
        id: response.exportId,
        content: selectedContent,
        status: response.status,
        progress: 0,
        audioFilename: response.filename,
        transcriptFilename: response.transcriptFilename,
        audioUrl: response.audioUrl,
        transcriptUrl: response.transcriptUrl,
        duration: response.duration,
        createdAt: new Date().toISOString(),
      };

      setAudioJobs(prev => [newJob, ...prev]);
      announceSuccess('Audio generation started');
    } catch (error) {
      announceError('Failed to start audio generation');
      console.error('Audio generation error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadAudio = async (job: AudioExportJob) => {
    if (!job.audioUrl) return;

    try {
      announceStatus('Starting audio download');
      
      const link = document.createElement('a');
      link.href = job.audioUrl;
      link.download = job.audioFilename || 'audio.mp3';
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      announceSuccess(`Downloaded ${job.audioFilename}`);
    } catch (error) {
      announceError(`Failed to download ${job.audioFilename}`);
      console.error('Download error:', error);
    }
  };

  const handleDownloadTranscript = async (job: AudioExportJob) => {
    if (!job.transcriptUrl) return;

    try {
      announceStatus('Starting transcript download');
      
      const link = document.createElement('a');
      link.href = job.transcriptUrl;
      link.download = job.transcriptFilename || 'transcript.srt';
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      announceSuccess(`Downloaded ${job.transcriptFilename}`);
    } catch (error) {
      announceError(`Failed to download ${job.transcriptFilename}`);
      console.error('Download error:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'generating':
        return <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700',
          'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors',
          className
        )}
        aria-label="Open audio export center"
      >
        <Volume2 className="w-4 h-4" />
        <span>Audio Export</span>
      </button>

      <AccessibleModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Audio Export Center"
        description="Generate audio narration and transcripts for your document"
        size="lg"
      >
        <div className="space-y-6">
          {/* Content Selection */}
          <div>
            <h3 className="text-lg font-medium mb-4">Content to Narrate</h3>
            <div className="space-y-2">
              {[
                { value: 'summary', label: 'Document Summary', description: 'Plain language summary of the document' },
                { value: 'full_document', label: 'Full Document', description: 'Complete document text' },
                { value: 'risk_analysis', label: 'Risk Analysis', description: 'Risk assessment and recommendations' },
              ].map(({ value, label, description }) => (
                <label key={value} className="flex items-start space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="content"
                    value={value}
                    checked={selectedContent === value}
                    onChange={(e) => setSelectedContent(e.target.value as any)}
                    className="mt-1 text-purple-600 focus:ring-purple-500"
                  />
                  <div>
                    <div className="font-medium">{label}</div>
                    <div className="text-sm text-gray-600">{description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice Selection */}
          <div>
            <h3 className="text-lg font-medium mb-4">Voice Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Voice</label>
                <div className="grid grid-cols-1 gap-3 max-h-40 overflow-y-auto">
                  {voices.map((voice) => (
                    <div
                      key={voice.id}
                      className={cn(
                        'p-3 border rounded-lg cursor-pointer transition-colors',
                        selectedVoice === voice.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                      onClick={() => {
                        setSelectedVoice(voice.id);
                        setAudioOptions(prev => ({ ...prev, voice: voice.id }));
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{voice.name}</div>
                          <div className="text-sm text-gray-600">
                            {voice.language} • {voice.gender}
                          </div>
                          <div className="text-xs text-gray-500">{voice.description}</div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (isPlaying) {
                              stopPreview();
                            } else {
                              handleVoicePreview(voice.id);
                            }
                          }}
                          className="p-2 text-purple-600 hover:text-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-md"
                          aria-label={`Preview ${voice.name} voice`}
                        >
                          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Audio Options */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Format</label>
                  <select
                    value={audioOptions.format}
                    onChange={(e) => setAudioOptions(prev => ({ ...prev, format: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="mp3">MP3</option>
                    <option value="wav">WAV</option>
                    <option value="ogg">OGG</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Quality</label>
                  <select
                    value={audioOptions.quality}
                    onChange={(e) => setAudioOptions(prev => ({ ...prev, quality: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="low">Low (64 kbps)</option>
                    <option value="medium">Medium (128 kbps)</option>
                    <option value="high">High (320 kbps)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Speed: {audioOptions.speed}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={audioOptions.speed}
                  onChange={(e) => setAudioOptions(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.5x</span>
                  <span>1.0x</span>
                  <span>2.0x</span>
                </div>
              </div>
            </div>
          </div>

          {/* Transcript Options */}
          <div>
            <h3 className="text-lg font-medium mb-4">Transcript Options</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-2">Transcript Format</label>
                <select
                  value={transcriptOptions.format}
                  onChange={(e) => setTranscriptOptions(prev => ({ ...prev, format: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="srt">SRT (SubRip)</option>
                  <option value="vtt">VTT (WebVTT)</option>
                  <option value="txt">Plain Text</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={transcriptOptions.includeTimestamps}
                    onChange={(e) => setTranscriptOptions(prev => ({ ...prev, includeTimestamps: e.target.checked }))}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span>Include timestamps</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={transcriptOptions.chapterMarkers}
                    onChange={(e) => setTranscriptOptions(prev => ({ ...prev, chapterMarkers: e.target.checked }))}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span>Include chapter markers</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={transcriptOptions.includeMetadata}
                    onChange={(e) => setTranscriptOptions(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span>Include metadata</span>
                </label>
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <div className="flex justify-end">
            <button
              onClick={handleGenerateAudio}
              disabled={isGenerating || !selectedVoice}
              className={cn(
                'flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-md',
                'hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              )}
            >
              {isGenerating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
              <span>{isGenerating ? 'Generating...' : 'Generate Audio'}</span>
            </button>
          </div>

          {/* Audio Jobs */}
          {audioJobs.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-4">Audio Exports</h3>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {audioJobs.map((job) => (
                  <div
                    key={job.id}
                    className="p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(job.status)}
                        <span className="font-medium">{job.content.replace('_', ' ')}</span>
                        {job.duration && (
                          <span className="text-sm text-gray-500">
                            ({formatDuration(job.duration)})
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {job.status === 'ready' && job.audioUrl && (
                          <button
                            onClick={() => handleDownloadAudio(job)}
                            className="p-2 text-purple-600 hover:text-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-md"
                            aria-label="Download audio file"
                          >
                            <FileAudio className="w-4 h-4" />
                          </button>
                        )}
                        {job.status === 'ready' && job.transcriptUrl && (
                          <button
                            onClick={() => handleDownloadTranscript(job)}
                            className="p-2 text-purple-600 hover:text-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-md"
                            aria-label="Download transcript file"
                          >
                            <FileText className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {job.status === 'generating' && (
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 bg-purple-500 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    )}

                    {job.status === 'failed' && (
                      <div className="text-sm text-red-600">
                        {job.error || 'Audio generation failed'}
                      </div>
                    )}

                    {job.status === 'ready' && (
                      <div className="text-sm text-green-600">
                        Audio and transcript ready for download
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </AccessibleModal>
    </>
  );
};

export default AudioExportCenter;