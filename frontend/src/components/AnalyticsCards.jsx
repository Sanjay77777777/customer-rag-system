// ---------------------------------------------------------------------------
// ANALYTICS CARDS COMPONENT
// ---------------------------------------------------------------------------
// Renders a grid of summary cards used on the Dashboard page.
// Each card shows a label (e.g. "Total Customers") and a value.
//
// Props:
//   analytics — object from GET /analytics endpoint or null while loading.
//     Shape: { total_customers, average_income, platinum_customers,
//              gold_customers, silver_customers }

import "./AnalyticsCards.css";

export default function AnalyticsCards({ analytics }) {
  // Show a loading message while analytics data hasn't arrived yet
  if (!analytics) {
    return <p className="empty">Loading analytics...</p>;
  }

  // Define the 5 summary cards
  const cards = [
    { label: "Total Customers", value: analytics.total_customers },
    // toLocaleString() adds thousand separators (e.g. 85000 → "85,000")
    { label: "Average Income", value: `$${analytics.average_income?.toLocaleString()}` },
    { label: "Platinum", value: analytics.platinum_customers },
    { label: "Gold", value: analytics.gold_customers },
    { label: "Silver", value: analytics.silver_customers },
  ];

  return (
    <div className="cards-grid">
      {cards.map((card) => (
        <div className="card" key={card.label}>
          <span className="card-label">{card.label}</span>
          <span className="card-value">{card.value}</span>
        </div>
      ))}
    </div>
  );
}
