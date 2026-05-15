import { useState, useCallback } from "react";
import { uploadPDF } from "../api/client";

/**
 * Manages PDF upload session state.
 *
 * @returns {{
 *   filename: string|null,
 *   uploadStatus: 'idle'|'uploading'|'success'|'error',
 *   uploadError: string|null,
 *   uploadFile: (file: File) => Promise<Object|null>
 * }}
 */
export function useSession() {
  const [filename, setFilename] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle");
  const [uploadError, setUploadError] = useState(null);

  const uploadFile = useCallback(async (file) => {
    setUploadStatus("uploading");
    setUploadError(null);

    try {
      const response = await uploadPDF(file);
      setFilename(response.filename);
      setUploadStatus("success");
      return response;
    } catch (error) {
      setUploadStatus("error");
      setUploadError(error.message);
      return null;
    }
  }, []);

  return { filename, uploadStatus, uploadError, uploadFile };
}
