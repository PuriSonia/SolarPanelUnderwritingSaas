"use client";

export default function TrendArrow({ value }: { value: number }) {
  const positive = value < 0; // emissions down is good
  return (
    <span style={{ color: positive ? "green" : "red", fontWeight: 600 }}>
      {positive ? "▲" : "▼"} {value}
    </span>
  );
}
