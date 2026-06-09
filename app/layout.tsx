import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartCredit - Get My Money Back",
  description:
    "Hosted SmartCredit funds-finder demo for unclaimed-property review and claim guidance.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
