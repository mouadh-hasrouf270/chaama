import { useState } from "react";
import { Check, Eye, EyeOff } from "lucide-react";

import { Field, GoldButton } from "../../../components/layout/AccessLayout";

type ActivateFormProps = {
  onSubmit?: () => void;
};

export default function ActivateAccountForm({ onSubmit }: ActivateFormProps) {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const ready = password.length >= 8 && password === confirmation;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!ready) return;

    onSubmit?.();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-5">
        <div className="relative">
          <Field
            label="Mot de passe"
            type={showPassword ? "text" : "password"}
            placeholder="Votre mot de passe"
            value={password}
            onChange={setPassword}
          />

          <button
            type="button"
            aria-label={
              showPassword
                ? "Masquer le mot de passe"
                : "Afficher le mot de passe"
            }
            onClick={() => setShowPassword((prev) => !prev)}
            className="absolute right-5 top-[38px] text-chaama-muted transition hover:text-chaama-gold"
          >
            {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        <Field
          label="Confirmer le mot de passe"
          type={showPassword ? "text" : "password"}
          placeholder="Confirmez votre mot de passe"
          value={confirmation}
          onChange={setConfirmation}
        />
      </div>

      <div className="mt-5 flex items-center gap-2 text-[11px] text-chaama-muted">
        <span
          className={`flex h-4 w-4 items-center justify-center rounded-full ${
            password.length >= 8
              ? "bg-chaama-gold text-white"
              : "bg-chaama-border"
          }`}
        >
          {password.length >= 8 && <Check size={11} />}
        </span>
        8 caractères minimum
      </div>

      <GoldButton type="submit" disabled={!ready}>
        Activer mon compte
      </GoldButton>
    </form>
  );
}
