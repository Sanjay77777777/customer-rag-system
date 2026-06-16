import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  headers: {
    "X-API-KEY": import.meta.env.VITE_API_KEY || "",
  },
});

export function getCustomers(params = {}) {
  return client.get("/customers", { params }).then((r) => r.data);
}

export function getAnalytics() {
  return client.get("/analytics").then((r) => r.data);
}

export function reindexDatabase() {
  return client.post("/reindex").then((r) => r.data);
}

export function getSegmentDistribution() {
  return client.get("/analytics/segments").then((r) => r.data);
}

export function getProductPreferences() {
  return client.get("/analytics/products").then((r) => r.data);
}

export function getIncomeBySegment() {
  return client.get("/analytics/income").then((r) => r.data);
}
