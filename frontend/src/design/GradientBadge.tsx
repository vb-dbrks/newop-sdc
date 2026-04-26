import { useEffect, useRef } from "react";

interface Props {
  size?: number;
  className?: string;
}

/** Animated purple-to-pink gradient circular badge from the Figma hero. */
export default function GradientBadge({ size = 200, className }: Props) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    let raf = 0;
    let t = 0;
    const draw = () => {
      ctx.clearRect(0, 0, size, size);
      const cx = size / 2;
      const cy = size / 2;
      const r = size / 2;

      const drift = Math.sin(t / 60) * 12;
      const g = ctx.createRadialGradient(cx + drift, cy + drift, 8, cx, cy, r);
      g.addColorStop(0, "#1a0510");
      g.addColorStop(0.4, "#5e1340");
      g.addColorStop(0.8, "#a51d70");
      g.addColorStop(1, "#f7c5d9");

      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();

      t += 1;
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [size]);

  return (
    <canvas
      ref={ref}
      style={{ width: size, height: size }}
      className={className}
      aria-hidden="true"
    />
  );
}
