import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Menu, X, Target, Users, MessageSquare, Library, FileText, Home } from 'lucide-react';
import HomePage from './pages/HomePage';
import BowDiagram from './pages/BowDiagram';
import WoodLibrary from './pages/WoodLibrary';
import CraftsmenChat from './pages/CraftsmenChat';
import Archives from './pages/Archives';
import AudioUpload from './pages/AudioUpload';

function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: '首页', icon: Home },
    { path: '/bow-diagram', label: '角弓拆解', icon: Target },
    { path: '/wood-library', label: '木材纹理', icon: Library },
    { path: '/craftsmen', label: '匠人交流', icon: Users },
    { path: '/audio', label: '音频处理', icon: MessageSquare },
    { path: '/archives', label: '工艺档案', icon: FileText },
  ];

  return (
    <div className="min-h-screen wood-texture">
      <nav className="bg-gradient-to-r from-wood-800 to-wood-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-parchment-400 rounded-full flex items-center justify-center">
                <span className="text-wood-800 font-bold text-xl">弓</span>
              </div>
              <div>
                <h1 className="text-xl font-bold">弓道纪要</h1>
                <p className="text-xs text-wood-200">传统弓箭制作工艺传承平台</p>
              </div>
            </Link>

            <div className="hidden md:flex space-x-1">
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                    location.pathname === item.path
                      ? 'bg-wood-600 text-parchment-300'
                      : 'hover:bg-wood-600/50'
                  }`}
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>

            <button
              className="md:hidden p-2"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>

          {menuOpen && (
            <div className="md:hidden pb-4 space-y-2">
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
                    location.pathname === item.path
                      ? 'bg-wood-600 text-parchment-300'
                      : 'hover:bg-wood-600/50'
                  }`}
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/bow-diagram" element={<BowDiagram />} />
          <Route path="/wood-library" element={<WoodLibrary />} />
          <Route path="/craftsmen" element={<CraftsmenChat />} />
          <Route path="/audio" element={<AudioUpload />} />
          <Route path="/archives" element={<Archives />} />
        </Routes>
      </main>

      <footer className="bg-wood-800 text-wood-200 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-sm">🏹 弓道纪要 - 守护传统弓箭制作工艺，传承非遗文化</p>
          <p className="text-xs mt-2 text-wood-400">© 2024 传统弓箭制作工艺传承平台</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
