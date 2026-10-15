import { useState } from "react";
import { Check, Eye, EyeOff } from "lucide-react";
import { Field, GoldButton } from "../../../components/layout/AccessLayout";

type ResetPasswordFormProps = {
  onLogin: () => void;
};

export default function ResetPasswordForm({ onLogin }: ResetPasswordFormProps) {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [visible, setVisible] = useState(false);
  const [done, setDone] = useState(false);

  const ready = password.length >= 8 && password === confirmation;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!ready) return;

    setDone(true);
  };

  if (done) {
    return (
      <div className="border border-chaama-border bg-chaama-green p-8 text-center">
        <Check
          className="mx-auto text-chaama-gold"
          size={34}
          strokeWidth={1.4}
        />

        <h2 className="mt-5 font-display text-[32px] text-chaama-text">
          Mot de passe mis à jour
        </h2>

        <p className="mt-3 text-[14px] leading-6 text-chaama-muted">
          Votre espace est de nouveau sécurisé. Vous pouvez vous connecter dès
          maintenant.
        </p>

        <button
          type="button"
          onClick={onLogin}
          className="mt-6 text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
        >
          Retour à la connexion
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="mt-9 space-y-5">
        <div className="relative">
          <Field
            label="Nouveau mot de passe"
            type={visible ? "text" : "password"}
            placeholder="Votre nouveau mot de passe"
            value={password}
            onChange={setPassword}
          />

          <button
            type="button"
            aria-label={
              visible ? "Masquer le mot de passe" : "Afficher le mot de passe"
            }
            onClick={() => setVisible((prev) => !prev)}
            className="absolute right-5 top-[38px] text-chaama-muted transition hover:text-chaama-gold"
          >
            {visible ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        <Field
          label="Confirmer le mot de passe"
          type={visible ? "text" : "password"}
          placeholder="Confirmez votre mot de passe"
          value={confirmation}
          onChange={setConfirmation}
        />
      </div>

      <div className="mt-5 flex items-center gap-2 text-[11px] text-chaama-muted">
        <span
          className={`flex h-4 w-4 items-center justify-center rounded-full ${
            ready ? "bg-chaama-gold text-white" : "bg-chaama-border"
          }`}
        >
          {ready && <Check size={11} />}
        </span>
        Les deux mots de passe doivent correspondre
      </div>

      <GoldButton type="submit" disabled={!ready}>
        Réinitialiser le mot de passe
      </GoldButton>
    </form>
  );
}
