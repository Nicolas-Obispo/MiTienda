import { useState } from "react";
import { loginUsuario } from "../services/authService";
import { useAuth } from "../context/AuthContext";

/**
 * Login
 * Página de inicio de sesión.
 *
 * Responsabilidades:
 * - Capturar credenciales del usuario
 * - Llamar al backend (/usuarios/login)
 * - Guardar el token en el AuthContext
 */
export default function Login() {
  // Estados del formulario
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMensaje, setErrorMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  // Función login del AuthContext
  const { login } = useAuth();

  /**
   * manejarSubmitLogin
   * Envía las credenciales al backend y,
   * si son válidas, guarda el token en el AuthContext.
   */
  async function manejarSubmitLogin(event) {
    event.preventDefault();
    setErrorMensaje("");
    setCargando(true);

    try {
      // Llamada al backend
      const token = await loginUsuario({ email, password });

      // Guardamos el token en el contexto global
      login(token);
    } catch (error) {
      setErrorMensaje(error.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <h2>Iniciar sesión</h2>

      <form onSubmit={manejarSubmitLogin}>
        <div>
          <label>Email</label>
          <br />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label>Password</label>
          <br />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={cargando}>
          {cargando ? "Ingresando..." : "Ingresar"}
        </button>
      </form>

      {errorMensaje && (
        <p style={{ color: "red" }}>{errorMensaje}</p>
      )}
    </div>
  );
}
