// ---------------------------------------------------------------------------
// API Service Layer
// ---------------------------------------------------------------------------
// This module provides all the functions that the frontend pages use to
// communicate with the FastAPI backend. Each function returns a Promise
// that resolves to the JSON response body.
//
// Base URL is "/api" — in development, Vite's dev server proxies /api/* to
// http://127.0.0.1:8000/*. In production, nginx does the same proxying.

// axios is a Promise-based HTTP client for browser and Node.js.
// It handles request/response serialization, error handling, and
// provides a clean API for GET/POST/etc.
import axios from "axios";

// Create a pre-configured axios instance with the /api base URL.
// All requests will be relative to this prefix.
const client = axios.create({
  baseURL: "/api",
});

// ---------------------------------------------------------------------------
// READ ENDPOINTS (no authentication)
// ---------------------------------------------------------------------------

// GET /customers — fetch customer list with optional filter params.
// Example: getCustomers({ segment: "Gold" }) → ?segment=Gold
export function getCustomers(params = {}) {
  return client.get("/customers", { params }).then((r) => r.data);
}

// GET /analytics — aggregated dashboard statistics.
// Returns { total_customers, average_income, platinum_customers, ... }
export function getAnalytics() {
  return client.get("/analytics").then((r) => r.data);
}

// GET /analytics/segments — segment distribution for pie chart.
// Returns [{ segment: "Gold", count: 5 }, ...]
export function getSegmentDistribution() {
  return client.get("/analytics/segments").then((r) => r.data);
}

// GET /analytics/products — product preference counts for bar chart.
// Returns [{ product: "Laptop", count: 4 }, ...]
export function getProductPreferences() {
  return client.get("/analytics/products").then((r) => r.data);
}

// GET /analytics/income — average income per segment for bar chart.
// Returns [{ segment: "Gold", avg_income: 95000 }, ...]
export function getIncomeBySegment() {
  return client.get("/analytics/income").then((r) => r.data);
}

// ---------------------------------------------------------------------------
// WRITE ENDPOINTS
// ---------------------------------------------------------------------------

// POST /reindex — rebuild the ChromaDB vector index from PostgreSQL.
// Returns { status: "success", indexed_customers: 40 }
export function reindexDatabase() {
  return client.post("/reindex").then((r) => r.data);
}
