import { useState } from "react";
import { X } from "lucide-react";
import InputField from "../../../components/forms/InputField";
import PhoneField from "../../../components/forms/PhoneField";
import TextareaField from "../../../components/forms/TextareaField";
import { createClient } from "../../../api/clients.api";
import { errorMessage } from "../../../api/client";

type ClientFormModalProps = {
  open: boolean;
  onClose: () => void;
  onCreated: (client: any) => void;
};

const emptyForm = {
  first_name: "",
  last_name: "",
  phone: "",
  email: "",
  city: "",
  address: "",
  notes: "",
};

export default function ClientFormModal({ open, onClose, onCreated }: ClientFormModalProps) {
  const [form, setForm] = useState(emptyForm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const set = (field: keyof typeof emptyForm) => (value: string) =>
    setForm((current) => ({ ...current, [field]: value }));

  const canSubmit = Boolean(form.first_name && form.last_name && form.phone);

  const handleClose = () => {
    if (busy) return;
    setForm(emptyForm);
    setError("");
    onClose();
  };

  const handleSubmit = async () => {
    if (!canSubmit || busy) return;
    setBusy(true);
    setError("");
    try {
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone,
        ...(form.email && { email: form.email }),
        ...(form.city && { city: form.city }),
        ...(form.address && { address: form.address }),
        ...(form.notes && { notes: form.notes }),
      };
      const client = await createClient(payload);
      setForm(emptyForm);
      onCreated(client);
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="new-client-title"
      onClick={handleClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto border border-chaama-border bg-white p-5 sm:p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 id="new-client-title" className="font-display text-[20px] text-chaama-text">
            Nouveau client
          </h2>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Fermer"
            className="text-chaama-muted transition-colors hover:text-chaama-dark"
          >
            <X size={18} strokeWidth={1.8} />
          </button>
        </div>

        {error && (
          <p role="alert" className="mb-4 border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-red-700">
            {error}
          </p>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <InputField label="Prénom" value={form.first_name} onChange={set("first_name")} required />
          <InputField label="Nom" value={form.last_name} onChange={set("last_name")} required />
          <PhoneField label="Téléphone" value={form.phone} onChange={set("phone")} required />
          <InputField label="Email" type="email" value={form.email} onChange={set("email")} />
          <InputField label="Ville" value={form.city} onChange={set("city")} />
          <InputField label="Adresse" value={form.address} onChange={set("address")} />
        </div>

        <div className="mt-4">
          <TextareaField label="Notes internes" value={form.notes} onChange={set("notes")} rows={3} />
        </div>

        <div className="mt-6 flex items-center justify-end gap-3 border-t border-chaama-border pt-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={busy}
            className="px-4 py-2.5 text-[13px] font-semibold text-chaama-muted transition-colors hover:text-chaama-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            Annuler
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || busy}
            className="border border-chaama-dark bg-chaama-dark px-4 py-2.5 text-[13px] font-semibold text-white transition hover:bg-chaama-dark2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Création…" : "Créer le client"}
          </button>
        </div>
      </div>
    </div>
  );
}
