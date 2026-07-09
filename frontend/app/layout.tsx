import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap", weight: ["400", "500", "600"] });
const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["500", "600", "700"]
});

export const metadata = {
  title: "Multi-Agent Automation Assistant",
  description: "An agentic co-pilot that plans and executes multi-step workflows across your tools"
};

const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("maa-theme");
    var theme = stored === "light" || stored === "dark" ? stored : "dark";
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();
`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      data-theme="dark"
      suppressHydrationWarning
      className={`${inter.variable} ${display.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body suppressHydrationWarning>
        {/* Fixed ambient background: drifting aurora mesh + dithered grain, painted behind all glass. */}
        <div className="app-bg" aria-hidden>
          <div className="aurora">
            <span className="aurora-blob aurora-blob--1" />
            <span className="aurora-blob aurora-blob--2" />
            <span className="aurora-blob aurora-blob--3" />
            <span className="aurora-blob aurora-blob--4" />
          </div>
          <div className="grain" />
        </div>
        {children}
      </body>
    </html>
  );
}
