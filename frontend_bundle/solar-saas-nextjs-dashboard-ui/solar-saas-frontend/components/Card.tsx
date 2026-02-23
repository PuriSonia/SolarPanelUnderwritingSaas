import React from "react";

export function Card(props: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className="bg-white border border-zinc-200 rounded-xl p-4 shadow-[0_1px_0_rgba(0,0,0,0.03)]">
      <header className="flex items-start justify-between gap-3">
        <h3 className="text-[11px] tracking-[0.14em] uppercase font-semibold text-zinc-600">
          {props.title}
        </h3>
        {props.right}
      </header>
      <div className="mt-3">{props.children}</div>
    </section>
  );
}
