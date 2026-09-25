import { useState, useEffect, useRef } from 'react';
import { Send, Users, MessageCircle, User } from 'lucide-react';
import { api } from '../api';
import { Message, Craftsman } from '../types';

export default function CraftsmenChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [craftsmen, setCraftsmen] = useState<Craftsman[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [selectedCraftsman, setSelectedCraftsman] = useState<Craftsman | null>(null);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [messagesData, craftsmenData] = await Promise.all([
          api.messages.list(),
          api.craftsmen.list()
        ]);
        setMessages(messagesData.reverse());
        setCraftsmen(craftsmenData);
        if (craftsmenData.length > 0) {
          setSelectedCraftsman(craftsmenData[0]);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/messages/ws`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    return () => {
      wsRef.current?.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedCraftsman) return;

    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          content: newMessage,
          craftsman_id: selectedCraftsman.id,
          message_type: 'chat'
        }));
      } else {
        const message = await api.messages.create({
          content: newMessage,
          craftsman_id: selectedCraftsman.id,
          message_type: 'chat'
        });
        setMessages(prev => [...prev, message]);
      }
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getSchoolColor = (school: string) => {
    const colors: Record<string, string> = {
      '汉族传统弓': 'bg-amber-100 text-amber-800',
      '蒙古族角弓': 'bg-blue-100 text-blue-800',
      '满族清弓': 'bg-purple-100 text-purple-800',
      '藏族牛角弓': 'bg-cyan-100 text-cyan-800',
      '彝族竹弓': 'bg-green-100 text-green-800',
    };
    return colors[school] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-wood-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-wood-800">匠人交流</h1>
          <p className="text-wood-600 mt-1">与各流派匠人交流传统制弓技艺</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-6 h-[600px]">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl p-4 shadow-lg border border-wood-100 h-full overflow-y-auto scrollbar-hide">
            <h3 className="font-semibold text-wood-800 mb-4 flex items-center gap-2">
              <Users size={18} />
              在线匠人
            </h3>
            <div className="space-y-2">
              {craftsmen.map((craftsman) => (
                <button
                  key={craftsman.id}
                  onClick={() => setSelectedCraftsman(craftsman)}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all ${
                    selectedCraftsman?.id === craftsman.id
                      ? 'bg-wood-100 border-2 border-wood-400'
                      : 'hover:bg-wood-50 border-2 border-transparent'
                  }`}
                >
                  <div className="relative">
                    <div className="w-10 h-10 bg-gradient-to-br from-wood-400 to-wood-600 rounded-full flex items-center justify-center text-white font-bold">
                      {craftsman.name.charAt(0)}
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
                  </div>
                  <div className="text-left flex-1">
                    <p className="font-medium text-wood-800 text-sm">{craftsman.name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getSchoolColor(craftsman.school)}`}>
                      {craftsman.school}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-3 flex flex-col">
          <div className="bg-white rounded-2xl shadow-lg border border-wood-100 flex-1 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-wood-100 bg-gradient-to-r from-wood-50 to-parchment-50">
              <div className="flex items-center gap-3">
                <MessageCircle className="text-wood-600" size={20} />
                <div>
                  <h3 className="font-semibold text-wood-800">匠人交流群</h3>
                  <p className="text-xs text-wood-500">{craftsmen.length} 位匠人在线</p>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
              {messages.map((message, index) => (
                <div
                  key={message.id || index}
                  className={`flex ${message.craftsman_id === selectedCraftsman?.id ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[70%] ${message.craftsman_id === selectedCraftsman?.id ? 'order-2' : 'order-1'}`}>
                    <div className={`flex items-center gap-2 mb-1 ${message.craftsman_id === selectedCraftsman?.id ? 'justify-end' : ''}`}>
                      {message.craftsman && (
                        <>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getSchoolColor(message.craftsman.school)}`}>
                            {message.craftsman.school}
                          </span>
                          <span className="text-sm font-medium text-wood-700">{message.craftsman.name}</span>
                        </>
                      )}
                      <span className="text-xs text-wood-400">
                        {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div
                      className={`px-4 py-3 rounded-2xl ${
                        message.craftsman_id === selectedCraftsman?.id
                          ? 'bg-wood-600 text-white rounded-br-md'
                          : 'bg-wood-100 text-wood-800 rounded-bl-md'
                      }`}
                    >
                      {message.content}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t border-wood-100 bg-wood-50">
              <div className="flex items-center gap-3">
                {selectedCraftsman && (
                  <div className="w-10 h-10 bg-gradient-to-br from-wood-400 to-wood-600 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    {selectedCraftsman.name.charAt(0)}
                  </div>
                )}
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="输入您的问题或见解..."
                    className="w-full px-4 py-3 pr-12 border border-wood-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-wood-400 focus:border-transparent bg-white"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!newMessage.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-wood-600 text-white rounded-lg hover:bg-wood-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
