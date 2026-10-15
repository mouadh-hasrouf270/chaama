import api from "./client";
export const readNotification = (id) => api.post(`/v1/notifications/${id}/read/`).then(r => r.data);
export const readAllNotifications = () => api.post("/v1/notifications/read-all/").then(r => r.data);
