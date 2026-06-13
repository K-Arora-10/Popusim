import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquareCode, Sparkles, X, ChevronRight } from 'lucide-react';
import { sendChatMessage, getChatHistory } from '../api';

export default function ChatSidebar({ simulationId, isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (simulationId && isOpen) {
      loadHistory();
    }
  }, [simulationId, isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const loadHistory = async () => {
    try {
      const history = await getChatHistory(simulationId);
      setMessages(history);
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput('');
    setError('');
    
    // Add user message optimistically
    const userMsg = { role: 'user', content: query, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    
    setLoading(true);
    try {
      const response = await sendChatMessage(simulationId, query);
      const assistantMsg = { role: 'assistant', content: response.response, timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setError('Failed to get answer. Make sure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 bottom-0 w-80 sm:w-96 bg-darkCard border-l border-darkBorder z-50 flex flex-col shadow-2xl transition-all duration-300">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-darkBorder flex items-center justify-between bg-darkBg/60">
        <div className="flex items-center gap-2">
          <MessageSquareCode size={18} className="text-neonCyan animate-pulse" />
          <div>
            <h3 className="font-bold text-white text-sm">SimGPT Analyst</h3>
            <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">PopuSim Assistant</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-darkBg transition-all"
        >
          <X size={16} />
        </button>
      </div>

      {/* Messages List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-gray-500 flex flex-col items-center justify-center gap-3 mt-12">
            <Sparkles size={32} className="text-neonCyan animate-spin" />
            <p className="text-xs font-bold text-gray-300">Discuss Simulation Results</p>
            <p className="text-[10px] text-gray-500 max-w-[200px] leading-relaxed">
              Ask questions about user paths, conversion roadblocks, or specific personas.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={index}
                className={`flex flex-col max-w-[85%] ${isUser ? 'ml-auto items-end' : 'mr-auto items-start'}`}
              >
                <div
                  className={`rounded-xl p-3 text-xs leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-neonCyan text-darkBg font-semibold shadow-sm'
                      : 'bg-darkBg border border-darkBorder text-gray-200'
                  }`}
                >
                  {msg.content}
                </div>
                <span className="text-[8px] text-gray-600 mt-1 uppercase font-bold tracking-wider">
                  {isUser ? 'You' : 'SimGPT'}
                </span>
              </div>
            );
          })
        )}
        
        {/* Loading Indicator */}
        {loading && (
          <div className="flex flex-col items-start max-w-[80%] mr-auto space-y-1">
            <div className="bg-darkBg border border-darkBorder rounded-xl p-3 flex items-center gap-2 text-xs text-gray-400">
              <span className="w-1.5 h-1.5 bg-neonCyan rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-neonCyan rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-neonCyan rounded-full animate-bounce [animation-delay:0.4s]"></span>
              <span className="text-[10px] text-gray-500 font-bold ml-1 uppercase">Analyzing Logs...</span>
            </div>
          </div>
        )}
        
        {error && <p className="text-[10px] text-neonRed text-center font-bold mt-2">{error}</p>}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Submit form */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-darkBorder bg-darkBg/30">
        <div className="relative flex items-center">
          <input
            type="text"
            placeholder="e.g. Why did Arthur Pendelton churn?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="w-full bg-darkBg border border-darkBorder focus:border-neonCyan rounded-xl py-3 pl-4 pr-10 text-xs text-white outline-none outline-none placeholder-gray-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 text-gray-400 hover:text-neonCyan disabled:opacity-30 p-1.5 rounded-lg hover:bg-darkBg/60 transition-all"
          >
            <Send size={14} />
          </button>
        </div>
      </form>
    </div>
  );
}
