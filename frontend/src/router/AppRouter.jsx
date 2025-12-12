// React Router: componentes necesarios para manejar rutas
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Importamos las páginas
import Home from "../pages/Home";
import Login from "../pages/Login";

// Importamos el layout principal
import MainLayout from "../layouts/MainLayout";

/**
 * AppRouter
 * Define todas las rutas de la aplicación.
 */
export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/*
          Rutas con layout principal
        */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
