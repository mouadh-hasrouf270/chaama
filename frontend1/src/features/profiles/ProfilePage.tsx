import { useRef, useState } from "react";
import useApi from "../../hooks/useApi";
import api, { errorMessage } from "../../api/client";
import { Camera } from "lucide-react";
import { PageHeader, Card } from "../../components/ui/InternalUI";

export default function ProfilePage() {
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data: user, loading, error } = useApi("/accounts/me/");
  const lawyer = useApi(user?.lawyer_profile_id ? "/accounts/lawyers/me/" : null);
  const areas = useApi("/v1/public/practice-areas/", true);
  const [specialty, setSpecialty] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const currentSpecialty = (areas.data || []).filter((area: any) => lawyer.data?.practice_areas?.includes(area.id)).map((area: any) => area.name).join(", ");
  const save = async () => {
    const names = (specialty ?? currentSpecialty).split(",").map(s => s.trim()).filter(Boolean);
    const selected = names.map(name => areas.data?.find((area: any) => area.name.toLowerCase() === name.toLowerCase()));
    if (selected.some(item => !item)) { setMessage("Choisissez un domaine existant : " + (areas.data || []).map((area: any) => area.name).join(", ")); return; }
    setBusy(true);
    try {
      await api.patch("/accounts/lawyers/me/", { practice_areas: selected.map(item => item.id) });
      setMessage("Spécialités enregistrées."); lawyer.reload();
    } catch (failure) { setMessage(errorMessage(failure)); }
    finally { setBusy(false); }
  };

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    setProfileImage(imageUrl);
  };

  return (
    <div>
      <PageHeader eyebrow="Mon profil" title="Informations du compte" />

      {loading && <p role="status">Chargement…</p>}
      {(error || lawyer.error || areas.error) && <p role="alert">{error || lawyer.error || areas.error}</p>}
      {message && <p role="status">{message}</p>}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_260px]">
        {/* Informations du compte */}
        <Card className="p-6">
          {/* Photo de profil */}
          <div className="mb-7 flex items-center gap-5 border-b border-chaama-border pb-6">
            <div className="relative">
              <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border border-chaama-border bg-chaama-green">
                {profileImage ? (
                  <img
                    src={profileImage}
                    alt="Photo de profil"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-2xl font-semibold text-chaama-dark">
                    {[user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join("")}
                  </span>
                )}
              </div>

              <button
                type="button"
                disabled
                title="L’envoi de photo de profil n’est pas disponible."
                className="absolute bottom-0 right-0 flex h-8 w-8 items-center justify-center rounded-full border-2 border-chaama-cream bg-chaama-gold text-chaama-dark shadow-sm transition hover:brightness-95 cursor-pointer"
              >
                <Camera size={15} />
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
              />
            </div>

            <div>
              <h3 className="text-[15px] font-semibold text-chaama-dark">
                Photo de profil
              </h3>

              <p className="mt-1 text-[12px] leading-5 text-chaama-muted">
                Ajoutez une photo pour personnaliser votre profil.
              </p>

              <button
                type="button"
                disabled
                title="L’envoi de photo de profil n’est pas disponible."
                className="mt-3 text-[12px] font-semibold text-chaama-gold transition hover:underline cursor-pointer"
              >
                Modifier la photo
              </button>
            </div>
          </div>

          {/* Prénom + Nom */}
          <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
                Prénom
              </label>

              <input
                value={user?.first_name || ""}
                readOnly
                className="h-11 w-full border border-chaama-border bg-chaama-cream px-4 text-[13px] outline-none focus:border-chaama-gold"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
                Nom
              </label>

              <input
                value={user?.last_name || ""}
                readOnly
                className="h-11 w-full border border-chaama-border bg-chaama-cream px-4 text-[13px] outline-none focus:border-chaama-gold"
              />
            </div>
          </div>

          {/* Email */}
          <div className="mb-5">
            <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
              Email
            </label>

            <input
              value={user?.email || ""}
              readOnly
              className="h-11 w-full border border-chaama-border bg-chaama-cream px-4 text-[13px] outline-none focus:border-chaama-gold"
            />
          </div>

          {/* Spécialité */}
          <div className="mb-6">
            <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
              Spécialité
            </label>

            <input
              value={specialty ?? currentSpecialty}
              onChange={event => setSpecialty(event.target.value)}
              className="h-11 w-full border border-chaama-border bg-chaama-cream px-4 text-[13px] outline-none focus:border-chaama-gold"
            />
          </div>

          <button onClick={save} disabled={busy || !lawyer.data || areas.loading || !!areas.error} className="border border-chaama-dark bg-chaama-dark px-5 py-2.5 text-[13px] font-semibold text-white transition hover:bg-chaama-dark-2 cursor-pointer">
            Enregistrer
          </button>
        </Card>

        {/* Changer le mot de passe */}
        <Card className="p-6">
          <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-chaama-muted">
            Changer le mot de passe
          </h3>

          <div className="mb-4">
            <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
              Mot de passe actuel
            </label>

            <input
              type="password"
              className="h-10 w-full border border-chaama-border bg-chaama-cream px-3 text-[13px] outline-none focus:border-chaama-gold"
            />
          </div>

          <div className="mb-5">
            <label className="mb-1.5 block text-[12px] font-medium text-chaama-muted">
              Nouveau mot de passe
            </label>

            <input
              type="password"
              className="h-10 w-full border border-chaama-border bg-chaama-cream px-3 text-[13px] outline-none focus:border-chaama-gold"
            />
          </div>

          <button disabled title="Le changement de mot de passe n’est pas disponible via cette API." className="w-full border border-chaama-dark px-4 py-2 text-[12.5px] font-semibold text-chaama-dark transition hover:bg-chaama-dark hover:text-white cursor-pointer">
            Mettre à jour
          </button>
        </Card>
      </div>
    </div>
  );
}
