/**
 * App.jsx
 * -------
 * Router principal de la app Frontend de MiPlaza.
 *
 * RESPONSABILIDAD:
 * - Definir rutas (solo navegación).
 * - No contiene lógica de negocio.
 *
 * Rutas:
 * - "/"     => Home (pantalla actual de prueba Tailwind)
 * - "/feed" => FeedPage (ETAPA 32)
 */

import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import FeedPage from "./pages/FeedPage";

/**
 * HomePage:
 * - Dejamos tu pantalla actual intacta, solo la encapsulamos como "Home".
 */
function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900">
      <h1 className="text-4xl font-bold text-purple-400">
        TailwindCSS v4 funcionando en MiTienda 🚀
      </h1>

      {/* Navegación mínima para testear rutas */}
      <div className="mt-6">
        <Link
          to="/feed"
          className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 text-white"
        >
          Ir al Feed
        </Link>
      </div>
    </div>
  );
}

/**
 * App:
 * - Define el enrutado principal.
 */
export default function App() {
  return (
    <BrowserRouter>
      {/* Barra simple arriba para volver al Home */}
      <div className="bg-gray-950 text-white p-3 flex gap-4">
        <Link to="/" className="hover:underline">
          Home
        </Link>
        <Link to="/feed" className="hover:underline">
          Feed
        </Link>
      </div>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/feed" element={<FeedPage />} />
      </Routes>
    </BrowserRouter>
  );
}
