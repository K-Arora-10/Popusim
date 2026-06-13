import React, { useState, useEffect } from 'react';
import { startSimulation, getSimulationHistory, getSimulationStatus, getSimulationReport, deleteSimulation } from './api';
import { connectSimulationWS } from './ws';

// Components
import URLInput from './components/URLInput';
import AgentSwarm from './components/AgentSwarm';
import AgentCard from './components/AgentCard';
import FunnelChart from './components/FunnelChart';
import BugFeed from './components/BugFeed';
import NpsGauge from './components/NpsGauge';
import PersonaHeatmap from './components/PersonaHeatmap';
import ReportPanel from './components/ReportPanel';
import ChatSidebar from './components/ChatSidebar';

// Icons
import { LayoutDashboard, LogOut, ArrowLeft, RefreshCw, MessageSquareCode, Sparkles } from 'lucide-react';

export default function App() {
  const [view, setView] = useState('input'); // input, active, report
  const [simHistory, setSimHistory] = useState([]);
  
  // Active Simulation State
  const [currentSimId, setCurrentSimId] = useState(null);
  const [simStatus, setSimStatus] = useState(null); // FastAPI StatusResponse
  const [personas, setPersonas] = useState([]);
  const [agentLogs, setAgentLogs] = useState({}); // persona_id -> list of steps
  const [selectedPersonaId, setSelectedPersonaId] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Initializing...');
  const [simError, setSimError] = useState('');
  
  // Report state
  const [report, setReport] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const history = await getSimulationHistory();
      setSimHistory(history);
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  };

  const handleStartSimulation = async (url, numPersonas, useSharedSession) => {
    setLoading(true);
    setSimError('');
    try {
      const res = await startSimulation(url, numPersonas, useSharedSession);
      setCurrentSimId(res.simulation_id);
      setPersonas([]);
      setAgentLogs({});
      setSelectedPersonaId(null);
      setView('active');
      setStatusMessage('Request received. Initializing database schema...');
      
      // Start WebSocket Connection
      connectWS(res.simulation_id);
    } catch (e) {
      setSimError(e.message);
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const connectWS = (simulationId) => {
    const disconnect = connectSimulationWS(
      simulationId,
      (event) => {
        // Event Message Handler
        if (event.type === 'status_update') {
          setStatusMessage(event.message);
          setSimStatus(prev => prev ? { ...prev, status: event.status } : null);
        }
        
        else if (event.type === 'personas_generated') {
          setPersonas(event.personas);
          if (event.personas.length > 0) {
            setSelectedPersonaId(event.personas[0].id);
          }
        }
        
        else if (event.type === 'agent_step') {
          // Append log to persona
          setAgentLogs(prev => {
            const currentLogs = prev[event.persona_id] || [];
            // De-duplicate if step received twice
            if (currentLogs.some(l => l.step === event.step)) return prev;
            return {
              ...prev,
              [event.persona_id]: [...currentLogs, event]
            };
          });

          // Update individual persona status in state
          setPersonas(prev => 
            prev.map(p => p.id === event.persona_id ? { ...p, status: event.status } : p)
          );
        }
        
        else if (event.type === 'simulation_complete') {
          setStatusMessage('Simulation completed. Structuring analysis report...');
          setReport({
            nps: event.nps,
            churn_rate: event.churn_rate,
            wtp: event.wtp,
            bugs: event.bugs,
            summary: event.summary
          });
          
          // Poll final status
          fetchReportDetails(simulationId);
        }
      },
      (err) => {
        console.error('WebSocket encountered error:', err);
      },
      () => {
        console.log('WebSocket closed.');
      }
    );

    // Store disconnect function in window context or clean up on route change
    return () => disconnect();
  };

  const fetchReportDetails = async (simulationId) => {
    try {
      const reportData = await getSimulationReport(simulationId);
      const statusData = await getSimulationStatus(simulationId);
      
      setReport(reportData);
      setPersonas(statusData.personas);
      setSimStatus(statusData);
      setView('report');
      loadHistory(); // refresh history list
    } catch (e) {
      console.error('Failed to load report:', e);
      setStatusMessage('Error loading final report details.');
    }
  };

  const handleSelectHistory = async (simulationId) => {
    setLoading(true);
    try {
      const statusData = await getSimulationStatus(simulationId);
      setSimStatus(statusData);
      setPersonas(statusData.personas);
      setCurrentSimId(simulationId);

      // Re-populate logs from status personas/logs
      // Since logs are saved in DB, let's fetch individual steps
      // To make it simple, we load the report which contains bugs/summary
      if (statusData.status === 'completed') {
        const reportData = await getSimulationReport(simulationId);
        setReport(reportData);
        
        // Fetch logs for personas
        const logRes = await fetch(`/api/simulation/${simulationId}/status`); // this fetches status
        // Let's call standard endpoint to get simulation history detail
        // For convenience, we can fetch all steps from API or let it load report.
        // Let's load the active logs by getting status logs:
        // We'll write a small fetch call for logs if needed, but since we are keeping it light,
        // let's do a fast fetch to load persona history logs.
        const resLogs = await fetch(`/api/simulation/${simulationId}/status`);
        // We can fetch logs directly or mock empty logs (we will fetch from sqlite logs table if needed,
        // but wait! We can fetch them by querying a status API route that returns logs!
        // Let's modify models or add a route in simulation.py if we need to load logs.
        // Wait, does getSimulationStatus include logs?
        // Let's write a route or fetch logs if we didn't add it in the schema.
        // Let's add a logs fetcher in App.jsx:
        const response = await fetch(`/api/simulation/${simulationId}/status`); // or a new endpoint we can create.
        // Let's make sure we fetch agent steps. Let's look at what endpoints we have in simulation.py.
        // We have /simulation/{id}/status which returns personas. We can query logs inside that endpoint or create a route.
        // Let's create an endpoint in routes/simulation.py or check if we can query logs.
        // Ah, let's check: we didn't explicitly return logs in SimulationStatusResponse.
        // Let's check: we can fetch agent logs from `/api/simulation/{simulation_id}/logs`!
        // Let's look at `routes/simulation.py` to see if we have that route. We don't have it. We should add a route to get agent logs!
        // That is a simple change in `routes/simulation.py`. Let's write that edit soon.
        // For now, let's complete App.jsx.
        await fetchLogsForHistory(simulationId);
        setView('report');
      } else if (statusData.status === 'running' || statusData.status === 'ingesting') {
        // Re-connect to active WS streams
        setView('active');
        connectWS(simulationId);
      } else {
        // Failed simulation
        setSimError('This simulation failed to complete.');
        setView('input');
      }
    } catch (e) {
      console.error(e);
      setSimError('Failed to load this simulation session.');
      setView('input');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogsForHistory = async (simulationId) => {
    try {
      const response = await fetch(`/api/simulation/${simulationId}/logs`);
      if (response.ok) {
        const data = await response.json();
        // data will be persona_id -> list of steps
        setAgentLogs(data);
      }
    } catch (e) {
      console.error('Failed to fetch historical logs:', e);
    }
  };

  const handleDeleteHistory = async (simulationId) => {
    if (!confirm('Are you sure you want to delete this simulation record?')) return;
    try {
      await deleteSimulation(simulationId);
      loadHistory();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-darkBg text-gray-100 flex flex-col font-sans">
      {/* Header navbar */}
      <header className="border-b border-darkBorder bg-darkCard/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div
            className="flex items-center gap-2 cursor-pointer group"
            onClick={() => setView('input')}
          >
            <span className="text-2xl group-hover:scale-110 transition-transform">🤖</span>
            <span className="font-extrabold text-lg bg-gradient-to-r from-neonCyan to-neonPurple bg-clip-text text-transparent">
              PopuSim
            </span>
          </div>

          <div className="flex items-center gap-4">
            {view !== 'input' && (
              <button
                onClick={() => setView('input')}
                className="text-xs bg-darkBg border border-darkBorder hover:border-gray-700 px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-all text-gray-400 hover:text-white"
              >
                <ArrowLeft size={13} /> Exit Dashboard
              </button>
            )}
            
            {view === 'report' && (
              <button
                onClick={() => setIsChatOpen(!isChatOpen)}
                className="text-xs bg-neonCyan text-darkBg font-bold px-4 py-2 rounded-xl flex items-center gap-1.5 hover:opacity-90 active:scale-95 transition-all"
              >
                <MessageSquareCode size={13} /> SimGPT Analyst
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* VIEW 1: Input Landing Page */}
        {view === 'input' && (
          <div className="space-y-4">
            {simError && (
              <div className="max-w-4xl mx-auto bg-red-500/15 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm flex items-center justify-between">
                <span>{simError}</span>
                <button onClick={() => setSimError('')} className="font-bold hover:text-white">✕</button>
              </div>
            )}
            <URLInput
              onSubmit={handleStartSimulation}
              history={simHistory}
              onSelectHistory={handleSelectHistory}
              onDeleteHistory={handleDeleteHistory}
              loading={loading}
            />
          </div>
        )}

        {/* VIEW 2: Active Simulation swarm */}
        {view === 'active' && (
          <div className="space-y-6">
            {/* Status updates banner */}
            <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block">Simulation Status</span>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-neonCyan animate-ping"></span>
                  {statusMessage}
                </h2>
              </div>
              
              <div className="flex items-center gap-3 text-xs bg-darkBg border border-darkBorder px-4 py-2 rounded-xl text-gray-400">
                <RefreshCw size={13} className="animate-spin text-neonPurple" />
                <span>Streaming live events</span>
              </div>
            </div>

            {/* Grid display */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
              {/* Left Swarm column */}
              <div className="xl:col-span-5">
                <AgentSwarm
                  personas={personas}
                  activePersonaId={selectedPersonaId}
                  onSelectPersona={setSelectedPersonaId}
                  logs={agentLogs}
                />
              </div>

              {/* Right browser column */}
              <div className="xl:col-span-7 h-full">
                <AgentCard
                  persona={personas.find(p => p.id === selectedPersonaId)}
                  logs={agentLogs[selectedPersonaId] || []}
                />
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: Report Summary Dashboard */}
        {view === 'report' && report && (
          <div className="space-y-6">
            {/* Simulation Header */}
            <div className="bg-darkCard border border-darkBorder rounded-2xl p-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-neonCyan font-extrabold uppercase tracking-widest">Completed Simulation</span>
                <h1 className="text-xl font-bold text-white truncate max-w-xl">
                  {simStatus?.url}
                </h1>
                <p className="text-xs text-gray-500">
                  Ran on {simStatus ? new Date(simStatus.created_at).toLocaleString() : ''}
                </p>
              </div>

              <div className="flex gap-2.5 no-print">
                <button
                  onClick={() => window.print()}
                  className="text-xs bg-gradient-to-r from-neonCyan to-neonPurple hover:opacity-90 active:scale-95 text-darkBg font-bold px-4 py-2.5 rounded-xl transition-all shadow-sm flex items-center gap-1"
                >
                  Download PDF Report
                </button>
                <button
                  onClick={() => setView('input')}
                  className="text-xs bg-darkBg border border-darkBorder hover:border-gray-700 text-gray-400 hover:text-white font-bold px-4 py-2.5 rounded-xl transition-all"
                >
                  Start New Simulation
                </button>
              </div>

            </div>

            {/* Top Row Score widgets */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <NpsGauge score={report.nps} />
              
              <FunnelChart personas={personas} logs={agentLogs} />
              
              <BugFeed bugs={report.bugs} />
            </div>

            {/* Middle Heatmap row */}
            <div className="grid grid-cols-1 gap-6">
              <PersonaHeatmap personas={personas} logs={agentLogs} />
            </div>

            {/* Bottom Report Panel row */}
            <div className="grid grid-cols-1 gap-6">
              <ReportPanel report={report} />
            </div>

            {/* Conversational Floating Chat Sidebar */}
            <ChatSidebar
              simulationId={currentSimId}
              isOpen={isChatOpen}
              onClose={() => setIsChatOpen(false)}
            />
          </div>
        )}
      </main>
    </div>
  );
}
