import { Route, Routes } from "react-router-dom";
import Landing from "./routes/landing";
import Dashboard from "./routes/dashboard";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}
