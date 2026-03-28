"use client";
import { useEffect, useState } from "react";

interface WebGpuSupport {
  supported: boolean;
  checked: boolean;
}

export function useWebGpuSupport(): WebGpuSupport {
  const [state, setState] = useState<WebGpuSupport>({ supported: false, checked: false });
  useEffect(() => {
    const checkSupport = async (): Promise<void> => {
      if (typeof navigator === "undefined" || !("gpu" in navigator)) {
        setState({ supported: false, checked: true });
        return;
      }
      try {
        const adapter = await navigator.gpu.requestAdapter();
        setState({ supported: adapter !== null, checked: true });
      } catch {
        setState({ supported: false, checked: true });
      }
    };
    void checkSupport();
  }, []);
  return state;
}
