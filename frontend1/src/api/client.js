import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
const api = axios.create({ baseURL, timeout: 20000 });
const tokenClient = axios.create({ baseURL, timeout: 20000 });
export const getAccessToken = () => sessionStorage.getItem("chaama_access");
export function clearSession() {
  sessionStorage.removeItem("chaama_access");
  sessionStorage.removeItem("chaama_refresh");
  window.dispatchEvent(new Event("chaama-session"));
}
export function storeTokens(tokens) {
  sessionStorage.setItem("chaama_access", tokens.access);
  if (tokens.refresh) sessionStorage.setItem("chaama_refresh", tokens.refresh);
}
api.interceptors.request.use((config) => {
  const isPublic = config.url?.includes("/public/") || config.url?.includes("/availability/");
  if (!isPublic && getAccessToken()) config.headers.Authorization = `Bearer ${getAccessToken()}`;
  return config;
});
let refreshPromise;
api.interceptors.response.use((response) => response, async (error) => {
  const config = error.config;
  const refresh = sessionStorage.getItem("chaama_refresh");
  if (error.response?.status === 401 && refresh && !config?._retried && !config?.url?.includes("/token/")) {
    config._retried = true;
    try {
      refreshPromise ||= tokenClient.post("/token/refresh/", { refresh })
        .then(({ data }) => { storeTokens(data); return data.access; })
        .finally(() => { refreshPromise = null; });
      const access = await refreshPromise;
      config.headers.Authorization = `Bearer ${access}`;
      return await api(config);
    } catch (refreshError) {
      if (refreshError.response?.status === 401) clearSession();
      return Promise.reject(refreshError);
    }
  }
  if (error.response?.status === 401 && !config?.url?.includes("/token/")) clearSession();
  return Promise.reject(error);
});
export function errorMessage(error) {
  const data = error?.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  if (data && typeof data === "object") return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(" ") : String(messages)}`).join(" ");
  return "Impossible de joindre le serveur. Veuillez réessayer.";
}
export async function getAll(url, params = {}, signal) {
  const rows = [];
  let page = 1;
  while (true) {
    const { data } = await api.get(url, { params: { ...params, page, page_size: 100 }, signal });
    if (Array.isArray(data)) return data;
    rows.push(...data.results);
    if (!data.next) return rows;
    page += 1;
  }
}
export default api;
