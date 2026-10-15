import api, { clearSession, storeTokens } from "./client";
export async function login(username, password) {
  const { data } = await api.post("/token/", { username, password });
  storeTokens(data);
  const response = await api.get("/accounts/me/");
  window.dispatchEvent(new Event("chaama-session"));
  return response.data;
}
export async function logout() {
  try {
    const refresh = sessionStorage.getItem("chaama_refresh");
    if (refresh) await api.post("/accounts/logout/", { refresh });
  } finally {
    clearSession();
  }
}
export const getMe = () => api.get("/accounts/me/").then(({ data }) => data);
