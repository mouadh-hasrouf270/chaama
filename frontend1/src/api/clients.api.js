import api from "./client";
export const createClient = (data) => api.post("/v1/clients/", data).then(r => r.data);
export const updateClient = (id, data) => api.patch(`/v1/clients/${id}/`, data).then(r => r.data);
export const deleteClient = (id) => api.delete(`/v1/clients/${id}/`);
