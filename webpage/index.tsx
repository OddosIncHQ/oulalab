import React from "react";
import ReactDOM from "react-dom/client";
// Cambiamos HashRouter por BrowserRouter para tener la URL limpia (oulalab.com/care)
import { BrowserRouter } from "react-router-dom";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
