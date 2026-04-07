import { useState } from 'react';
import { Play, Pause, Square, Settings, AlertCircle } from 'lucide-react';
import { useNetworkStore } from '@/lib/store';

export function ControlPanel() {
  const { simulation } = useNetworkStore();
  const [config, setConfig] = useState({
    nodes: 100,
    topology: 'scale_free',
    duration: 60,
  });
  
  const handleStart = async () => {
    const response = await fetch('/api/simulation/start', { method: 'POST' });
    return response.json();
  };
  
  const handleStop = async () => {
    const response = await fetch('/api/simulation/stop', { method: 'POST' });
    return response.json();
  };
  
  return (
    <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-800 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Simulation Control</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            simulation.state === 'running' ? 'bg-green-400 animate-pulse' :
            simulation.state === 'paused' ? 'bg-yellow-400' : 'bg-gray-500'
          }`} />
          <span className="text-sm text-gray-400 capitalize">{simulation.state}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={handleStart}
          disabled={simulation.state === 'running'}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
        >
          <Play className="w-4 h-4" />
          Start
        </button>
        
        <button
          disabled={simulation.state !== 'running'}
          className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
        >
          <Pause className="w-4 h-4" />
          Pause
        </button>
        
        <button
          onClick={handleStop}
          disabled={simulation.state === 'stopped'}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
        >
          <Square className="w-4 h-4" />
          Stop
        </button>
        
        <div className="ml-auto text-sm text-gray-400">
          Elapsed: <span className="text-white font-mono">{simulation.elapsed.toFixed(1)}s</span>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Nodes</label>
          <input
            type="number"
            value={config.nodes}
            onChange={(e) => setConfig({ ...config, nodes: parseInt(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
          />
        </div>
        
        <div>
          <label className="block text-xs text-gray-400 mb-1">Topology</label>
          <select
            value={config.topology}
            onChange={(e) => setConfig({ ...config, topology: e.target.value })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
          >
            <option value="scale_free">Scale-Free</option>
            <option value="mesh">Mesh</option>
            <option value="random">Random</option>
            <option value="small_world">Small World</option>
          </select>
        </div>
        
        <div>
          <label className="block text-xs text-gray-400 mb-1">Duration (s)</label>
          <input
            type="number"
            value={config.duration}
            onChange={(e) => setConfig({ ...config, duration: parseInt(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>
    </div>
  );
}
