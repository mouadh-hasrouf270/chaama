import { AccessLayout } from "../../../components/layout/AccessLayout";
import ActivateAccountForm from "../components/ActivateAccountForm";

type ActivatePageProps = {
  onGoLogin: () => void;
};

export default function ActivateAccountPage({ onGoLogin }: ActivatePageProps) {
  return (
    <AccessLayout
      eyebrow="Votre première connexion"
      title={
        <>
          Activez votre
          <br />
          <span className="text-chaama-gold">espace de travail.</span>
        </>
      }
      description="Choisissez le mot de passe qui protégera vos dossiers, vos échanges et vos outils professionnels."
      onBack={onGoLogin}
    >
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-chaama-gold">
        Activation du compte
      </p>

      <h2 className="font-display text-[38px] leading-tight tracking-[-1.2px] text-chaama-text sm:text-[44px]">
        Activer mon compte
      </h2>

      <p className="mt-3 text-[16px] leading-7 text-chaama-muted">
        Choisissez le mot de passe qui protégera votre espace.
      </p>

      <ActivateAccountForm onSubmit={onGoLogin} />
    </AccessLayout>
  );
}
