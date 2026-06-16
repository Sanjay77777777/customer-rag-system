import { useEffect, useState } from "react";
import { getAnalytics, reindexDatabase } from "../services/api";
import AnalyticsCards from "../components/AnalyticsCards";

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMsg, setReindexMsg] = useState(null);

  useEffect(() => {
    getAnalytics().then(setAnalytics).catch(console.error);
  }, []);

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
      <AnalyticsCards analytics={analytics} />

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
