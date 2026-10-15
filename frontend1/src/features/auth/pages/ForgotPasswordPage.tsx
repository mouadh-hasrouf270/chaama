import { useNavigate } from "react-router-dom";

import { AccessLayout } from "../../../components/layout/AccessLayout";
import ForgotPasswordForm from "../components/ForgotPasswordForm";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  return (
    <AccessLayout
      eyebrow="Un accès retrouvé"
      title={
        <>
          Votre espace reste
          <br />
          <span className="text-chaama-gold">à portée de main.</span>
        </>
      }
      description="Un oubli de mot de passe ne doit jamais devenir un obstacle. Nous vous aidons à retrouver votre accès en toute confidentialité."
      onBack={() => navigate("/auth/login")}
    >
      <ForgotPasswordForm />

      <button
        type="button"
        onClick={() => navigate("/auth/login")}
        className="mt-6 block w-full text-center text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
      >
        Retour à la connexion
      </button>
    </AccessLayout>
  );
}
