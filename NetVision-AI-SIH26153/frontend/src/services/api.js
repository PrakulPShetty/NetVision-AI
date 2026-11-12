/**
 * NetVision AI — Primary API Client Service
 *
 * Interacts with the FastAPI backend:
 *   GET  /health          — engine reachability
 *   POST /forecast        — practical profile or 138-feature forecast
 *   POST /preprocess/file — capture upload (see services/upload.js)
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch system health status
 */
export async function getHealthStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`Health check failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Health Check Error:', error);
    return {
      status: 'unavailable',
      error: error.message,
    };
  }
}

async function postForecast(body) {
  try {
    const response = await fetch(`${API_BASE_URL}/forecast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (response.status === 422) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Traffic data validation failed.');
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend error (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error('API Forecast Request Error:', error);
    return {
      success: false,
      error:
        error.message ||
        'Unable to connect to NetVision AI forecast engine.',
    };
  }
}

/**
 * Submit a practical 40-field traffic profile.
 *
 * @param {Object} trafficData - Practical network traffic fields
 * @returns {Promise<Object>} Unified forecast response from backend
 */
export async function submitTrafficForecast(trafficData) {
  return postForecast({ traffic: trafficData });
}

/**
 * Submit a complete 138-feature model row (feature CSV path).
 *
 * @param {Object} features - Exactly 138 model-ready feature values
 * @returns {Promise<Object>} Unified forecast response from backend
 */
export async function submitFeatureForecast(features) {
  return postForecast({ features });
}
