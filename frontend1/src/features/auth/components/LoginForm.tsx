import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { login } from "../../../api/auth.api";
import { errorMessage } from "../../../api/client";
import { ArrowRight } from "lucide-react";

import { Field, GoldButton } from "../../../components/layout/AccessLayout";

type LoginFormProps = {
  onSubmit?: (email: string, password: string) => void;
};

export default function LoginForm({ onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const canSubmit = email.trim().length > 0 && password.length > 0 && !busy;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!canSubmit) return;

    setBusy(true);
    setMessage("");
    try {
      const user = await login(email.trim(), password);
      onSubmit?.(email, password);
      const destination = user.role === "CLIENT" ? "/rendez-vous" : "/app";
      navigate(location.state?.from?.startsWith("/app") && user.role !== "CLIENT" ? location.state.from : destination);
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="mt-9 space-y-5">
        <Field
          label="Nom d’utilisateur"
          type="text"
          placeholder="Votre identifiant"
          value={email}
          onChange={setEmail}
        />

        <Field
          label="Mot de passe"
          type="password"
          placeholder="Votre mot de passe"
          value={password}
          onChange={setPassword}
        />

        <GoldButton type="submit" disabled={!canSubmit}>
          {busy ? "Connexion…" : "Se connecter"}
          <ArrowRight className="ml-2 inline" size={16} strokeWidth={1.8} />
        </GoldButton>
      </form>

      {message && (
        <p className="mt-4 text-center text-[12px] font-medium text-chaama-dark">
          {message}
        </p>
      )}
    </>
  );
}
