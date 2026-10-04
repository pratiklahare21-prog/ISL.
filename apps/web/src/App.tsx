import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TranslatorPage } from "./pages/TranslatorPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TranslatorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
