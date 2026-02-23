"use client";

import React from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

type Point = { month: string; generation_kwh?: number; grid_kwh?: number };

export function SeriesChart(props: {
  data: Point[];
  dataKey: "generation_kwh" | "grid_kwh";
  label: string;
}) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={props.data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey={props.dataKey} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-2 text-xs text-zinc-500">{props.label}</div>
    </div>
  );
}
