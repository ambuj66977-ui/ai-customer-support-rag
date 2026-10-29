import "./globals.css";

export const metadata = {
  title: "Northstar · Customer care",
  description: "A grounded AI customer-support RAG demonstration.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
