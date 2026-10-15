import { useEffect } from "react";
import useApi from "../../hooks/useApi";

export default function useLiveAppointments(url: string) {
  const result = useApi(url);
  const { reload } = result;
  useEffect(() => {
    const refresh = () => { if (!document.hidden) reload(); };
    const timer = window.setInterval(refresh, 30000);
    window.addEventListener("focus", refresh);
    window.addEventListener("appointments-changed", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("appointments-changed", refresh);
    };
  }, [reload]);
  return result;
}
