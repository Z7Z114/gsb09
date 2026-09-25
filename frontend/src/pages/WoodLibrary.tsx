import { useState, useEffect } from 'react';
import { TreeDeciduous, MapPin, Check, Info } from 'lucide-react';
import { api } from '../api';
import { WoodMaterial } from '../types';

export default function WoodLibrary() {
  const [woods, setWoods] = useState<WoodMaterial[]>([]);
  const [selectedWood, setSelectedWood] = useState<WoodMaterial | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadWoods = async () => {
      try {
        const data = await api.materials.listWoods();
        setWoods(data);
        if (data.length > 0) {
          setSelectedWood(data[0]);
        }
      } catch (error) {
        console.error('Failed to load woods:', error);
      } finally {
        setLoading(false);
      }
    };
    loadWoods();
  }, []);

  const generateTexturePattern = (name: string) => {
    const patterns: Record<string, string> = {
      '桦木': 'repeating-linear-gradient(90deg, #E8D4B8, #E8D4B8 2px, #D4B896 2px, #D4B896 8px)',
      '橡木': 'repeating-linear-gradient(90deg, #C4A574, #C4A574 3px, #A0522D 3px, #A0522D 10px)',
      '榆木': 'repeating-linear-gradient(90deg, #D4B896, #D4B896 4px, #B8860B 4px, #B8860B 8px)',
      '桑木': 'repeating-linear-gradient(90deg, #DEB887, #DEB887 2px, #CD853F 2px, #CD853F 6px)',
      '柘木': 'repeating-linear-gradient(90deg, #DAA520, #DAA520 3px, #B8860B 3px, #B8860B 9px)',
    };
    return patterns[name] || 'repeating-linear-gradient(90deg, #D2B48C, #D2B48C 3px, #A0522D 3px, #A0522D 8px)';
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
          <h1 className="text-3xl font-bold text-wood-800">木材纹理库</h1>
          <p className="text-wood-600 mt-1">探索传统制弓所用的珍贵木材</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl p-4 shadow-lg border border-wood-100 space-y-2">
            {woods.map((wood) => (
              <button
                key={wood.id}
                onClick={() => setSelectedWood(wood)}
                className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all ${
                  selectedWood?.id === wood.id
                    ? 'bg-wood-100 border-2 border-wood-400'
                    : 'hover:bg-wood-50 border-2 border-transparent'
                }`}
              >
                <div
                  className="w-16 h-16 rounded-lg shadow-inner flex-shrink-0"
                  style={{ background: generateTexturePattern(wood.name) }}
                />
                <div className="text-left">
                  <p className="font-semibold text-wood-800">{wood.name}</p>
                  <p className="text-xs text-wood-500 italic">{wood.scientific_name}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2">
          {selectedWood && (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100 space-y-6">
              <div className="flex items-start gap-6">
                <div
                  className="w-48 h-48 rounded-2xl shadow-lg flex-shrink-0"
                  style={{ background: generateTexturePattern(selectedWood.name) }}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <TreeDeciduous className="text-wood-600" size={28} />
                    <h2 className="text-2xl font-bold text-wood-800">{selectedWood.name}</h2>
                  </div>
                  <p className="text-wood-500 italic mb-4">{selectedWood.scientific_name}</p>
                  <div className="flex items-center gap-2 text-wood-600 mb-4">
                    <MapPin size={16} />
                    <span>{selectedWood.origin}</span>
                  </div>
                  <p className="text-wood-700 leading-relaxed">{selectedWood.description}</p>
                </div>
              </div>

              {selectedWood.properties && (
                <div className="bg-wood-50 rounded-xl p-5">
                  <h3 className="font-semibold text-wood-800 mb-4">木材特性</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-wood-700">{selectedWood.properties.density}</div>
                      <div className="text-sm text-wood-500">密度 (g/cm³)</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-wood-700">{selectedWood.properties.hardness}</div>
                      <div className="text-sm text-wood-500">硬度</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-wood-700">{selectedWood.properties.elasticity}</div>
                      <div className="text-sm text-wood-500">弹性</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-wood-700">{selectedWood.properties.durability}</div>
                      <div className="text-sm text-wood-500">耐久性</div>
                    </div>
                  </div>
                </div>
              )}

              {selectedWood.suitable_parts && selectedWood.suitable_parts.length > 0 && (
                <div>
                  <h3 className="font-semibold text-wood-800 mb-3 flex items-center gap-2">
                    <Check size={18} className="text-green-600" />
                    适用部位
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedWood.suitable_parts.map((part, idx) => (
                      <span
                        key={idx}
                        className="px-4 py-2 bg-green-50 text-green-700 rounded-full text-sm font-medium"
                      >
                        {part}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedWood.traditional_usage && (
                <div className="bg-parchment-50 rounded-xl p-5 border-l-4 border-wood-400">
                  <h3 className="font-semibold text-wood-800 mb-2 flex items-center gap-2">
                    <Info size={18} className="text-wood-600" />
                    传统用法
                  </h3>
                  <p className="text-wood-700 leading-relaxed">{selectedWood.traditional_usage}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
