// frontend/src/features/auth/index.js

// Contexto principal de autenticación.
export { AuthProvider } from "@features/auth/context/AuthContext";

// Hook oficial para consumir autenticación.
export { useAuth } from "@features/auth/hooks/useAuth";

// Servicios de autenticación.
export {
  loginUsuario,
  logoutUsuario,
  getMe,
  actualizarPerfilUsuario,
  registrarUsuario,
  comprobarDisponibilidadEmail,
  REGISTRATION_EMAIL_UNAVAILABLE,
  EMAIL_VERIFICATION_INVALID,
  EMAIL_VERIFICATION_RATE_LIMITED,
  confirmarEmail,
  reenviarVerificacionEmail,
  extraerTokenVerificacionDelFragmento,
  solicitarRecuperacionPassword,
  restablecerPassword,
  PASSWORD_RESET_INVALID,
  cambiarPasswordAutenticado,
  CURRENT_PASSWORD_INCORRECT,
  CURRENT_PASSWORD_RATE_LIMITED,
  PHONE_VERIFICATION_INVALID,
  PHONE_VERIFICATION_RATE_LIMITED,
  solicitarVerificacionTelefono,
  confirmarVerificacionTelefono,
} from "@features/auth/services/authService";

export * from '@features/auth/services/usuarioService';

export { default as Login } from '@features/auth/pages/Login';
export { default as Registro } from '@features/auth/pages/Registro';
export { default as VerificarEmail } from '@features/auth/pages/VerificarEmail';
export { default as RecuperarPassword } from '@features/auth/pages/RecuperarPassword';
export { default as RestablecerPassword } from '@features/auth/pages/RestablecerPassword';
export { default as ProfilePage } from '@features/auth/pages/ProfilePage';
