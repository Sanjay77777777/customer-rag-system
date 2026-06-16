import { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
} from "recharts";
import {
  getSegmentDistribution,
  getProductPreferences,
  getIncomeBySegment,
} from "../services/api";

const COLORS = ["#e94560", "#f5a623", "#4ade80", "#60a5fa", "#a78bfa"];

export default function Analytics() {
  const [segments, setSegments] = useState(null);
  const [products, setProducts] = useState(null);
  const [income, setIncome] = useState(null);
  const [error, setError] = useState(null);

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
        <div className="chart-card">
          <h3>Segment Distribution</h3>
          {!segments ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={segments}
                  dataKey="count"
                  nameKey="segment"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
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
