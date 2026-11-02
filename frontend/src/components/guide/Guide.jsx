// src/components/guide/Guide.jsx
//
// "Scout" -- the little glowing blob (in a graduation cap) who walks
// students through the app. Pure inline SVG + CSS, so it's razor sharp at
// any size and costs no image downloads.
//
// It reacts in three ways:
//   - mood:    swaps the eyes/mouth (idle, happy, excited, curious, wow,
//              thinking, sad, shy) and the body animation
//   - lookAt:  {x, y} viewport point to stare at (e.g. the caret of the
//              field being typed in); without it, the eyes follow the
//              pointer/finger around the screen
//   - message: speech bubble text, announced politely to screen readers
//
// The character itself is decorative (aria-hidden); everything it "says"
// lives in the bubble as real text.

import { useEffect, useRef, useState } from "react";

const MAX_EYE_SHIFT = 6; // SVG units the eyes can travel from center

function useEyeOffset(svgRef, lookAt) {
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const pointer = useRef(null);
  const frame = useRef(0);

  // Eye tracking stays on even with "reduce motion": it's a few pixels of
  // glance, not the large looping movement that setting is meant to stop
  // (those animations are switched off in CSS).
  useEffect(() => {
    function aimAt(target) {
      const svg = svgRef.current;
      if (!svg || !target) {
        setOffset({ x: 0, y: 0 });
        return;
      }
      const rect = svg.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height * 0.56;
      const dx = target.x - cx;
      const dy = target.y - cy;
      const dist = Math.hypot(dx, dy) || 1;
      // Ease toward the max shift over the first ~240px of distance so
      // nearby targets get a subtle glance and far ones a full look.
      const reach = Math.min(dist / 240, 1) * MAX_EYE_SHIFT;
      setOffset({ x: (dx / dist) * reach, y: (dy / dist) * reach * 0.8 });
    }

    if (lookAt) {
      aimAt(lookAt);
      return undefined;
    }

    function onMove(e) {
      pointer.current = { x: e.clientX, y: e.clientY };
      cancelAnimationFrame(frame.current);
      frame.current = requestAnimationFrame(() => aimAt(pointer.current));
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerdown", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerdown", onMove);
      cancelAnimationFrame(frame.current);
    };
  }, [svgRef, lookAt?.x, lookAt?.y]); // eslint-disable-line react-hooks/exhaustive-deps

  return offset;
}

function useBlink(enabled) {
  const [blinking, setBlinking] = useState(false);
  useEffect(() => {
    if (!enabled) return undefined;
    let timer;
    function schedule() {
      timer = setTimeout(() => {
        setBlinking(true);
        timer = setTimeout(() => {
          setBlinking(false);
          schedule();
        }, 140);
      }, 2400 + Math.random() * 3200);
    }
    schedule();
    return () => clearTimeout(timer);
  }, [enabled]);
  return blinking;
}

function Eyes({ mood, blinking }) {
  if (mood === "happy" || mood === "excited") {
    return (
      <g className="guide__eyes-shape" fill="none" stroke="#1d1838" strokeWidth="4.5" strokeLinecap="round">
        <path d="M46 80 Q54 69 62 80" />
        <path d="M78 80 Q86 69 94 80" />
      </g>
    );
  }
  if (mood === "shy") {
    return (
      <g className="guide__eyes-shape" fill="none" stroke="#1d1838" strokeWidth="4.5" strokeLinecap="round">
        <path d="M46 77 Q54 84 62 77" />
        <path d="M78 77 Q86 84 94 77" />
      </g>
    );
  }
  const big = mood === "wow";
  const ry = big ? 11.5 : 10;
  const rx = big ? 8.5 : 7.5;
  return (
    <g className={`guide__eyes-shape ${blinking ? "is-blinking" : ""}`}>
      {[54, 86].map((cx) => (
        <g key={cx} className="guide__eye">
          <ellipse cx={cx} cy="78" rx={rx} ry={ry} fill="#1d1838" />
          <circle cx={cx + 2.6} cy={78 - 4.2} r="2.8" fill="#fff" />
          <circle cx={cx - 2.4} cy={78 + 4} r="1.2" fill="#fff" opacity="0.7" />
        </g>
      ))}
    </g>
  );
}

