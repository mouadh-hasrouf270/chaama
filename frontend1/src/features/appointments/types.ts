export type BookingStep = 1 | 2 | 3;
export type BookingFormData = {
  consultationType: string;
  expertise: string;
  date: string;
  time: string;
  method: string;
  name: string;
  email: string;
  phone: string;
  subject: string;
  description: string;
  opposingParty: string;
  consent: boolean;
};
export type BookingChange = (
  field: keyof BookingFormData,
  value: string | boolean,
) => void;
export const initialBookingData: BookingFormData = {
  consultationType: "",
  expertise: "",
  date: "",
  time: "",
  method: "",
  name: "",
  email: "",
  phone: "",
  subject: "",
  description: "",
  opposingParty: "",
  consent: false,
};

// export type BookingStep = 1 | 2 | 3;
// export type BookingNeed = { consultation: string; domain: string };
// export type BookingSchedule = { date: string; time: string; mode: string };
// export type BookingContact = {
//   name: string;
//   email: string;
//   phone: string;
//   subject: string;
//   details: string;
//   opposingParty: string;
//   consent: boolean;
// };
// export type ContactField = keyof BookingContact;
// export type BookingFormData = {
//   need: BookingNeed;
//   schedule: BookingSchedule;
//   contact: BookingContact;
// };
// export const initialBookingData: BookingFormData = {
//   need: { consultation: "", domain: "" },
//   schedule: { date: "", time: "", mode: "" },
//   contact: {
//     name: "",
//     email: "",
//     phone: "",
//     subject: "",
//     details: "",
//     opposingParty: "",
//     consent: false,
//   },
// };

// export type BookingChange = (
//   field: keyof BookingFormData,
//   value: string | boolean,
// ) => void;

// export const BOOKING_STEPS = [
//   { id: 1, label: "Votre besoin" },
//   { id: 2, label: "Le rendez-vous" },
//   { id: 3, label: "Vos coordonnées" },
// ] as const;
