// ---------------------------------------------------------------------------
// APPLICATION ROOT COMPONENT
// ---------------------------------------------------------------------------
// Sets up client-side routing and the global layout.
// react-router-dom handles navigation between pages without full page reloads.

// BrowserRouter wraps the app and enables HTML5 history-based routing
// (no hash in URLs). Routes and Route define page mappings.
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Navbar is the top navigation bar (Dashboard, Customers, Analytics, Chat links).
import Navbar from "./components/Navbar";

// Page components — each renders a full page view.
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
import Analytics from "./pages/Analytics";
import Chat from "./pages/Chat";

// Global styles applied to the entire application.
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      {/* Navigation bar — visible on every page */}
      <Navbar />
      <main className="main-content">
        <Routes>
          {/* Route paths match the navbar links */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
