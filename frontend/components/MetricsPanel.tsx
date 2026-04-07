'use client';

import { useNetworkStore } from '@/lib/store';
import { Shield, Activity, Zap, AlertTriangle, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function MetricsPanel() {
  const { metrics, simulation } = useNetworkStore();
  
  const data = [
    { time: 0, fidelity: 0.98, latency: 12, throughput: 2400 },
    { time: 1, fidelity: 0.97, latency: 14, throughput: 2600 },
    { time: 2, fidelity: 0.99, latency: 11, throughput: 2500 },
    { time: 3, fidelity: 0.96, latency: 15, throughput: 2300 },
    { time: 4, fidelity: 0.98, latency: 13, throughput: 2450 },
  ];
  
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="Total Nodes"
        value={metrics.totalNodes}
        icon={<Activity className="w-5 h-5" />}
        color="cyan"
      />
      <MetricCard
        title="Active Links"
        value={metrics.activeLinks}
        icon={<Zap className="w-5 h-5" />}
        color="green"
      />
      <MetricCard
        title="Avg Fidelity"
        value={`${(metrics.averageFidelity * 100).toFixed(1)}%`}
        icon={<Shield className="w-5 h-5" />}
        color="purple"
      />
      <MetricCard
        title="Throughput"
        value={`${(metrics.throughput / 1000).toFixed(1)} Gbps`}
        icon={<TrendingUp className="w-5 h-5" />}
        color="yellow"
      />
      
      <div className="col-span-2 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Fidelity Over Time</h3>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="time" stroke="#6b7280" fontSize={10} />
              <YAxis stroke="#6b7280" fontSize={10} domain={[0.9, 1]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="fidelity" stroke="#00ff88" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="col-span-2 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Latency (ms)</h3>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="time" stroke="#6b7280" fontSize={10} />
              <YAxis stroke="#6b7280" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="latency" stroke="#ff6b6b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, color }: any) {
  const colorMap: Record<string, string> = {
    cyan: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
    green: 'text-green-400 bg-green-400/10 border-green-400/20',
    purple: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
    yellow: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  };
  
  return (
    <div className={`rounded-xl p-4 border ${colorMap[color]} backdrop-blur-sm`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-70">{title}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
