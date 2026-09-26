import { useState, useEffect } from 'react';
import { FileText, Mail, Send, CheckCircle, Clock, Loader2, Eye, Download } from 'lucide-react';
import { api } from '../api';
import { CraftArchive, AudioRecording } from '../types';

export default function Archives() {
  const [archives, setArchives] = useState<CraftArchive[]>([]);
  const [recordings, setRecordings] = useState<AudioRecording[]>([]);
  const [selectedArchive, setSelectedArchive] = useState<CraftArchive | null>(null);
  const [selectedRecording, setSelectedRecording] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [archivesData, recordingsData] = await Promise.all([
        api.archives.list(),
        api.audio.list()
      ]);
      setArchives(archivesData);
      setRecordings(recordingsData.filter(r => r.status === 'transcribed'));
      if (archivesData.length > 0) {
        setSelectedArchive(archivesData[0]);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedRecording) return;
    setGenerating(true);
    try {
      await api.archives.generate(selectedRecording);
      setTimeout(async () => {
        await loadData();
        setGenerating(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to generate archive:', error);
      setGenerating(false);
    }
  };

  const handleSendEmail = async (archiveId: number) => {
    setSending(true);
    try {
      const result = await api.archives.sendEmail({ archive_id: archiveId });
      await loadData();
      alert(result.success ? '邮件发送成功！' : `邮件发送失败: ${result.message}`);
    } catch (error) {
      console.error('Failed to send email:', error);
      alert('邮件发送失败');
    } finally {
      setSending(false);
    }
  };

  const handlePreview = async (archiveId: number) => {
    try {
      const result = await api.archives.getHtml(archiveId);
      setHtmlContent(result.html_content);
      setShowPreview(true);
    } catch (error) {
      console.error('Failed to load archive HTML:', error);
    }
  };

  const handleDownload = (archive: CraftArchive) => {
    if (!htmlContent) return;
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `工艺档案_${archive.title}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const transcribedRecordings = recordings.filter(r => r.status === 'transcribed');

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
          <h1 className="text-3xl font-bold text-wood-800">工艺档案</h1>
          <p className="text-wood-600 mt-1">AI智能生成工艺档案，一键发送至非遗保护中心</p>
        </div>
      </div>

      {transcribedRecordings.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
          <h3 className="font-semibold text-wood-800 mb-4 flex items-center gap-2">
            <FileText size={18} />
            生成新档案
          </h3>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[250px]">
              <label className="block text-sm font-medium text-wood-700 mb-2">选择已转写的录音</label>
              <select
                value={selectedRecording || ''}
                onChange={(e) => setSelectedRecording(Number(e.target.value))}
                className="w-full px-4 py-2 border border-wood-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wood-400"
              >
                <option value="">请选择录音...</option>
                {transcribedRecordings.map((recording) => (
                  <option key={recording.id} value={recording.id}>
                    {recording.filename} ({recording.workshop})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleGenerate}
              disabled={!selectedRecording || generating}
              className="px-6 py-2 bg-wood-600 text-white rounded-lg font-medium hover:bg-wood-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {generating ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  生成中...
                </>
              ) : (
                <>
                  <FileText size={18} />
                  生成档案
                </>
              )}
            </button>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl p-4 shadow-lg border border-wood-100 max-h-[500px] overflow-y-auto scrollbar-hide">
            <h3 className="font-semibold text-wood-800 mb-4">档案列表</h3>
            {archives.length === 0 ? (
              <div className="text-center py-8 text-wood-500">
                <FileText size={48} className="mx-auto mb-4 opacity-50" />
                <p>暂无工艺档案</p>
                <p className="text-sm mt-2">上传并处理录音后可生成档案</p>
              </div>
            ) : (
              <div className="space-y-2">
                {archives.map((archive) => (
                  <button
                    key={archive.id}
                    onClick={() => setSelectedArchive(archive)}
                    className={`w-full p-4 rounded-xl text-left transition-all ${
                      selectedArchive?.id === archive.id
                        ? 'bg-wood-100 border-2 border-wood-400'
                        : 'hover:bg-wood-50 border-2 border-transparent'
                    }`}
                  >
                    <p className="font-medium text-wood-800 text-sm truncate">{archive.title}</p>
                    <p className="text-xs text-wood-500 mt-1 line-clamp-2">{archive.summary}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-wood-400">
                        {new Date(archive.generated_at).toLocaleDateString('zh-CN')}
                      </span>
                      {archive.sent_to_feiyi ? (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <CheckCircle size={12} />
                          已发送
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-yellow-600">
                          <Clock size={12} />
                          待发送
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2">
          {selectedArchive ? (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-wood-800">{selectedArchive.title}</h2>
                  <p className="text-sm text-wood-500 mt-1">
                    生成于 {new Date(selectedArchive.generated_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handlePreview(selectedArchive.id)}
                    className="p-2 text-wood-600 hover:bg-wood-100 rounded-lg transition-colors"
                    title="预览"
                  >
                    <Eye size={20} />
                  </button>
                  <button
                    onClick={() => {
                      if (!htmlContent) {
                        handlePreview(selectedArchive.id);
                      } else {
                        handleDownload(selectedArchive);
                      }
                    }}
                    className="p-2 text-wood-600 hover:bg-wood-100 rounded-lg transition-colors"
                    title="下载"
                  >
                    <Download size={20} />
                  </button>
                  <button
                    onClick={() => handleSendEmail(selectedArchive.id)}
                    disabled={sending}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    {sending ? (
                      <Loader2 className="animate-spin" size={18} />
                    ) : (
                      <Send size={18} />
                    )}
                    发送至非遗中心
                  </button>
                </div>
              </div>

              <div className="space-y-6">
                <div className="bg-wood-50 rounded-xl p-5">
                  <h3 className="font-semibold text-wood-800 mb-3">档案摘要</h3>
                  <p className="text-wood-700 leading-relaxed">{selectedArchive.summary}</p>
                </div>

                {selectedArchive.keywords && selectedArchive.keywords.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-wood-800 mb-3">关键词</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedArchive.keywords.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-parchment-100 text-wood-700 rounded-full text-sm"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedArchive.content?.key_points && (
                  <div>
                    <h3 className="font-semibold text-wood-800 mb-3">核心工艺要点</h3>
                    <ul className="space-y-2">
                      {selectedArchive.content.key_points.map((point: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-wood-700">
                          <span className="w-2 h-2 bg-wood-500 rounded-full mt-2 flex-shrink-0"></span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedArchive.content?.school_analysis && (
                  <div className="bg-parchment-50 rounded-xl p-5">
                    <h3 className="font-semibold text-wood-800 mb-3">流派分析</h3>
                    <p className="text-wood-600 text-sm mb-2">
                      <strong>涉及流派：</strong>
                      {selectedArchive.content.school_analysis.schools_involved?.join('、') || '未知'}
                    </p>
                    <p className="text-wood-700">
                      {selectedArchive.content.school_analysis.differences}
                    </p>
                  </div>
                )}

                {selectedArchive.content?.heritage_value && (
                  <div>
                    <h3 className="font-semibold text-wood-800 mb-3">传承价值评估</h3>
                    <div className="inline-block px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">
                      {selectedArchive.content.heritage_value}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100 text-center py-20 text-wood-500">
              <FileText size={48} className="mx-auto mb-4 opacity-50" />
              <p>请选择一个档案查看详情</p>
            </div>
          )}
        </div>
      </div>

      {showPreview && htmlContent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-wood-100">
              <h3 className="font-semibold text-wood-800">档案预览</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleDownload(selectedArchive!)}
                  className="flex items-center gap-2 px-4 py-2 bg-wood-600 text-white rounded-lg hover:bg-wood-700 transition-colors"
                >
                  <Download size={18} />
                  下载
                </button>
                <button
                  onClick={() => setShowPreview(false)}
                  className="px-4 py-2 text-wood-600 hover:bg-wood-100 rounded-lg transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <iframe
                srcDoc={htmlContent}
                className="w-full h-full min-h-[500px]"
                title="档案预览"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
