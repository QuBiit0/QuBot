import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Qubot - AI Agent Mission Control",
  description: "Multi-agent AI platform with visual coworking interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
