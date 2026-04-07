'use client';

import { NetworkVisualization } from '@/components/NetworkVisualization';
import { MetricsPanel } from '@/components/MetricsPanel';
import { ControlPanel } from '@/components/ControlPanel';
import { AlertsPanel } from '@/components/AlertsPanel';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
                <span className="text-xl font-bold">Q</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  QNet
                </h1>
                <p className="text-xs text-gray-500">Quantum Network Simulator</p>
              </div>
            </div>
            
            <nav className="flex items-center gap-6">
              <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Dashboard</a>
              <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Nodes</a>
              <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Security</a>
              <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">API</a>
            </nav>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-6 py-8">
        <ControlPanel />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Network Topology
              </h2>
              <div className="rounded-lg overflow-hidden">
                <NetworkVisualization width={800} height={500} />
              </div>
            </div>
          </div>
          
          <div>
            <AlertsPanel />
          </div>
        </div>
        
        <MetricsPanel />
        
        <footer className="mt-12 pt-6 border-t border-gray-800 text-center text-sm text-gray-500">
          <p>QNet v1.0.0 - Quantum-Decentralized Networking Protocol & Simulator</p>
        </footer>
      </main>
    </div>
  );
}
