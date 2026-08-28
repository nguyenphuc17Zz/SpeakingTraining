"use client";

import React, { useEffect, useRef, useState } from "react";
import { useTheme } from "@/components/theme-provider";

export type WeatherMode = "auto" | "sakura" | "rain" | "thunder" | "snow" | "momiji" | "hotaru" | "off";

export interface WeatherEngineProps {
  mode?: WeatherMode;
  density?: "low" | "medium" | "high";
  className?: string;
}

export function AtmosphericWeatherEngine({
  mode: propMode,
  density = "medium",
  className,
}: WeatherEngineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { theme } = useTheme();
  const [activeMode, setActiveMode] = useState<WeatherMode>("auto");
  const [mounted, setMounted] = useState(false);

  // Load saved preference from localStorage
  useEffect(() => {
    setMounted(true);
    if (typeof window === "undefined") return;
    if (propMode) {
      setActiveMode(propMode);
    } else {
      const saved = localStorage.getItem("hanasu-weather-fx") as WeatherMode | null;
      setActiveMode(saved || "auto");
    }

    const handleStorage = () => {
      const saved = localStorage.getItem("hanasu-weather-fx") as WeatherMode | null;
      if (saved) setActiveMode(saved);
    };

    window.addEventListener("weather-change", handleStorage);
    window.addEventListener("storage", handleStorage);
    return () => {
      window.removeEventListener("weather-change", handleStorage);
      window.removeEventListener("storage", handleStorage);
    };
  }, [propMode]);

  // Determine effective weather type
  const effectiveWeather: Exclude<WeatherMode, "auto"> = (() => {
    if (activeMode !== "auto") return activeMode;
    // Auto map from Japanese themes
    switch (theme) {
      case "haru":
        return "sakura";
      case "matcha":
        return "hotaru";
      case "aizome":
        return "snow";
      case "kohaku":
        return "rain";
      default:
        return "hotaru";
    }
  })();

  useEffect(() => {
    if (effectiveWeather === "off" || typeof window === "undefined") return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // Density multiplier
    const countMultiplier = density === "low" ? 0.5 : density === "high" ? 1.5 : 1.0;

    // Particle Classes & States
    interface Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      rotation: number;
      rotationSpeed: number;
      opacity: number;
      color: string;
      phase?: number;
    }

    const particles: Particle[] = [];

    // Initialize particles based on weather
    if (effectiveWeather === "sakura") {
      const total = Math.floor(28 * countMultiplier);
      for (let i = 0; i < total; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 8 + 6,
          speedX: Math.random() * 1.5 + 0.8,
          speedY: Math.random() * 1.2 + 0.8,
          rotation: Math.random() * Math.PI * 2,
          rotationSpeed: (Math.random() - 0.5) * 0.03,
          opacity: Math.random() * 0.4 + 0.35,
          color: Math.random() > 0.3 ? "#f472b6" : "#fb7185", // Sakura pink shades
          phase: Math.random() * Math.PI * 2,
        });
      }
    } else if (effectiveWeather === "rain" || effectiveWeather === "thunder") {
      const total = Math.floor((effectiveWeather === "thunder" ? 75 : 45) * countMultiplier);
      for (let i = 0; i < total; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 14 + 10,
          speedX: -1.8,
          speedY: Math.random() * 7 + 9,
          rotation: 0,
          rotationSpeed: 0,
          opacity: Math.random() * 0.25 + 0.15,
          color: "#93c5fd",
        });
      }
    } else if (effectiveWeather === "snow") {
      const total = Math.floor(40 * countMultiplier);
      for (let i = 0; i < total; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 3.5 + 2,
          speedX: Math.random() * 0.8 - 0.4,
          speedY: Math.random() * 1.2 + 0.6,
          rotation: 0,
          rotationSpeed: 0,
          opacity: Math.random() * 0.5 + 0.25,
          color: "#f8fafc",
          phase: Math.random() * Math.PI * 2,
        });
      }
    } else if (effectiveWeather === "momiji") {
      const total = Math.floor(22 * countMultiplier);
      const momijiColors = ["#e11d48", "#ea580c", "#d97706", "#dc2626"];
      for (let i = 0; i < total; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 9 + 8,
          speedX: Math.random() * 1.8 + 0.6,
          speedY: Math.random() * 1.5 + 0.9,
          rotation: Math.random() * Math.PI * 2,
          rotationSpeed: (Math.random() - 0.5) * 0.04,
          opacity: Math.random() * 0.45 + 0.35,
          color: momijiColors[Math.floor(Math.random() * momijiColors.length)],
          phase: Math.random() * Math.PI * 2,
        });
      }
    } else if (effectiveWeather === "hotaru") {
      const total = Math.floor(24 * countMultiplier);
      for (let i = 0; i < total; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 4 + 3,
          speedX: (Math.random() - 0.5) * 0.7,
          speedY: (Math.random() - 0.5) * 0.7,
          rotation: 0,
          rotationSpeed: 0,
          opacity: Math.random() * 0.6 + 0.2,
          color: "#a3e635", // Lime gold glow
          phase: Math.random() * Math.PI * 2,
        });
      }
    }

    // Lightning Flash State (for Thunder mode)
    let lightningOpacity = 0;
    let nextLightningTime = Date.now() + Math.random() * 6000 + 4000;

    // Render loop
    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Thunder lightning flash handling
      if (effectiveWeather === "thunder") {
        const now = Date.now();
        if (now > nextLightningTime) {
          lightningOpacity = 0.22;
          nextLightningTime = now + Math.random() * 7000 + 5000;
        }
        if (lightningOpacity > 0.01) {
          ctx.fillStyle = `rgba(147, 197, 253, ${lightningOpacity})`;
          ctx.fillRect(0, 0, width, height);
          lightningOpacity *= 0.88;
        }
      }

      // Draw each particle
      particles.forEach((p) => {
        if (effectiveWeather === "sakura" || effectiveWeather === "momiji") {
          // Draw falling fluttering leaf/petal
          p.x += p.speedX + Math.sin(p.phase || 0) * 0.8;
          p.y += p.speedY;
          p.rotation += p.rotationSpeed;
          if (p.phase !== undefined) p.phase += 0.02;

          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(p.rotation);
          ctx.fillStyle = p.color;
          ctx.globalAlpha = p.opacity;

          // Draw organic petal / momiji leaf shape
          ctx.beginPath();
          ctx.moveTo(0, -p.size);
          ctx.bezierCurveTo(p.size * 0.8, -p.size * 0.5, p.size * 0.8, p.size * 0.8, 0, p.size);
          ctx.bezierCurveTo(-p.size * 0.8, p.size * 0.8, -p.size * 0.8, -p.size * 0.5, 0, -p.size);
          ctx.fill();
          ctx.restore();
        } else if (effectiveWeather === "rain" || effectiveWeather === "thunder") {
          // Draw rain streak
          p.x += p.speedX;
          p.y += p.speedY;

          ctx.strokeStyle = p.color;
          ctx.globalAlpha = p.opacity;
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x + p.speedX * 2, p.y + p.size);
          ctx.stroke();
        } else if (effectiveWeather === "snow") {
          // Draw snowflake
          p.x += p.speedX + Math.sin(p.phase || 0) * 0.4;
          p.y += p.speedY;
          if (p.phase !== undefined) p.phase += 0.015;

          ctx.fillStyle = p.color;
          ctx.globalAlpha = p.opacity;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fill();
        } else if (effectiveWeather === "hotaru") {
          // Draw floating glowing firefly
          p.x += p.speedX;
          p.y += p.speedY;
          if (p.phase !== undefined) p.phase += 0.03;
          const currentGlow = Math.sin(p.phase || 0) * 0.35 + 0.45;

          // Glow shadow
          ctx.save();
          ctx.shadowBlur = 10;
          ctx.shadowColor = "#bef264";
          ctx.fillStyle = p.color;
          ctx.globalAlpha = Math.max(0.05, currentGlow * p.opacity);
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }

        // Screen wrap-around
        if (p.y > height + 20) {
          p.y = -20;
          p.x = Math.random() * width;
        }
        if (p.x > width + 20) p.x = -20;
        if (p.x < -20) p.x = width + 20;
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
    };
  }, [effectiveWeather, density, theme]);

  if (!mounted || effectiveWeather === "off") return null;

  return (
    <canvas
      ref={canvasRef}
      className={`fixed inset-0 pointer-events-none z-0 ${className || ""}`}
      style={{ opacity: 0.85 }}
    />
  );
}
