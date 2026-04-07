'use client';

import { useEffect, useState } from 'react';
import { useNetworkStore } from '@/lib/store';
import { AlertCircle, AlertTriangle, Info, XCircle, X } from 'lucide-react';

interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: number;
}

export function AlertsPanel() {
  const { alerts, addAlert, removeAlert } = useNetworkStore();
  const [socket, setSocket] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'subscribe' }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'alert') {
        addAlert({
          id: Date.now().toString(),
          ...data.alert,
          timestamp: Date.now(),
        });
      }
    };
    
    setSocket(ws);
    
    return () => ws.close();
  }, [addAlert]);
  
  const getIcon = (type: string) => {
    switch (type) {
      case 'critical':
      case 'error':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };
  
  const getBorderColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'border-red-500';
      case 'error':
        return 'border-red-400';
      case 'warning':
        return 'border-yellow-500';
      default:
        return 'border-blue-500';
    }
  };
  
  return (
    <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-800 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-cyan-400" />
          Security Alerts
        </h2>
        <span className="text-sm text-gray-400">{alerts.length} alerts</span>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No active alerts</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${getBorderColor(alert.type)} bg-gray-800/50`}
            >
              {getIcon(alert.type)}
              <div className="flex-1">
                <p className="text-sm text-white">{alert.message}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </p>
              </div>
              <button
                onClick={() => removeAlert(alert.id)}
                className="text-gray-500 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
