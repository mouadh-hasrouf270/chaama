import { useEffect, useState, useCallback } from "react";
import api, { errorMessage, getAll } from "../api/client";

export default function useApi<T = any>(url: string | null, all = false) {
  const [state, setState] = useState<{ data: T | null; loading: boolean; error: string }>({
    data: null, loading: Boolean(url), error: "",
  });
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion(v => v + 1), []);
  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    setState({ data: null, loading: true, error: "" });
    const promise = all ? getAll(url, {}, controller.signal) :
      api.get(url, { signal: controller.signal }).then(response => response.data);
    promise.then(data => {
      if (!controller.signal.aborted) setState({ data, loading: false, error: "" });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ data: null, loading: false, error: errorMessage(error) });
    });
    return () => controller.abort();
  }, [url, all, version]);
  return { ...state, reload };
}

