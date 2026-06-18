// ---------------------------------------------------------------------------
// DASHBOARD PAGE
// ---------------------------------------------------------------------------
// Landing page that shows analytics summary cards and a button to rebuild
// the ChromaDB vector index.

import { useEffect, useState } from "react";
import { getAnalytics, reindexDatabase } from "../services/api";
import AnalyticsCards from "../components/AnalyticsCards";

export default function Dashboard() {
  // analytics stores the response from GET /analytics (or null while loading)
  const [analytics, setAnalytics] = useState(null);
  // reindexing tracks whether a reindex POST is in progress
  const [reindexing, setReindexing] = useState(false);
  // reindexMsg shows success/error feedback after reindex completes
  const [reindexMsg, setReindexMsg] = useState(null);

  // On mount, fetch analytics data once (empty dependency array = run once)
  useEffect(() => {
    getAnalytics().then(setAnalytics).catch(console.error);
  }, []);

  // Called when the "Reindex Vector Database" button is clicked
  async function handleReindex() {
    setReindexing(true);
    setReindexMsg(null);
    try {
      const result = await reindexDatabase();
      setReindexMsg(
        `Indexed ${result.indexed_customers} customers successfully.`
      );
    } catch (err) {
      setReindexMsg(`Error: ${err.message}`);
    } finally {
      setReindexing(false);
    }
  }

  return (
    <div className="page">
      <h2>Dashboard</h2>
      <p className="subtitle">Customer analytics overview</p>
      {/* AnalyticsCards renders 5 summary cards once analytics loads */}
      <AnalyticsCards analytics={analytics} />

      {/* Reindex button — disabled while a reindex is running */}
      <div className="card vector-db-card">
        <span className="card-label">Vector Database</span>
        <button
          className="reindex-button"
          onClick={handleReindex}
          disabled={reindexing}
        >
          {reindexing ? "Reindexing..." : "Reindex Vector Database"}
        </button>
        {reindexMsg && <p className="reindex-msg">{reindexMsg}</p>}
      </div>
    </div>
  );
}
