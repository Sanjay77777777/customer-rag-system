// ---------------------------------------------------------------------------
// VITE DEVELOPMENT CONFIGURATION
// ---------------------------------------------------------------------------
// Vite is the build tool and dev server for the React frontend.
// This file configures the React plugin and a dev proxy that forwards
// /api/* requests to the FastAPI backend running on port 8000.
//
// In production, the proxy is handled by nginx (see nginx.conf).

// defineConfig provides type hints and validation for Vite config.
import { defineConfig } from "vite";

// @vitejs/plugin-react enables React Fast Refresh and JSX transform.
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    proxy: {
      // Any request to /api/* during development (e.g. /api/customers)
      // is forwarded to http://127.0.0.1:8000/*.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // Strip the /api prefix so the backend receives /customers, not /api/customers
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
