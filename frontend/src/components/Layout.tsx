import { IconFlask } from '@tabler/icons-react';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-linear-dark-bg text-linear-dark-text">
      {/* Header with subtle border */}
      <header className="border-b border-linear-dark-border bg-linear-dark-surface/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-linear bg-white/5 border border-white/10">
              <IconFlask size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">Research Paper Analyzer</h1>
              <p className="text-xs text-linear-dark-muted">
                AI-powered paper analysis and discovery
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
}
