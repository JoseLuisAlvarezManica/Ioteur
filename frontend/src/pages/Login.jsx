import { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState(null);
  const successMessage          = location.state?.message;

  const handleLogin = async () => {
    if (!email || !password) {
      setError("Por favor ingresa tu correo y contraseña.");
      return;
    }
    setError(null);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Credenciales incorrectas.");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleLogin();
  };

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col">
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <span className="font-bold text-xl text-purple-700 tracking-tight flex items-center gap-2">
          Ioteur
        </span>
        <span className="text-gray-400 text-sm">Secure Login</span>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="bg-white shadow-xl rounded-3xl p-10 w-full max-w-[480px] flex flex-col items-center gap-6 border border-purple-100">

          {/* Logo */}
          <div className="w-28 h-28 bg-gradient-to-tr from-white to-purple-200 shadow-lg rounded-3xl flex items-center justify-center text-white p-4">
            <img src="/logoioteur.svg" alt="Logo" className="w-16 h-16"/>
          </div>

          {/* Title con nombre */}
          <div className="w-full text-center">
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mb-1">
              Bienvenido de nuevo
            </h1>
            <p className="text-sm text-gray-500 mb-5">Ingresa tus credenciales para acceder a la plataforma</p>
            <div className="w-full h-px bg-gradient-to-r from-transparent via-purple-200 to-transparent"></div>
          </div>

          {/* Success Message */}
          {successMessage && !error && (
            <div className="w-full bg-green-50 border-l-4 border-green-500 text-green-700 text-sm px-4 py-3 rounded-r-lg flex items-center gap-2">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              {successMessage}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="w-full bg-red-50 border-l-4 border-red-500 text-red-700 text-sm px-4 py-3 rounded-r-lg flex items-center gap-2">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              {error}
            </div>
          )}

          {/* Form */}
          <div className="w-full flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700 ml-1">Correo electrónico</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="bg-slate-50 border border-slate-200 text-gray-900 rounded-xl pl-10 pr-4 py-3.5 text-sm outline-none w-full focus:bg-white focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all font-medium placeholder-gray-400"
                  placeholder="admin@ioteur.com"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700 ml-1">Contraseña</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="bg-slate-50 border border-slate-200 text-gray-900 rounded-xl pl-10 pr-4 py-3.5 text-sm outline-none w-full focus:bg-white focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all font-medium placeholder-gray-400"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          {/* Button */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="bg-purple-600 rounded-xl py-3.5 w-full text-sm font-semibold text-white mt-2 hover:bg-purple-700 shadow-md shadow-purple-600/20 disabled:opacity-70 disabled:shadow-none transition-all flex justify-center items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Ingresando...
              </>
            ) : "Iniciar sesión"}
          </button>

          {/* Links */}
          <div className="flex flex-col items-center gap-2 text-gray-500 text-sm mt-2">
            {/* <a href="#" className="hover:text-purple-600 transition-colors">¿Olvidaste tu contraseña?</a> */}
            <span>
              ¿No tienes una cuenta?{" "}
              <Link to="/register" className="font-semibold text-purple-600 hover:text-purple-800 transition-colors">Regístrate</Link>
            </span>
          </div>

        </div>
      </div>
    </main>
  );
}

export default Login;