function Mouth({ mood }) {
  const ink = "#1d1838";
  switch (mood) {
    case "happy":
    case "excited":
      return (
        <g>
          <path d="M57 95 Q70 114 83 95 Z" fill={ink} />
          <ellipse cx="70" cy="104" rx="6" ry="3.4" fill="#ff6fa5" />
        </g>
      );
    case "wow":
      return <ellipse cx="70" cy="101" rx="5.5" ry="7" fill={ink} />;
    case "curious":
      return <ellipse cx="72" cy="100" rx="3.6" ry="4.2" fill={ink} />;
    case "sad":
      return <path d="M61 104 Q70 95 79 104" fill="none" stroke={ink} strokeWidth="4" strokeLinecap="round" />;
    case "thinking":
      return <path d="M62 101 L78 97" fill="none" stroke={ink} strokeWidth="4" strokeLinecap="round" />;
    case "shy":
      return <path d="M64 100 Q70 104 76 100" fill="none" stroke={ink} strokeWidth="3.5" strokeLinecap="round" />;
    default:
      return <path d="M61 97 Q70 106 79 97" fill="none" stroke={ink} strokeWidth="4" strokeLinecap="round" />;
  }
}

function Sparkle({ x, y, size, delay }) {
  const s = size;
  return (
    <path
      className="guide__sparkle"
      style={{ animationDelay: `${delay}s` }}
      d={`M${x} ${y - s} Q${x} ${y} ${x + s} ${y} Q${x} ${y} ${x} ${y + s} Q${x} ${y} ${x - s} ${y} Q${x} ${y} ${x} ${y - s} Z`}
      fill="#ffc53d"
    />
  );
}

export default function Guide({
  mood = "idle",
  message,
  lookAt = null,
  size = 96,
  bubble = "right", // "right" | "below"
  onClick,
  label = "Scout, your ScholarMatch guide",
  className = "",
}) {
  const svgRef = useRef(null);
  const eye = useEyeOffset(svgRef, lookAt);
  const blinking = useBlink(mood !== "happy" && mood !== "excited" && mood !== "shy");

  const character = (
    <span className={`guide__figure guide--${mood}`} style={{ width: size, height: size }}>
      <span className="guide__glow" aria-hidden="true" />
      <svg
        ref={svgRef}
        className="guide__svg"
        viewBox="0 0 140 140"
        width={size}
        height={size}
        aria-hidden="true"
        focusable="false"
      >
        <defs>
          <radialGradient id="guideBody" cx="38%" cy="30%" r="75%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="45%" stopColor="#f4f0ff" />
            <stop offset="80%" stopColor="#d8caff" />
            <stop offset="100%" stopColor="#b59cff" />
          </radialGradient>
          <linearGradient id="guideCap" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#3a2f73" />
            <stop offset="100%" stopColor="#1d1838" />
          </linearGradient>
        </defs>

        <g className="guide__body">
          <path
            d="M70 26 C104 26 122 50 122 82 C122 112 100 130 70 130 C40 130 18 112 18 82 C18 50 36 26 70 26 Z"
            fill="url(#guideBody)"
            stroke="#ffffff"
            strokeWidth="1.5"
          />
          <ellipse cx="50" cy="50" rx="15" ry="8" fill="#fff" opacity="0.85" transform="rotate(-24 50 50)" />

          <ellipse cx="42" cy="94" rx="8" ry="5" fill="#ff6fa5" opacity="0.45" />
          <ellipse cx="98" cy="94" rx="8" ry="5" fill="#ff6fa5" opacity="0.45" />

          <g transform={`translate(${eye.x} ${eye.y})`}>
            <Eyes mood={mood} blinking={blinking} />
          </g>
          <g transform={`translate(${eye.x * 0.4} ${eye.y * 0.3})`}>
            <Mouth mood={mood} />
          </g>

          {/* Mortarboard: the one prop that says "scholarship" at a glance */}
          <g className="guide__cap" transform="translate(70 27) rotate(-9)">
            <path d="M-17 2 L-17 13 Q0 21 17 13 L17 2 Z" fill="#2a2352" />
            <path d="M-34 0 L0 -13 L34 0 L0 13 Z" fill="url(#guideCap)" stroke="#5b4fa8" strokeWidth="1" />
            <g className="guide__tassel">
              <path d="M0 0 L27 3 L28 19" fill="none" stroke="#ffc53d" strokeWidth="2.4" strokeLinecap="round" />
              <rect x="25" y="18" width="6" height="9" rx="2" fill="#ffc53d" />
            </g>
            <circle cx="0" cy="0" r="3" fill="#ffc53d" />
          </g>
        </g>

        {mood === "excited" && (
          <g>
            <Sparkle x={14} y={40} size={7} delay={0} />
            <Sparkle x={126} y={56} size={6} delay={0.35} />
            <Sparkle x={118} y={18} size={4.5} delay={0.7} />
          </g>
        )}
      </svg>
    </span>
  );

  return (
    <div className={`guide guide--bubble-${bubble} ${className}`}>
      {onClick ? (
        <button type="button" className="guide__button" onClick={onClick} aria-label={label}>
          {character}
        </button>
      ) : (
        character
      )}
      {message && (
        <p className="guide__bubble" role="status" aria-live="polite">
          {message}
        </p>
      )}
    </div>
  );
}
