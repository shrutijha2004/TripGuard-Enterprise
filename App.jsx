import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Car, Activity, MapPin, 
  AlertTriangle, CheckCircle, Radio, Play, Clock, Navigation, ExternalLink, Download, Trash2, XCircle
} from 'lucide-react';

export default function TripguardEnterpriseApp() {
  const [incidents, setIncidents] = useState([]);
  const [resolvedIncidents, setResolvedIncidents] = useState([]);
  const [wsStatus, setWsStatus] = useState('Connecting...');
  const [simulating, setSimulating] = useState(false);
  const [toast, setToast] = useState(null);

  const activeEmergencies = incidents.length;

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/dashboard');

    ws.onopen = () => setWsStatus('Live Connection Active');
    ws.onmessage = (event) => {
      const newAlert = JSON.parse(event.data);
      setIncidents((prev) => [newAlert, ...prev]);
    };
    ws.onclose = () => setWsStatus('Disconnected - Retry');

    return () => ws.close();
  }, []);

  const triggerSimulation = async (type) => {
    setSimulating(true);
    
    let currentLat = 28.6139; 
    let currentLng = 77.2090;

    try {
      const pos = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { 
          enableHighAccuracy: true, 
          maximumAge: 0,
          timeout: 5000 
        });
      });
      currentLat = pos.coords.latitude;
      currentLng = pos.coords.longitude;
    } catch (e) {
      console.log("Live location access denied. Using default coordinates.");
    }

    const latOffset = (Math.random() - 0.5) * 0.0002;
    const lngOffset = (Math.random() - 0.5) * 0.0002;

    const mockPayloads = {
      SCREAM: {
        vehicle_id: "CAB-8821",
        driver_id: "DRV-901",
        distress_phrase: "Acoustic anomaly / High decibel scream",
        vision_status: "CABIN_DISTRESS_DETECTED",
        confidence_score: 0.96,
        location_lat: parseFloat((currentLat + latOffset).toFixed(6)),
        location_lng: parseFloat((currentLng + lngOffset).toFixed(6))
      },
      DROWSY: {
        vehicle_id: "RAPIDO-771",
        driver_id: "DRV-442",
        distress_phrase: "None (Micro-sleep incident)",
        vision_status: "EYE_CLOSURE_THRESHOLD_EXCEEDED",
        confidence_score: 0.89,
        location_lat: parseFloat((currentLat + latOffset).toFixed(6)),
        location_lng: parseFloat((currentLng + lngOffset).toFixed(6))
      },
      DISTRESS: {
        vehicle_id: "CAB-1049",
        driver_id: "DRV-118",
        distress_phrase: "stop the car let me out",
        vision_status: "STRESSED_MOVEMENT",
        confidence_score: 0.98,
        location_lat: parseFloat((currentLat + latOffset).toFixed(6)),
        location_lng: parseFloat((currentLng + lngOffset).toFixed(6))
      }
    };

    try {
      await fetch('http://127.0.0.1:8000/api/v1/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockPayloads[type])
      });
      
      setToast(`${type} alert deployed to Edge AI.`);
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      setToast("Failed to connect to backend.");
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSimulating(false);
    }
  };

  const handleDispatch = (targetIndex, vehicleId) => {
    const resolvedIncident = incidents[targetIndex];
    
    const now = new Date();
    const auditRecord = {
      ...resolvedIncident,
      resolve_date: now.toLocaleDateString(),
      resolve_day: now.toLocaleDateString('en-US', { weekday: 'long' }),
      resolve_time: now.toLocaleTimeString(),
      status: 'DISPATCHED & LOGGED'
    };

    setResolvedIncidents((prev) => [auditRecord, ...prev]);
    setIncidents((prev) => prev.filter((_, index) => index !== targetIndex));
    
    setToast(`🚓 Authorities dispatched to ${vehicleId}. Incident moved to Audit Log.`);
    setTimeout(() => setToast(null), 4000);
  };

  // NEW: Operator validation handler to dismiss AI false positives
  const handleDismiss = (targetIndex, vehicleId) => {
    const dismissedIncident = incidents[targetIndex];
    
    const now = new Date();
    const auditRecord = {
      ...dismissedIncident,
      resolve_date: now.toLocaleDateString(),
      resolve_day: now.toLocaleDateString('en-US', { weekday: 'long' }),
      resolve_time: now.toLocaleTimeString(),
      status: 'DISMISSED / FALSE POSITIVE'
    };

    setResolvedIncidents((prev) => [auditRecord, ...prev]);
    setIncidents((prev) => prev.filter((_, index) => index !== targetIndex));
    
    setToast(`⚠️ Alert for ${vehicleId} dismissed as False Positive.`);
    setTimeout(() => setToast(null), 4000);
  };

  const exportToExcel = () => {
    if (resolvedIncidents.length === 0) return;

    const headers = ['Incident ID', 'Date', 'Day', 'Time', 'Vehicle ID', 'Driver ID', 'Trigger Event', 'Latitude', 'Longitude', 'Resolution Status'];
    const rows = resolvedIncidents.map(inc => [
      inc.id, inc.resolve_date, inc.resolve_day, inc.resolve_time, inc.vehicle_id, 
      inc.driver_id || 'N/A', inc.event_type, inc.location.lat, inc.location.lon, inc.status
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `Tripguard_Audit_Log_${new Date().toLocaleDateString().replace(/\//g, '-')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearLiveFeed = () => {
    setIncidents([]);
    setToast("Live feed cleared. Ready for next simulation.");
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col relative">
      
      {toast && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 bg-emerald-500 text-white px-6 py-3 rounded-full shadow-lg z-50 font-bold flex items-center gap-2 animate-[bounce_0.3s_ease-out]">
          <CheckCircle size={18} /> {toast}
        </div>
      )}

      <header className="bg-slate-900/80 backdrop-blur border-b border-slate-800 sticky top-0 z-40 px-6 py-4 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600/20 rounded-lg border border-blue-500/30">
            <ShieldAlert className="text-blue-400" size={26} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-white">
              TRIPGUARD <span className="text-blue-400 font-normal">ENTERPRISE</span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">Real-Time Fleet Safety Monitoring API</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {resolvedIncidents.length > 0 && (
            <button 
              onClick={exportToExcel}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors shadow-lg animate-[fadeIn_0.5s_ease-out]"
            >
              <Download size={14} /> Export Audit Log
            </button>
          )}
          
          <div className="flex items-center gap-2 text-xs font-medium bg-slate-900 border border-slate-800 px-4 py-2 rounded-full shadow-inner">
            <span className={`w-2.5 h-2.5 rounded-full ${wsStatus.includes('Active') ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`}></span>
            <span className="text-slate-300">{wsStatus}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-4 sm:p-6 w-full max-w-[1600px] mx-auto flex flex-col lg:flex-row gap-6">
        
        <div className="flex-1 space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 sm:p-5 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400 font-medium">Active Fleet</span>
                <Car size={16} className="text-blue-400" />
              </div>
              <p className="text-xl sm:text-2xl font-bold text-white">12,450</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 sm:p-5 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400 font-medium">Safe Trips</span>
                <CheckCircle size={16} className="text-emerald-400" />
              </div>
              <p className="text-xl sm:text-2xl font-bold text-emerald-400">84,120</p>
            </div>

            <div className={`bg-slate-900 p-4 sm:p-5 rounded-xl border transition-colors ${activeEmergencies > 0 ? 'border-red-500/50 bg-red-950/20' : 'border-slate-800'}`}>
              <div className="flex justify-between items-center mb-2">
                <span className={`text-xs font-medium ${activeEmergencies > 0 ? 'text-red-400' : 'text-slate-400'}`}>Active Emergencies</span>
                <AlertTriangle size={16} className={activeEmergencies > 0 ? 'text-red-400 animate-bounce' : 'text-slate-400'} />
              </div>
              <p className={`text-xl sm:text-2xl font-bold ${activeEmergencies > 0 ? 'text-red-400' : 'text-white'}`}>{activeEmergencies}</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 sm:p-5 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400 font-medium">Latency</span>
                <Activity size={16} className="text-blue-400" />
              </div>
              <p className="text-xl sm:text-2xl font-bold text-white">&lt; 15ms</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl flex flex-col min-h-100">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50 rounded-t-xl">
              <div className="flex items-center gap-2">
                <Radio size={18} className="text-blue-400 animate-pulse" />
                <h2 className="text-sm font-bold tracking-wide uppercase text-slate-200">Live Edge Telemetry Feed</h2>
              </div>
              {incidents.length > 0 && (
                <button 
                  onClick={clearLiveFeed} 
                  className="text-xs font-bold text-slate-500 hover:text-red-400 flex items-center gap-1.5 transition-colors px-3 py-1 rounded bg-slate-800/50 hover:bg-slate-800"
                >
                  <Trash2 size={12} /> Clear Feed
                </button>
              )}
            </div>

            <div className="overflow-x-auto flex-1">
              {incidents.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-12 text-slate-500">
                  <Activity size={48} className="animate-pulse text-slate-700 mb-4" />
                  <p className="text-sm">System armed. Awaiting edge telemetry...</p>
                  <p className="text-xs mt-2 text-slate-600">Use the simulator on the right or autonomous edge scripts.</p>
                </div>
              ) : (
                <table className="w-full text-left text-xs sm:text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px] sm:text-xs">
                      <th className="p-3 sm:p-4">Time</th>
                      <th className="p-3 sm:p-4">Vehicle</th>
                      <th className="p-3 sm:p-4">Trigger Event</th>
                      <th className="p-3 sm:p-4 hidden sm:table-cell">GPS Map</th>
                      <th className="p-3 sm:p-4">Operator Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {incidents.map((inc, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition-colors animate-[fadeIn_0.4s_ease-out]">
                        <td className="p-3 sm:p-4 font-mono text-slate-500 text-[10px] sm:text-xs">
                          {new Date().toLocaleTimeString()}
                        </td>
                        <td className="p-3 sm:p-4 font-bold text-slate-200">{inc.vehicle_id}</td>
                        <td className="p-3 sm:p-4">
                          <span className={`px-2 py-1 rounded text-[10px] font-bold block w-fit mb-1 ${inc.status === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                            {inc.event_type}
                          </span>
                          <span className="text-slate-400 text-xs hidden sm:block truncate max-w-50">{inc.details}</span>
                        </td>
                        
                        <td className="p-3 sm:p-4 hidden sm:table-cell">
                          <a 
                            href={`https://www.google.com/maps/search/?api=1&query=${inc.location.lat},${inc.location.lon}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 hover:text-blue-300 font-medium text-xs transition-colors border border-blue-500/20"
                            title="Open in Google Maps"
                          >
                            <MapPin size={12} /> Live View <ExternalLink size={10} />
                          </a>
                        </td>
                        
                        {/* UPDATED: Added Dismiss / False Positive button alongside Dispatch */}
                        <td className="p-3 sm:p-4">
                          <div className="flex items-center gap-2">
                            <button 
                              onClick={() => handleDispatch(i, inc.vehicle_id)}
                              className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded font-bold text-[10px] sm:text-xs transition-colors flex items-center gap-1 shadow">
                              <Navigation size={12} /> Dispatch
                            </button>

                            <button 
                              onClick={() => handleDismiss(i, inc.vehicle_id)}
                              className="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-red-400 px-3 py-1.5 rounded font-bold text-[10px] sm:text-xs transition-colors border border-slate-700 flex items-center gap-1">
                              <XCircle size={12} /> Dismiss
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        <div className="w-full lg:w-96 shrink-0 space-y-6">
          <div className="bg-linear-to-b from-slate-900 to-slate-950 border border-slate-800 p-6 rounded-xl shadow-xl sticky top-24">
            <div className="mb-6">
              <h2 className="text-lg font-bold text-white mb-1">Live Simulator</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Demonstrate edge AI alerts to evaluators. Clicking these buttons simulates real-time WebSocket payloads arriving from in-cab hardware.
              </p>
            </div>

            <div className="space-y-4">
              <button disabled={simulating} onClick={() => triggerSimulation('SCREAM')} className="w-full bg-slate-900 border border-red-500/30 p-4 rounded-xl hover:border-red-500 hover:bg-red-500/5 text-left transition-all group flex gap-4 items-center">
                <div className="p-3 bg-red-500/10 rounded-lg text-red-400 group-hover:scale-110 transition-transform">
                  <ShieldAlert size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Acoustic Scream</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">High-decibel cabin anomaly</p>
                </div>
              </button>

              <button disabled={simulating} onClick={() => triggerSimulation('DROWSY')} className="w-full bg-slate-900 border border-amber-500/30 p-4 rounded-xl hover:border-amber-500 hover:bg-amber-500/5 text-left transition-all group flex gap-4 items-center">
                <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400 group-hover:scale-110 transition-transform">
                  <Clock size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Driver Drowsiness</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">Eye closure threshold passed</p>
                </div>
              </button>

              <button disabled={simulating} onClick={() => triggerSimulation('DISTRESS')} className="w-full bg-slate-900 border border-blue-500/30 p-4 rounded-xl hover:border-blue-500 hover:bg-blue-500/5 text-left transition-all group flex gap-4 items-center">
                <div className="p-3 bg-blue-500/10 rounded-lg text-blue-400 group-hover:scale-110 transition-transform">
                  <Play size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Vocal Distress</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">NLP matched "help me"</p>
                </div>
              </button>
            </div>
          </div>
        </div>
        
      </main>
    </div>
  );
}