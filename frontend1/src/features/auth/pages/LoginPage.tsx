import { useNavigate } from "react-router-dom";

import { AccessLayout } from "../../../components/layout/AccessLayout";
import LoginForm from "../components/LoginForm";

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <AccessLayout
      eyebrow="Le portail du cabinet"
      title={
        <>
          Retrouvez vos dossiers
          <br />
          là où vous les avez
          <br />
          <span className="text-chaama-gold">laissés.</span>
        </>
      }
      description="Un espace confidentiel pensé pour suivre vos missions, vos échéances et vos échanges en toute sérénité."
    >
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-chaama-gold">
        Espace professionnel
      </p>

      <h2 className="font-display text-[38px] leading-tight tracking-[-1.2px] text-chaama-text sm:text-[44px]">
        Connexion
      </h2>

      <p className="mt-3 text-[16px] leading-7 text-chaama-muted">
        Accédez à votre espace de travail.
      </p>

      <LoginForm />

      <button
        type="button"
        onClick={() => navigate("/auth/signup")}
        className="mx-auto mt-4 block cursor-pointer text-[11px] text-chaama-muted transition hover:text-chaama-text"
      >
        Vous êtes avocat externe&nbsp;?{" "}
        <span className="font-semibold text-chaama-gold">
          Devenir partenaire
        </span>
      </button>

      <button
        type="button"
        onClick={() => navigate("/auth/forgot-password")}
        className="mx-auto mt-7 block cursor-pointer text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
      >
        Mot de passe oublié&nbsp;?
      </button>
    </AccessLayout>
  );
}
