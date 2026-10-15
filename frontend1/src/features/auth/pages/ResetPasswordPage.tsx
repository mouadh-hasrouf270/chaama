import { AccessLayout } from "../../../components/layout/AccessLayout";
import ResetPasswordForm from "../components/ResetPasswordForm";

type ResetPasswordPageProps = {
  onLogin: () => void;
};

export default function ResetPasswordPage({ onLogin }: ResetPasswordPageProps) {
  return (
    <AccessLayout
      eyebrow="Un nouveau départ"
      title={
        <>
          Retrouvez votre
          <br />
          accès, en toute
          <br />
          <span className="text-chaama-gold">confidentialité.</span>
        </>
      }
      description="Définissez un nouveau mot de passe pour sécuriser à nouveau votre espace professionnel."
      onBack={onLogin}
    >
      <ResetPasswordForm onLogin={onLogin} />
    </AccessLayout>
  );
}
