import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/auth";

function Register() {
  const navigate = useNavigate();
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState(null);
  const [loading, setLoading]   = useState(false);

  const handleRegister = async () => {
    if (!name || !email || !password) {
      setError("Por favor completa todos los campos.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ name, email, password });
      // Después de registrar, lo enviamos al login con un parámetro opcional de éxito
      navigate("/", { state: { message: "Registro exitoso. Ahora puedes iniciar sesión." } });
    } catch (err) {
      setError(err.message || "Error al registrarse. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleRegister();
  };

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col">
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <span className="font-bold text-xl text-purple-700 tracking-tight flex items-center gap-2">
          <svg width="24" height="24" viewBox="0 0 80 80" fill="none">
            <polyline points="10,62 22,50 30,56 40,44 50,50 62,36 72,40" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Ioteur
        </span>
        <span className="text-gray-400 text-sm">Create Account</span>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="bg-white shadow-xl rounded-3xl p-10 w-full max-w-[480px] flex flex-col items-center gap-6 border border-purple-100">

          <div className="w-full text-center">
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mb-1">
              Crear una cuenta
            </h1>
            <p className="text-sm text-gray-500 mb-5">Únete para empezar a monitorear tus dispositivos</p>
            <div className="w-full h-px bg-gradient-to-r from-transparent via-purple-200 to-transparent"></div>
          </div>

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

          <div className="w-full flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700 ml-1">Nombre completo</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="bg-slate-50 border border-slate-200 text-gray-900 rounded-xl pl-10 pr-4 py-3.5 text-sm outline-none w-full focus:bg-white focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all font-medium placeholder-gray-400"
                  placeholder="Tu nombre"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700 ml-1">Correo electrónico</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
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
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
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

          <button
            type="button"
            onClick={handleRegister}
            disabled={loading}
            className="bg-purple-600 rounded-xl py-3.5 w-full text-sm font-semibold text-white mt-2 hover:bg-purple-700 shadow-md shadow-purple-600/20 disabled:opacity-70 disabled:shadow-none transition-all flex justify-center items-center gap-2"
          >
            {loading ? "Registrando..." : "Registrarse"}
          </button>

          <div className="flex flex-col items-center gap-2 text-gray-500 text-sm mt-2">
            <span>
              ¿Ya tienes una cuenta?{" "}
              <Link to="/" className="font-semibold text-purple-600 hover:text-purple-800 transition-colors">Inicia sesión</Link>
            </span>
          </div>

        </div>
      </div>
    </main>
  );
}

export default Register;