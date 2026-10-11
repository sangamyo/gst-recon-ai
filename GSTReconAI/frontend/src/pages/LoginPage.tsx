import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";

export const LoginPage = () => {
  const { login } = useAuthContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-slate-900">GSTRecon AI Login</h1>
        <p className="text-sm text-slate-500">Securely reconcile lakhs of invoices in the cloud.</p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="login-email" className="text-sm font-medium text-slate-600">
              Email
            </label>
            <input
              id="login-email"
              placeholder="ca@example.com"
              required
              type="email"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-primary focus:outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="login-password" className="text-sm font-medium text-slate-600">
              Password
            </label>
            <input
              id="login-password"
              required
              type="password"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-primary focus:outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-rose-500">{error}</p>}
          <button
            type="submit"
            className="w-full rounded-lg bg-primary px-4 py-2 font-semibold text-white hover:bg-blue-600"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Need an account? <Link to="/register" className="text-primary">Register</Link>
        </p>
      </div>
    </div>
  );
};
