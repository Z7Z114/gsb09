import { useState, useEffect } from 'react';
import { Info, ChevronRight } from 'lucide-react';
import { api } from '../api';
import { BowPart } from '../types';

export default function BowDiagram() {
  const [parts, setParts] = useState<BowPart[]>([]);
  const [selectedPart, setSelectedPart] = useState<BowPart | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadParts = async () => {
      try {
        const data = await api.materials.listBowParts();
        setParts(data);
        if (data.length > 0) {
          setSelectedPart(data[0]);
        }
      } catch (error) {
        console.error('Failed to load bow parts:', error);
      } finally {
        setLoading(false);
      }
    };
    loadParts();
  }, []);

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
          <h1 className="text-3xl font-bold text-wood-800">角弓拆解图</h1>
          <p className="text-wood-600 mt-1">探索传统角弓的结构奥秘</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
            <div className="relative bg-gradient-to-br from-parchment-50 to-wood-50 rounded-xl p-8 min-h-[400px]">
              <svg viewBox="0 0 800 400" className="w-full h-auto">
                <defs>
                  <linearGradient id="bowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#8B4513" />
                    <stop offset="50%" stopColor="#A0522D" />
                    <stop offset="100%" stopColor="#8B4513" />
                  </linearGradient>
                  <linearGradient id="hornGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#2C1810" />
                    <stop offset="50%" stopColor="#3D2317" />
                    <stop offset="100%" stopColor="#2C1810" />
                  </linearGradient>
                  <linearGradient id="sinewGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#F5DEB3" />
                    <stop offset="50%" stopColor="#DEB887" />
                    <stop offset="100%" stopColor="#F5DEB3" />
                  </linearGradient>
                </defs>

                <path
                  d="M 100 200 Q 200 100 400 180 Q 600 100 700 200 Q 600 300 400 220 Q 200 300 100 200"
                  fill="url(#bowGradient)"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓胎') || null)}
                />

                <path
                  d="M 120 210 Q 220 120 400 190 Q 580 120 680 210"
                  fill="none"
                  stroke="url(#hornGradient)"
                  strokeWidth="6"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓角') || null)}
                />

                <path
                  d="M 120 190 Q 220 280 400 210 Q 580 280 680 190"
                  fill="none"
                  stroke="url(#sinewGradient)"
                  strokeWidth="6"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓筋') || null)}
                />

                <ellipse
                  cx="100"
                  cy="200"
                  rx="30"
                  ry="45"
                  fill="#654321"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓梢') || null)}
                />
                <ellipse
                  cx="700"
                  cy="200"
                  rx="30"
                  ry="45"
                  fill="#654321"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓梢') || null)}
                />

                <rect
                  x="360"
                  y="170"
                  width="80"
                  height="60"
                  rx="8"
                  fill="#5D4037"
                  className="bow-part-hover cursor-pointer"
                  onClick={() => setSelectedPart(parts.find(p => p.name === '弓把') || null)}
                />

                <line x1="130" y1="155" x2="670" y2="155" stroke="#D2B48C" strokeWidth="2" strokeDasharray="5,5" />

                {parts.map((part, index) => {
                  const positions: Record<string, { x: number; y: number }> = {
                    '弓胎': { x: 400, y: 100 },
                    '弓角': { x: 400, y: 140 },
                    '弓筋': { x: 400, y: 280 },
                    '弓梢': { x: 100, y: 80 },
                    '弓把': { x: 400, y: 260 }
                  };
                  const pos = positions[part.name] || { x: 400, y: 200 };
                  return (
                    <g key={part.id} className="cursor-pointer" onClick={() => setSelectedPart(part)}>
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r="16"
                        fill={selectedPart?.id === part.id ? '#D2691E' : '#8B4513'}
                        className="transition-all hover:fill-wood-500"
                      />
                      <text
                        x={pos.x}
                        y={pos.y + 5}
                        textAnchor="middle"
                        fill="white"
                        fontSize="14"
                        fontWeight="bold"
                      >
                        {index + 1}
                      </text>
                    </g>
                  );
                })}
              </svg>

              <div className="absolute bottom-4 right-4 flex items-center gap-2 text-sm text-wood-500">
                <Info size={16} />
                <span>点击图中部件查看详情</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mt-4">
              {parts.map((part, index) => (
                <button
                  key={part.id}
                  onClick={() => setSelectedPart(part)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedPart?.id === part.id
                      ? 'bg-wood-600 text-white'
                      : 'bg-wood-100 text-wood-700 hover:bg-wood-200'
                  }`}
                >
                  {index + 1}. {part.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {selectedPart && (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-wood-400 to-wood-600 rounded-xl flex items-center justify-center text-white font-bold text-xl">
                  {selectedPart.name.charAt(0)}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-wood-800">{selectedPart.name}</h2>
                  {selectedPart.traditional_name && (
                    <p className="text-sm text-wood-500">古称：{selectedPart.traditional_name}</p>
                  )}
                </div>
              </div>

              <p className="text-wood-700 mb-4">{selectedPart.description}</p>

              {selectedPart.materials && selectedPart.materials.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold text-wood-800 mb-2">常用材料</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedPart.materials.map((material, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-parchment-100 text-wood-700 rounded-full text-sm"
                      >
                        {material}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedPart.crafting_steps && selectedPart.crafting_steps.length > 0 && (
                <div>
                  <h3 className="font-semibold text-wood-800 mb-3">制作工序</h3>
                  <div className="space-y-3">
                    {selectedPart.crafting_steps.map((step) => (
                      <div key={step.step} className="flex gap-3">
                        <div className="w-8 h-8 bg-wood-100 text-wood-700 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                          {step.step}
                        </div>
                        <p className="text-wood-600 text-sm pt-1">{step.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
