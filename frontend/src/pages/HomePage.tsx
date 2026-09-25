import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Library, Users, FileText, Mic, ArrowRight, Sparkles } from 'lucide-react';
import { api } from '../api';
import { Craftsman, CraftArchive, WoodMaterial } from '../types';

export default function HomePage() {
  const [craftsmen, setCraftsmen] = useState<Craftsman[]>([]);
  const [archives, setArchives] = useState<CraftArchive[]>([]);
  const [woods, setWoods] = useState<WoodMaterial[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        await api.materials.seedData();
        const [craftsmenData, archivesData, woodsData] = await Promise.all([
          api.craftsmen.list(),
          api.archives.list(),
          api.materials.listWoods()
        ]);
        setCraftsmen(craftsmenData);
        setArchives(archivesData);
        setWoods(woodsData);
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const features = [
    {
      icon: Target,
      title: '角弓拆解图',
      description: '交互式角弓结构分解，详细展示各部件名称、材料和制作工艺',
      link: '/bow-diagram',
      color: 'from-amber-500 to-orange-600'
    },
    {
      icon: Library,
      title: '木材纹理库',
      description: '收录多种制弓木材的纹理、特性和传统使用方法',
      link: '/wood-library',
      color: 'from-green-500 to-emerald-600'
    },
    {
      icon: Users,
      title: '匠人交流',
      description: '各流派匠人实时交流平台，传承口传技艺',
      link: '/craftsmen',
      color: 'from-blue-500 to-indigo-600'
    },
    {
      icon: Mic,
      title: '音频处理',
      description: '上传会议录音，自动转写口传知识，标记匠人身份',
      link: '/audio',
      color: 'from-purple-500 to-pink-600'
    },
    {
      icon: FileText,
      title: '工艺档案',
      description: 'AI智能生成图文档案，一键发送至非遗保护中心',
      link: '/archives',
      color: 'from-red-500 to-rose-600'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-wood-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="text-center py-12 bg-gradient-to-br from-wood-100 to-parchment-100 rounded-3xl p-8 shadow-xl">
        <div className="inline-flex items-center gap-2 bg-wood-100 text-wood-700 px-4 py-2 rounded-full mb-6">
          <Sparkles size={18} />
          <span className="text-sm font-medium">传承千年技艺，守护非遗文化</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-wood-800 mb-4">
          弓道纪要
        </h1>
        <p className="text-xl text-wood-600 mb-8 max-w-2xl mx-auto">
          传统弓箭制作工艺传承平台，记录角弓制作的每一道工序，
          保留匠人们的口传心授，让古老技艺在数字时代延续生命力
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link
            to="/bow-diagram"
            className="inline-flex items-center gap-2 bg-wood-600 hover:bg-wood-700 text-white px-8 py-3 rounded-xl font-medium transition-all hover:shadow-lg"
          >
            探索角弓结构
            <ArrowRight size={18} />
          </Link>
          <Link
            to="/craftsmen"
            className="inline-flex items-center gap-2 bg-white hover:bg-wood-50 text-wood-700 border-2 border-wood-300 px-8 py-3 rounded-xl font-medium transition-all"
          >
            与匠人交流
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-wood-800 mb-6">核心功能</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Link
              key={index}
              to={feature.link}
              className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 border border-wood-100"
            >
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <feature.icon className="text-white" size={28} />
              </div>
              <h3 className="text-xl font-bold text-wood-800 mb-2">{feature.title}</h3>
              <p className="text-wood-600">{feature.description}</p>
              <div className="mt-4 flex items-center text-wood-500 group-hover:text-wood-700">
                <span className="text-sm">了解更多</span>
                <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid lg:grid-cols-2 gap-8">
        <section className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
          <h2 className="text-xl font-bold text-wood-800 mb-4 flex items-center gap-2">
            <Users className="text-wood-600" size={24} />
            技艺传承人
          </h2>
          <div className="space-y-4">
            {craftsmen.slice(0, 3).map(craftsman => (
              <div key={craftsman.id} className="flex items-center gap-4 p-3 bg-wood-50 rounded-xl">
                <div className="w-12 h-12 bg-gradient-to-br from-wood-400 to-wood-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  {craftsman.name.charAt(0)}
                </div>
                <div>
                  <p className="font-semibold text-wood-800">{craftsman.name}</p>
                  <p className="text-sm text-wood-600">
                    {craftsman.school} · 第{craftsman.generation}代传承人
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
          <h2 className="text-xl font-bold text-wood-800 mb-4 flex items-center gap-2">
            <Library className="text-wood-600" size={24} />
            制弓木材
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {woods.slice(0, 4).map(wood => (
              <div key={wood.id} className="p-3 bg-gradient-to-br from-wood-50 to-parchment-50 rounded-xl border border-wood-100">
                <p className="font-semibold text-wood-800">{wood.name}</p>
                <p className="text-xs text-wood-500 mt-1">
                  {wood.suitable_parts?.slice(0, 2).join('、')}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {archives.length > 0 && (
        <section className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
          <h2 className="text-xl font-bold text-wood-800 mb-4 flex items-center gap-2">
            <FileText className="text-wood-600" size={24} />
            最新工艺档案
          </h2>
          <div className="space-y-3">
            {archives.slice(0, 3).map(archive => (
              <div key={archive.id} className="flex items-center justify-between p-4 bg-wood-50 rounded-xl hover:bg-wood-100 transition-colors">
                <div>
                  <p className="font-semibold text-wood-800">{archive.title}</p>
                  <p className="text-sm text-wood-500 mt-1 line-clamp-1">{archive.summary}</p>
                </div>
                <div className="flex items-center gap-2">
                  {archive.sent_to_feiyi ? (
                    <span className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full">已发送</span>
                  ) : (
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full">待发送</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
