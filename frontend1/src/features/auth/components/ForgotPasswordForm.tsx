import { useState } from "react";
import { MailCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Field, GoldButton } from "../../../components/layout/AccessLayout";

export default function ForgotPasswordForm() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const valid = email.includes("@");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!valid) return;

    setSent(true);
  };

  if (sent) {
    return (
      <div className="border border-chaama-border bg-chaama-green p-8 text-center">
        <MailCheck
          className="mx-auto text-chaama-gold"
          size={34}
          strokeWidth={1.4}
        />

        <h2 className="mt-5 font-display text-[32px] text-chaama-text">
          Vérifiez votre boîte mail
        </h2>

        <p className="mt-3 text-[14px] leading-6 text-chaama-muted">
          Si un compte correspond à cette adresse, un lien de réinitialisation
          vient d'être envoyé.
        </p>

        <button
          type="button"
          onClick={() => navigate("/auth/reset-password")}
          className="mt-6 cursor-pointer text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
        >
          Ouvrir la réinitialisation
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-9">
      <Field
        label="Email professionnel"
        type="email"
        placeholder="vous@cabinet.fr"
        value={email}
        onChange={setEmail}
      />

      <GoldButton type="submit" disabled={!valid}>
        Envoyer le lien
      </GoldButton>
    </form>
  );
}
