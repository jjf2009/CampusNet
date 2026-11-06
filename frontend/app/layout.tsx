import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CampusNet · Network Operations",
  description: "Campus network authentication operations console (local prototype)",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
