import { ChangeEvent, FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";

type RegisterForm = {
  name: string;
  email: string;
  password: string;
};

export const RegisterPage = () => {
  const { register } = useAuthContext();
  const [form, setForm] = useState<RegisterForm>({
    name: "",
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const updateField = <K extends keyof RegisterForm>(key: K, value: RegisterForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(form);
      navigate("/dashboard");
    } catch (err) {
      setError("Registration failed. Try a different email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-slate-900">Create your firm workspace</h1>
        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
          <div>
            <label htmlFor="register-name" className="text-sm font-medium text-slate-600">
              Firm Name
            </label>
            <input
              id="register-name"
              placeholder="Apex Tax Partners"
              required
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              value={form.name}
              onChange={(event: ChangeEvent<HTMLInputElement>) => updateField("name", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="register-email" className="text-sm font-medium text-slate-600">
              Email
            </label>
            <input
              id="register-email"
              placeholder="ca@example.com"
              required
              type="email"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              value={form.email}
              onChange={(event: ChangeEvent<HTMLInputElement>) => updateField("email", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="register-password" className="text-sm font-medium text-slate-600">
              Password
            </label>
            <input
              id="register-password"
              placeholder="At least 8 characters"
              minLength={8}
              required
              type="password"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              value={form.password}
              onChange={(event: ChangeEvent<HTMLInputElement>) => updateField("password", event.target.value)}
            />
          </div>
          {error && <p className="text-sm text-rose-500">{error}</p>}
          <button type="submit" className="rounded-lg bg-primary px-4 py-2 font-semibold text-white" disabled={loading}>
            {loading ? "Creating workspace..." : "Create workspace"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Already onboard? <Link to="/login" className="text-primary">Sign in</Link>
        </p>
      </div>
    </div>
  );
};
