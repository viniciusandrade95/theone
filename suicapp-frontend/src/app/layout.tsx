import "./globals.css";

export const metadata = {
  title: "Beauty CRM",
  description: "Enterprise CRM dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
