import { useState, useRef } from "react";
import LoadingSpinner from "./LoadingSpinner";
import "./components.css";

/**
 * PDF upload panel.
 *
 * @param {{
 *   filename: string|null,
 *   uploadStatus: 'idle'|'uploading'|'success'|'error',
 *   uploadError: string|null,
 *   uploadFile: (file: File) => Promise<any>,
 *   onUploadSuccess?: () => void
 * }} props
 */
export default function UploadPanel({
  filename,
  uploadStatus,
  uploadError,
  uploadFile,
  onUploadSuccess,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const isUploading = uploadStatus === "uploading";
  const isSuccess = uploadStatus === "success";

  function handleFileChange(e) {
    const file = e.target.files[0] || null;
    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    const result = await uploadFile(selectedFile);
    if (result !== null) {
      setSelectedFile(null);
      // Reset the file input so the same file can be re-selected later
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onUploadSuccess) onUploadSuccess();
    }
  }

  return (
    <div className="upload-panel">
      <p className="upload-panel__title">Upload PDF</p>

      <div className="upload-panel__row">
        {/* Hidden real file input */}
        <input
          ref={fileInputRef}
          id="pdf-file-input"
          type="file"
          accept=".pdf,application/pdf"
          className="upload-panel__file-input"
          disabled={isUploading}
          onChange={handleFileChange}
        />

        {/* Styled label acting as the visible button */}
        <label
          htmlFor="pdf-file-input"
          className={`upload-panel__file-label${isUploading ? " upload-panel__file-label--disabled" : ""}`}
        >
          Choose file
        </label>

        {/* Selected file name */}
        <span className="upload-panel__filename">
          {selectedFile ? selectedFile.name : "No file chosen"}
        </span>

        {/* Upload button */}
        <button
          className="upload-panel__btn"
          onClick={handleUpload}
          disabled={isUploading || !selectedFile}
        >
          {isUploading ? <LoadingSpinner small /> : "Upload"}
        </button>
      </div>

      {/* Status messages */}
      {isUploading && (
        <div className="upload-panel__status">
          <LoadingSpinner small />
          <span>Processing…</span>
        </div>
      )}

      {isSuccess && filename && (
        <div className="upload-panel__status upload-panel__status--success">
          ✓ Loaded: {filename}
        </div>
      )}

      {uploadStatus === "error" && uploadError && (
        <div className="upload-panel__status upload-panel__status--error">
          {uploadError}
        </div>
      )}
    </div>
  );
}
