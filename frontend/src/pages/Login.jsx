import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState(null);

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
    <main className="min-h-screen bg-gray-100 flex flex-col">
      <div className="bg-gray-100 border-b border-gray-200 px-4 py-3">
        <span className="text-gray-500 text-base">Login</span>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-[#d9d9d9] rounded-2xl p-10 w-full max-w-[480px] flex flex-col items-center gap-6">

          {/* Logo */}
          <div className="w-36 h-36 bg-[#d9d9d9] border-2 border-gray-800 rounded-2xl flex items-center justify-center">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <circle cx="40" cy="38" r="4" fill="#1a1a1a"/>
              <path d="M28 29 Q40 17 52 29" fill="none" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round"/>
              <path d="M21 22 Q40 6 59 22" fill="none" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round"/>
              <polyline points="10,62 22,50 30,56 40,44 50,50 62,36 72,40" fill="none" stroke="#1a1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>

          {/* Title con nombre */}
          <div className="w-full text-center">
            <div className="flex items-center justify-center gap-3 mb-1">
              <h1 className="text-3xl font-bold text-white tracking-tight">
                <span className="font-bold">iot</span>
                <span className="font-normal opacity-70">eur</span>
              </h1>
            </div>
            <p className="text-xs text-gray-400 mb-3">IoT monitoring platform</p>
            <hr className="border-gray-400 w-full" />
          </div>

          {/* Error */}
          {error && (
            <div className="w-full bg-red-100 border border-red-300 text-red-700 text-sm px-4 py-2 rounded-xl">
              {error}
            </div>
          )}

          {/* Form */}
          <div className="w-full flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Email or username</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={handleKeyDown}
                className="bg-white rounded-xl px-4 py-3 text-base outline-none border-none w-full"
                placeholder="tu@correo.com"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={handleKeyDown}
                className="bg-white rounded-xl px-4 py-3 text-base outline-none border-none w-full"
                placeholder="••••••••"
              />
            </div>
          </div>

          {/* Button */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="bg-white rounded-xl py-3 w-3/4 text-base font-medium text-gray-800 mt-2 hover:bg-gray-50 disabled:opacity-60 transition-opacity"
          >
            {loading ? "Entrando..." : "Login"}
          </button>

          {/* Links */}
          <div className="flex flex-col items-center gap-2 text-white text-sm">
            <a href="#" className="underline font-semibold">Forgot your password?</a>
            <span>
              Don&apos;t have an account?{" "}
              <a href="#" className="font-semibold underline">Sign up</a>
            </span>
          </div>

        </div>
      </div>
    </main>
  );
}

export default Login;