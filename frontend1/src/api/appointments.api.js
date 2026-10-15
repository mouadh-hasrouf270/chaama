import api from "./client";
export const submitBooking = (data) => api.post("/v1/public/bookings/", data).then(r => r.data);
export const cancelAppointment = (id) => api.post(`/v1/appointments/${id}/cancel/`).then(r => r.data);
export const uploadEvidence = (intakeId, file) => {
  const data = new FormData();
  data.append("file", file);
  return api.post(`/v1/intakes/${intakeId}/files/`, data).then(r => r.data);
};

export const submitBookingRequest = (data) => api.post("/v1/public/booking-requests/", data).then(r => r.data);
