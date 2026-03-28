"use client";

import { OrbitControls, Points } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo, type ReactElement } from "react";
import * as THREE from "three";

import { useWebGpuSupport } from "@/components/hooks/useWebGpuSupport";

const pointPositions = new Float32Array(Array.from({ length: 1200 }, () => (Math.random() - 0.5) * 40));

function PointCloud(): ReactElement {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pointPositions, 3));
    return g;
  }, []);
  return <Points geometry={geometry} />;
}

function webGpuCanvasProps(enabled: boolean): Record<string, unknown> {
  if (!enabled) {
    return {};
  }
  return {
    gl: async (props: Record<string, unknown>) => {
      const webGpu = await import("three/webgpu");
      const renderer = new webGpu.WebGPURenderer(props as ConstructorParameters<typeof webGpu.WebGPURenderer>[0]);
      await renderer.init();
      return renderer;
    }
  };
}

export function LidarViewer(): ReactElement {
  const { supported, checked } = useWebGpuSupport();

  return (
    <section className="rounded-lg border border-white/15 bg-black/35 p-4">
      <h2 className="mb-3 text-sm uppercase tracking-[0.14em] text-white/75 font-mono">3D Point Cloud</h2>
      {checked && !supported ? (
        <p className="mb-2 rounded-md border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
          WebGPU not available in this browser; automatically using WebGL fallback.
        </p>
      ) : null}
      <div className="h-72 w-full overflow-hidden rounded-md border border-white/10 bg-[#090d12]">
        <Canvas camera={{ position: [0, 8, 28], fov: 55 }} {...webGpuCanvasProps(supported)}>
          <color attach="background" args={["#090d12"]} />
          <ambientLight intensity={0.5} />
          <PointCloud />
          <OrbitControls enableDamping dampingFactor={0.08} />
        </Canvas>
      </div>
    </section>
  );
}
