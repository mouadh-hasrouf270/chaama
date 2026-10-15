import { useState } from "react";
import { CheckCircle2, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { AccessLayout } from "../../../components/layout/AccessLayout";
import SignupPartnerForm from "../components/SignupPartnerForm";

export default function SignupPartnerPage() {
  const navigate = useNavigate();
  const [submitted, setSubmitted] = useState(false);

  return (
    <AccessLayout
      eyebrow={submitted ? "Demande envoyée" : "Devenir partenaire"}
      title={
        submitted ? (
          <>
            Votre demande
            <br />
            est <span className="text-chaama-gold">en attente.</span>
          </>
        ) : (
          <>
            Rejoignez le
            <br />
            réseau <span className="text-chaama-gold">CHAAMA.</span>
          </>
        )
      }
      description={
        submitted
          ? "Chama examinera votre justificatif de barreau. Le cabinet vous contactera après examen."
          : "Soumettez votre candidature d'avocat externe. Chama vérifiera votre justificatif de barreau avant activation."
      }
      onBack={() => navigate("/auth/login")}
    >
      {submitted ? (
        <div className="border border-chaama-border bg-chaama-green p-8 text-center">
          <CheckCircle2
            className="mx-auto text-chaama-gold"
            size={36}
            strokeWidth={1.4}
          />

          <h2 className="mt-5 font-display text-[30px] text-chaama-text">
            Demande enregistrée
          </h2>

          <p className="mt-3 text-[14px] leading-6 text-chaama-muted">
            Votre inscription est en attente de vérification. Chama validera
            votre justificatif de barreau, puis vous contactera pour la suite.
          </p>

          <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-chaama-muted">
            <ShieldCheck
              size={14}
              strokeWidth={1.6}
              className="text-chaama-dark"
            />
            Statut : en attente de vérification
          </div>

          <button
            type="button"
            onClick={() => navigate("/auth/login")}
            className="mt-7 cursor-pointer text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
          >
            Retour à la connexion
          </button>
        </div>
      ) : (
        <>
          <SignupPartnerForm onSubmitted={() => setSubmitted(true)} />

          <button
            type="button"
            onClick={() => navigate("/auth/login")}
            className="mt-6 block w-full text-center text-[13px] font-semibold text-chaama-gold transition hover:text-chaama-dark2"
          >
            Retour à la connexion
          </button>
        </>
      )}
    </AccessLayout>
  );
}
