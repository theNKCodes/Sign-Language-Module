"use client"
import { SignLanguageTranslator } from "@/components/sign-language-translator"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"

export default function Home() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="sign-language-theme">
      <div className="min-h-screen bg-background">
        <header className="container mx-auto py-6 px-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold tracking-tight">Sign Language Translator</h1>
          <ModeToggle />
        </header>
        <main className="container mx-auto px-4 py-6">
          <SignLanguageTranslator />
        </main>
        <footer className="container mx-auto py-6 px-4 text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} Sign Language Translation App
        </footer>
      </div>
    </ThemeProvider>
  )
}

