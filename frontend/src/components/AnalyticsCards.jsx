import "./AnalyticsCards.css";

export default function AnalyticsCards({ analytics }) {
  if (!analytics) {
    return <p className="empty">Loading analytics...</p>;
  }

  const cards = [
    { label: "Total Customers", value: analytics.total_customers },
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
