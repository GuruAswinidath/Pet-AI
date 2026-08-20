import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pet AI - Vet Triage Assistant",
  description: "AI-assisted pet symptom triage - text and voice, multilingual.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
