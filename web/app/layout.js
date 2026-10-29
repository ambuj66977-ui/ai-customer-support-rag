import "./globals.css";

export const metadata = {
  title: "Northstar Shop | Shopping Help & Customer Support",
  description: "Northstar Shop is an online store for everyday products and accessories. Get help with orders, delivery, returns, refunds, payments, and your account.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
