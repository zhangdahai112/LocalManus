/**
 * Utility to get the correct API URL based on the execution context.
 * 
 * - Server-side (SSR): Uses BACKEND_URL (Docker internal network)
 * - Client-side (Browser): Uses NEXT_PUBLIC_API_URL (External access)
 */
export const getApiBaseUrl = (): string => {
  // Check if we are in the browser
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  // We are on the server (SSR)
  // Use the internal Docker service name if available
  return process.env.BACKEND_URL || 'http://localhost:8000';
};
