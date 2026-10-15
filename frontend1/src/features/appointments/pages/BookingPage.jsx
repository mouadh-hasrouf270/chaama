import { useMemo, useRef, useState } from "react";
import useApi from "../../../hooks/useApi";
import { submitBooking, submitBookingRequest } from "../../../api/appointments.api";
import { errorMessage } from "../../../api/client";
import BookingStepper from "../components/BookingStepper";
import StepNeed from "../components/StepNeed";
import StepSchedule from "../components/StepSchedule";
import StepContact from "../components/StepContact";
import useBookingForm from "../../../hooks/useBookingForm";

export default function BookingPage() {
  const [sent, setSent] = useState(false);
  const [pendingRequest, setPendingRequest] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submitting = useRef(false);
  const { step, data, update, nextStep, previousStep, goToStep, reset } =
    useBookingForm();
  const areas = useApi("/v1/public/practice-areas/", true);
  const areaOptions = Array.isArray(areas.data) ? areas.data : (areas.data?.results || []);
  const area = areaOptions.find(item => item.name === data.expertise);
  
  const availability = useApi(data.date && area ? `/v1/appointments/availability/?date=${data.date}&specialty=${encodeURIComponent(area.slug)}` : null);
  const slots = Array.isArray(availability.data) ? availability.data : (availability.data?.results || []);
  // A failed availability lookup must not block a request for manual confirmation.
  const noConfirmedSlots = Boolean(data.date && (availability.error || (!availability.loading && slots.length === 0)));
  // Keep the full slot identity: two lawyers may offer the same clock time.
  const timeZone = slots[0]?.timezone || "Africa/Algiers";
  const slotOptions = useMemo(() => slots.map(slot => ({
    value: `${slot.lawyer}|${slot.start_at}`,
    label: `${new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone }).format(new Date(slot.start_at))} — Avocat #${slot.lawyer}`,
  })), [availability.data, timeZone]);
  const handleSubmit = async () => {
    if (submitting.current) return;
    const slot = slots.find(item => `${item.lawyer}|${item.start_at}` === data.time);
    if (!area || (!slot && !/^([01]\d|2[0-3]):[0-5]\d$/.test(data.time))) { setError("Sélectionnez une expertise et un horaire valide."); return; }
    if (!data.consent || data.description.trim().length < 10) { setError("Acceptez le traitement des données et décrivez votre situation (10 caractères minimum)."); return; }
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      const contactData = {
        practice_area: area.id,
        consultation_type: { cabinet: "OFFICE", visio: "VIDEO", telephone: "PHONE" }[data.method],
        full_name: data.name, email: data.email, phone: data.phone,
        legal_topic: `${data.consultationType} — ${data.subject}`,
        description: data.description, opposing_party: data.opposingParty, consent: data.consent,
      };
      if (slot) {
        const result = await submitBooking({ ...slot, ...contactData });
        setReceipt(result?.appointment_reference ? `RDV-${result.appointment_reference}` : null);
        setPendingRequest(false);
      } else {
        const result = await submitBookingRequest({ ...contactData, requested_date: data.date, preferred_time: data.time });
        setReceipt(result?.appointment_reference ? `RDV-${result.appointment_reference}` : (result?.request_reference ? `DEM-${result.request_reference}` : null));
        setPendingRequest(Boolean(result?.assignment_pending));
      }
      setSent(true);
    } catch (failure) {
      setError(`Votre demande n’a pas été enregistrée. ${errorMessage(failure)} (Vérifiez que Django fonctionne et que les migrations sont appliquées.)`);
      if (failure.response?.status === 409) { availability.reload(); update("time", ""); previousStep(); }
    } finally { setBusy(false); submitting.current = false; }
  };
  const handleNewBooking = () => {
    reset();
    setSent(false);
    setPendingRequest(false);
    setReceipt(null);
    setError("");
    if (data.date) availability.reload();
  };
  return (
    <div className="min-h-screen bg-[#f7f6f2] text-[#1b3a42] pt-20">
      {" "}
      <main id="top">
        {" "}
        <section
          id="booking"
          className="min-h-[560px] px-5 py-[50px] md:px-6 md:py-[72px]"
        >
          {" "}
          <div className="mx-auto w-full max-w-[720px]">
            {" "}
            {sent ? (
              /* SUCCESS */ <div className="border border-[#dfe2dc] bg-[#eef3ef] p-6 md:p-[54px_42px]">
                {" "}
                <span className="mb-[18px] block text-[8px] font-semibold uppercase tracking-[0.22em] text-[#bd914c]">
                  {" "}
                  Demande envoyée{" "}
                </span>{" "}
                <h2 className="mb-[18px] font-['Playfair_Display'] text-[36px] font-medium leading-[0.95] tracking-[-0.045em] text-[#173a43] md:text-[44px]">
                  {" "}
                  Merci pour votre confiance.{" "}
                </h2>{" "}
                <p className="mb-7 max-w-[390px] text-[13px] leading-[1.7] text-[#688187]">
                  {" "}
                  {pendingRequest ? "Votre demande de créneau a été enregistrée. Un rendez-vous est enregistré dans le calendrier Chaama, en attente d’attribution d’un avocat. Notre équipe vous contactera pour confirmation." : "Votre demande a bien été prise en compte. Notre équipe vous recontactera rapidement pour confirmer votre rendez-vous."} Si vous êtes nouveau client, un compte Chaama a été préparé avec vos informations. Son accès nécessitera une vérification sécurisée.{" "}
                </p>{" "}
                {receipt && <p className="mb-5 font-semibold text-[#173a43]">Référence : {receipt} — {pendingRequest ? "En attente de confirmation" : "Rendez-vous enregistré"}</p>}
                <button
                  type="button"
                  onClick={handleNewBooking}
                  className="inline-flex items-center gap-2 bg-[#8e9da0] px-[15px] py-3 text-[11px] font-semibold text-white transition-all hover:bg-[#1b3a42]"
                >
                  {" "}
                  Nouvelle demande{" "}
                </button>{" "}
              </div>
            ) : (
              <>
                {" "}
                {/* STEPPER */} <BookingStepper currentStep={step} onStepChange={goToStep} /> {/* STEP 1 */}{" "}
                {(areas.loading || (data.date && availability.loading)) && <p role="status">Chargement…</p>}
                {(error || areas.error) && <p role="alert" className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error || areas.error}</p>}
                {availability.error && step === 2 && <p role="status" className="mb-4 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Calendrier indisponible pour le moment. Vous pouvez quand même proposer une date et une heure ; le cabinet confirmera votre demande.</p>}
                {!areas.loading && !areas.error && !areaOptions.length && <p role="alert">Les domaines juridiques ne sont pas encore configurés. Contactez le cabinet.</p>}
                {step === 2 && data.date && !availability.loading && !availability.error && <p>
                  {slotOptions.length ? `${slotOptions.length} créneau(x) disponible(s) — heure locale (${timeZone}).` : "Choisissez une date et une heure souhaitées : le cabinet vous recontactera pour confirmer le rendez-vous."}
                </p>}
                {step === 1 && (
                  <StepNeed
                    consultation={data.consultationType}
                    domain={data.expertise}
                    domainOptions={areaOptions.map(item => item.name)}
                    onConsultationChange={value => update("consultationType", value)}
                    onDomainChange={value => { update("expertise", value); update("time", ""); }}
                    onNext={nextStep}
                  />
                )}{" "}
                {/* STEP 2 */}{" "}
                {step === 2 && (
                  <StepSchedule
                    date={data.date}
                    time={data.time}
                    mode={data.method}
                    availableTimes={slotOptions}
                    noSlots={noConfirmedSlots}
                    onDateChange={value => { update("date", value); update("time", ""); }}
                    onTimeChange={value => update("time", value)}
                    onModeChange={value => update("method", value)}
                    onBack={previousStep}
                    onNext={nextStep}
                  />
                )}{" "}
                {/* STEP 3 */}{" "}
                {step === 3 && (
                  <StepContact
                    name={data.name}
                    email={data.email}
                    phone={data.phone}
                    subject={data.subject}
                    details={data.description}
                    opposingParty={data.opposingParty}
                    consent={data.consent}
                    onChange={(field, value) => update(field === "details" ? "description" : field, value)}
                    onBack={previousStep}
                    onSubmit={handleSubmit}
                    busy={busy}
                  />
                )}{" "}
              </>
            )}{" "}
          </div>{" "}
        </section>{" "}
      </main>{" "}
    </div>
  );
}
