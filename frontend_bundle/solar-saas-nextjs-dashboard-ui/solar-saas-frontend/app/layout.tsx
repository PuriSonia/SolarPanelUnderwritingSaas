import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Solar SaaS Dashboard",
  description: "Commercial solar performance + ESG reporting"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
