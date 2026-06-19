// frontend/src/features/auth/index.js

// Contexto principal de autenticación.
export { AuthProvider, AuthContext } from "@features/auth/context/AuthContext";

// Hook oficial para consumir autenticación.
export { useAuth } from "@features/auth/hooks/useAuth";

// Servicios de autenticación.
export {
  loginUsuario,
  logoutUsuario,
  getMe,
  actualizarPerfilUsuario,
  registrarUsuario,
} from "@features/auth/services/authService";

export * from '@features/auth/services/usuarioService';

export { default as Login } from '@features/auth/pages/Login';
export { default as Registro } from '@features/auth/pages/Registro';
export { default as ProfilePage } from '@features/auth/pages/ProfilePage';
