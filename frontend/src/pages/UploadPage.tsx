import React from 'react';
import { DocumentUploader } from '../components/upload';
import { UploadResponse } from '../types';

export const UploadPage: React.FC = () => {
  const handleUploadComplete = (response: UploadResponse) => {
    console.log('Upload completed:', response);
    // Here you would typically navigate to a job status page or show a success message
  };

  const handleError = (error: string) => {
    console.error('Upload error:', error);
    // Here you would typically show an error toast or message
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Upload Legal Documents
          </h1>
          <p className="mt-2 text-gray-600">
            Upload your legal documents for AI-powered analysis and risk assessment.
          </p>
        </div>

        <div className="rounded-lg bg-white p-6 shadow">
          <DocumentUploader
            onUploadComplete={handleUploadComplete}
            onError={handleError}
          />
        </div>

        <div className="mt-8 rounded-lg bg-blue-50 p-4">
          <h3 className="text-sm font-medium text-blue-900">
            Supported File Types
          </h3>
          <ul className="mt-2 text-sm text-blue-700">
            <li>• PDF documents (.pdf)</li>
            <li>• Microsoft Word documents (.docx, .doc)</li>
            <li>• Images of documents (.jpg, .jpeg, .png, .tiff, .bmp)</li>
          </ul>
        </div>

        <div className="mt-4 rounded-lg bg-yellow-50 p-4">
          <h3 className="text-sm font-medium text-yellow-900">
            Privacy & Security
          </h3>
          <p className="mt-2 text-sm text-yellow-700">
            Your documents are encrypted during upload and processing. 
            All data is automatically deleted after 30 days unless you specify otherwise.
          </p>
        </div>
      </div>
    </div>
  );
};