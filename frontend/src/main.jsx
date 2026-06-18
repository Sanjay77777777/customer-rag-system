// ---------------------------------------------------------------------------
// APPLICATION ENTRY POINT
// ---------------------------------------------------------------------------
// This is the first JavaScript file loaded by index.html.
// It mounts the React application into the DOM and enables StrictMode.

// StrictMode is a React development tool that:
//   - Highlights potential problems by double-invoking certain functions
//   - Does not affect the production build
//   - Helps catch side-effect bugs early
import { StrictMode } from "react";

// createRoot creates a React root at the given DOM element.
// React 18's createRoot API replaced the older ReactDOM.render().
import { createRoot } from "react-dom/client";

// Base CSS reset and global styles (applied to body, h1, etc.)
import "./index.css";

// App is the root component that sets up routing.
import App from "./App.jsx";

// Find the <div id="root"> in index.html and render the app inside it.
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
