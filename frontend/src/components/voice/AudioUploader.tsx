import React, { useState, useCallback, useRef } from 'react';
import {
  Upload,
  File,
  Play,
  Pause,
  Trash2,
  Download,
  AlertCircle,
  CheckCircle,
  Music,
  FileAudio,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface AudioUploaderProps {
  onFileUpload?: (file: File, duration?: number) => void;
  onFileRemove?: () => void;
  onError?: (error: string) => void;
  acceptedFormats?: string[];
  maxFileSize?: number; // in MB
  maxDuration?: number; // in seconds
  disabled?: boolean;
  className?: string;
  showPreview?: boolean;
  allowMultiple?: boolean;
}

interface AudioFileInfo {
  file: File;
  url: string;
  duration: number;
  size: string;
  format: string;
}

const DEFAULT_ACCEPTED_FORMATS = [
  'audio/mp3',
  'audio/mpeg',
  'audio/wav',
  'audio/ogg',
  'audio/webm',
  'audio/m4a',
  'audio/aac',
];

export const AudioUploader: React.FC<AudioUploaderProps> = ({
  onFileUpload,
  onFileRemove,
  onError,
  acceptedFormats = DEFAULT_ACCEPTED_FORMATS,
  maxFileSize = 50, // 50MB default
  maxDuration = 600, // 10 minutes default
  disabled = false,
  className,
  showPreview = true,
  allowMultiple = false,
}) => {
  const [audioFiles, setAudioFiles] = useState<AudioFileInfo[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioElementsRef = useRef<Map<string, HTMLAudioElement>>(new Map());

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get audio duration
  const getAudioDuration = (file: File): Promise<number> => {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      const url = URL.createObjectURL(file);
      
      audio.onloadedmetadata = () => {
        URL.revokeObjectURL(url);
        resolve(audio.duration);
      };
      
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('Failed to load audio file'));
      };
      
      audio.src = url;
    });
  };

  // Validate file
  const validateFile = async (file: File): Promise<{ valid: boolean; error?: string }> => {
    // Check file type
    if (!acceptedFormats.includes(file.type)) {
      return {
        valid: false,
        error: `Unsupported file format. Accepted formats: ${acceptedFormats.join(', ')}`,
      };
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      return {
        valid: false,
        error: `File size too large. Maximum size: ${maxFileSize}MB`,
      };
    }

    // Check duration
    try {
      const duration = await getAudioDuration(file);
      if (duration > maxDuration) {
        return {
          valid: false,
          error: `Audio too long. Maximum duration: ${formatDuration(maxDuration)}`,
        };
      }
    } catch (error) {
      return {
        valid: false,
        error: 'Invalid audio file or unable to read duration',
      };
    }

    return { valid: true };
  };

  // Process uploaded files
  const processFiles = useCallback(async (files: FileList) => {
    if (!files.length) return;

    setIsProcessing(true);

    try {
      const newAudioFiles: AudioFileInfo[] = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Validate file
        const validation = await validateFile(file);
        if (!validation.valid) {
          onError?.(validation.error!);
          continue;
        }

        // Get file info
        const duration = await getAudioDuration(file);
        const url = URL.createObjectURL(file);
        
        const audioInfo: AudioFileInfo = {
          file,
          url,
          duration,
          size: formatFileSize(file.size),
          format: file.type.split('/')[1].toUpperCase(),
        };

        newAudioFiles.push(audioInfo);
        onFileUpload?.(file, duration);

        // If not allowing multiple files, break after first valid file
        if (!allowMultiple) break;
      }

      if (allowMultiple) {
        setAudioFiles(prev => [...prev, ...newAudioFiles]);
      } else {
        // Clear previous files if not allowing multiple
        audioFiles.forEach(audioFile => URL.revokeObjectURL(audioFile.url));
        setAudioFiles(newAudioFiles);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process audio files';
      onError?.(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  }, [audioFiles, allowMultiple, onFileUpload, onError, maxFileSize, maxDuration, acceptedFormats]);

  // Handle file input change
  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      processFiles(files);
    }
    // Reset input value to allow selecting the same file again
    event.target.value = '';
  }, [processFiles]);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  }, [processFiles]);

  // Handle click to upload
  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  // Play/pause audio
  const handlePlayPause = useCallback((audioInfo: AudioFileInfo) => {
    const audioId = audioInfo.file.name;
    let audio = audioElementsRef.current.get(audioId);

    if (!audio) {
      audio = new Audio(audioInfo.url);
      audio.onended = () => setCurrentlyPlaying(null);
      audio.onpause = () => setCurrentlyPlaying(null);
      audio.onplay = () => setCurrentlyPlaying(audioId);
      audioElementsRef.current.set(audioId, audio);
    }

    if (currentlyPlaying === audioId) {
      audio.pause();
    } else {
      // Pause any currently playing audio
      audioElementsRef.current.forEach((audioEl, id) => {
        if (id !== audioId) {
          audioEl.pause();
        }
      });
      audio.play();
    }
  }, [currentlyPlaying]);

  // Remove file
  const handleRemoveFile = useCallback((index: number) => {
    const audioInfo = audioFiles[index];
    
    // Stop and cleanup audio element
    const audioId = audioInfo.file.name;
    const audio = audioElementsRef.current.get(audioId);
    if (audio) {
      audio.pause();
      audioElementsRef.current.delete(audioId);
    }
    
    // Revoke object URL
    URL.revokeObjectURL(audioInfo.url);
    
    // Remove from state
    const newFiles = audioFiles.filter((_, i) => i !== index);
    setAudioFiles(newFiles);
    
    if (newFiles.length === 0) {
      onFileRemove?.();
    }
  }, [audioFiles, onFileRemove]);

  // Download file
  const handleDownload = useCallback((audioInfo: AudioFileInfo) => {
    const link = document.createElement('a');
    link.href = audioInfo.url;
    link.download = audioInfo.file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      audioFiles.forEach(audioInfo => URL.revokeObjectURL(audioInfo.url));
      audioElementsRef.current.forEach(audio => audio.pause());
    };
  }, []);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Upload Area */}
      <div
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200',
          dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
          disabled && 'opacity-50 cursor-not-allowed',
          !disabled && 'cursor-pointer hover:bg-gray-50'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          multiple={allowMultiple}
          onChange={handleFileChange}
          disabled={disabled}
          className="hidden"
        />

        {isProcessing ? (
          <div className="space-y-2">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-gray-600">Processing audio files...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <FileAudio className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900">
                {dragActive ? 'Drop audio files here' : 'Upload audio files'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Drag and drop or click to select audio files
              </p>
            </div>
            
            <div className="text-xs text-gray-500 space-y-1">
              <p>Supported formats: {acceptedFormats.map(f => f.split('/')[1]).join(', ')}</p>
              <p>Max file size: {maxFileSize}MB • Max duration: {formatDuration(maxDuration)}</p>
            </div>
          </div>
        )}
      </div>

      {/* File List */}
      {showPreview && audioFiles.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-900">Uploaded Files</h4>
          
          {audioFiles.map((audioInfo, index) => (
            <div
              key={`${audioInfo.file.name}-${index}`}
              className="bg-white border rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="flex-shrink-0">
                    <Music className="w-8 h-8 text-blue-500" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {audioInfo.file.name}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                      <span>{audioInfo.format}</span>
                      <span>{audioInfo.size}</span>
                      <span>{formatDuration(audioInfo.duration)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    onClick={() => handlePlayPause(audioInfo)}
                    className="p-2 text-gray-400 hover:text-blue-500 rounded-md hover:bg-gray-100 transition-colors"
                    title={currentlyPlaying === audioInfo.file.name ? 'Pause' : 'Play'}
                  >
                    {currentlyPlaying === audioInfo.file.name ? (
                      <Pause className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                  
                  <button
                    onClick={() => handleDownload(audioInfo)}
                    className="p-2 text-gray-400 hover:text-green-500 rounded-md hover:bg-gray-100 transition-colors"
                    title="Download"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="p-2 text-gray-400 hover:text-red-500 rounded-md hover:bg-gray-100 transition-colors"
                    title="Remove"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Success Message */}
      {audioFiles.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-700">
              {audioFiles.length} audio file{audioFiles.length > 1 ? 's' : ''} uploaded successfully
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AudioUploader;