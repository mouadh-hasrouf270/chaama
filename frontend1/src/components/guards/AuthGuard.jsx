import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import useApi from "../../hooks/useApi";
import { getAccessToken } from "../../api/client";

export default function AuthGuard({ children }) {
  const location = useLocation();
  const [token, setToken] = useState(getAccessToken);
  const { data: user, loading, error } = useApi(token ? "/accounts/me/" : null);
  useEffect(() => {
    const update = () => setToken(getAccessToken());
    window.addEventListener("chaama-session", update);
    return () => window.removeEventListener("chaama-session", update);
  }, []);
  if (!token) return <Navigate to="/auth/login" replace state={{ from: location.pathname }} />;
  if (loading) return <p role="status">Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;
  if (!user) return null;
  if (!["SUPER_ADMIN", "INTERNAL_ASSOCIATE", "EXTERNAL_SUBCONTRACTOR"].includes(user.role))
    return <Navigate to="/rendez-vous" replace />;
  return children;
}
