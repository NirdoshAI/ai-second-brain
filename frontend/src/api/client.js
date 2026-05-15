const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Upload a PDF file to the backend for processing.
 * @param {File} file - The PDF file to upload.
 * @returns {Promise<Object>} Parsed JSON response (UploadResponse).
 * @throws {Error} If the response is not ok, throws with the backend's error detail.
 */
export async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
    // No Content-Type header — let the browser set it with the correct boundary
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Upload failed");
  }

  return response.json();
}

/**
 * Send a question to the backend to query the currently loaded document.
 * @param {string} question - The natural language question to ask.
 * @returns {Promise<Object>} Parsed JSON response (QueryResponse).
 * @throws {Error} If the response is not ok, throws with the backend's error detail.
 */
export async function queryDocument(question) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Query failed");
  }

  return response.json();
}

/**
 * Check the health of the backend service.
 * @returns {Promise<Object>} Parsed JSON response (HealthResponse).
 */
export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  return response.json();
}
