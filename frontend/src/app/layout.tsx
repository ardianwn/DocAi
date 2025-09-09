import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocAI - Document AI Processing Platform",
  description: "Upload documents and interact with them through AI-powered chat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
