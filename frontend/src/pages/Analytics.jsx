// ---------------------------------------------------------------------------
// ANALYTICS PAGE
// ---------------------------------------------------------------------------
// Displays three interactive charts built with Recharts:
//   1. Segment Distribution — pie chart of customer segments (Silver/Gold/Platinum)
//   2. Product Preferences — bar chart of preferred product counts
//   3. Average Income by Segment — bar chart of mean annual income per segment
//
// All three datasets are fetched in parallel on mount via Promise.all.

import { useEffect, useState } from "react";

// Recharts is a composable charting library for React.
// It provides responsive containers, pie/bar charts, axes, tooltips, etc.
import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
} from "recharts";

import {
  getSegmentDistribution,
  getProductPreferences,
  getIncomeBySegment,
} from "../services/api";

// Color palette used for chart segments and bars.
const COLORS = ["#e94560", "#f5a623", "#4ade80", "#60a5fa", "#a78bfa"];

export default function Analytics() {
  const [segments, setSegments] = useState(null);
  const [products, setProducts] = useState(null);
  const [income, setIncome] = useState(null);
  const [error, setError] = useState(null);

  // Fetch all three analytics datasets on mount
  useEffect(() => {
    Promise.all([
      getSegmentDistribution(),
      getProductPreferences(),
      getIncomeBySegment(),
    ])
      .then(([s, p, i]) => {
        setSegments(s);
        setProducts(p);
        setIncome(i);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="page"><p className="error">Error: {error}</p></div>;

  return (
    <div className="page">
      <h2>Analytics</h2>
      <p className="subtitle">Customer analytics overview</p>

      <div className="charts-grid">
        {/* ---- Chart 1: Segment Distribution (Pie) ---- */}
        <div className="chart-card">
          <h3>Segment Distribution</h3>
          {!segments ? (
            <p>Loading...</p>
          ) : (
            // ResponsiveContainer makes the chart resize with the window
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={segments}
                  dataKey="count"       // numeric value for slice size
                  nameKey="segment"     // label for each slice
                  cx="50%"             // center x
                  cy="50%"             // center y
                  outerRadius={90}
                  label                // show labels on slices
                >
                  {segments.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ---- Chart 2: Product Preferences (Bar) ---- */}
        <div className="chart-card">
          <h3>Product Preferences</h3>
          {!products ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={products}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="product" stroke="#aaa" />
                <YAxis stroke="#aaa" />
                <Tooltip />
                <Bar dataKey="count" fill="#e94560" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ---- Chart 3: Average Income by Segment (Bar) ---- */}
        <div className="chart-card">
          <h3>Average Income by Segment</h3>
          {!income ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={income}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="segment" stroke="#aaa" />
                <YAxis stroke="#aaa" />
                <Tooltip />
                <Bar dataKey="avg_income" fill="#4ade80" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
