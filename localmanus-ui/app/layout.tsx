import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LocalManus - 全能型 AI Agent 平台",
  description: "多模态、工具增强的通用 Agent 平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  );
}
