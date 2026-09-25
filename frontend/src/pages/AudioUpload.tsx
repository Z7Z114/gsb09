import { useState, useEffect } from 'react';
import { Upload, Play, FileAudio, Clock, CheckCircle, AlertCircle, Loader2, Mic } from 'lucide-react';
import { api } from '../api';
import { AudioRecording, Transcript } from '../types';

export default function AudioUpload() {
  const [recordings, setRecordings] = useState<AudioRecording[]>([]);
  const [selectedRecording, setSelectedRecording] = useState<AudioRecording | null>(null);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [workshop, setWorkshop] = useState('聚元号弓箭铺');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecordings();
  }, []);

  useEffect(() => {
    if (selectedRecording) {
      loadTranscripts(selectedRecording.id);
    }
  }, [selectedRecording]);

  const loadRecordings = async () => {
    try {
      const data = await api.audio.list();
      setRecordings(data);
      if (data.length > 0) {
        setSelectedRecording(data[0]);
      }
    } catch (error) {
      console.error('Failed to load recordings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTranscripts = async (recordingId: number) => {
    try {
      const data = await api.audio.getTranscripts(recordingId);
      setTranscripts(data);
    } catch (error) {
      console.error('Failed to load transcripts:', error);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const result = await api.audio.upload(file, workshop);
      await loadRecordings();
      setFile(null);
    } catch (error) {
      console.error('Failed to upload audio:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async (recordingId: number) => {
    setProcessing(recordingId);
    try {
      await api.audio.process(recordingId);
      setTimeout(async () => {
        await loadRecordings();
        setProcessing(null);
      }, 2000);
    } catch (error) {
      console.error('Failed to process audio:', error);
      setProcessing(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <FileAudio className="text-blue-500" size={18} />;
      case 'processing':
        return <Loader2 className="text-yellow-500 animate-spin" size={18} />;
      case 'processed':
        return <Play className="text-purple-500" size={18} />;
      case 'transcribed':
        return <CheckCircle className="text-green-500" size={18} />;
      case 'failed':
        return <AlertCircle className="text-red-500" size={18} />;
      default:
        return <FileAudio className="text-gray-500" size={18} />;
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      'uploaded': '已上传',
      'processing': '处理中',
      'processed': '已处理',
      'transcribed': '已转写',
      'failed': '处理失败'
    };
    return statusMap[status] || status;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSchoolColor = (school?: string) => {
    const colors: Record<string, string> = {
      '汉族传统弓': 'bg-amber-100 text-amber-800',
      '蒙古族角弓': 'bg-blue-100 text-blue-800',
      '满族清弓': 'bg-purple-100 text-purple-800',
      '藏族牛角弓': 'bg-cyan-100 text-cyan-800',
      '彝族竹弓': 'bg-green-100 text-green-800',
    };
    return colors[school || ''] || 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-wood-800">音频处理</h1>
          <p className="text-wood-600 mt-1">上传会议录音，自动转写口传知识</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
            <h3 className="font-semibold text-wood-800 mb-4 flex items-center gap-2">
              <Upload size={18} />
              上传录音
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-wood-700 mb-2">木工坊名称</label>
                <input
                  type="text"
                  value={workshop}
                  onChange={(e) => setWorkshop(e.target.value)}
                  className="w-full px-4 py-2 border border-wood-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wood-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-wood-700 mb-2">音频文件</label>
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-wood-300 rounded-xl cursor-pointer hover:bg-wood-50 transition-colors">
                  <Mic className="text-wood-400 mb-2" size={32} />
                  <span className="text-sm text-wood-600">
                    {file ? file.name : '点击或拖拽上传音频文件'}
                  </span>
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
              </div>
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full py-3 bg-wood-600 text-white rounded-xl font-medium hover:bg-wood-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    上传中...
                  </>
                ) : (
                  <>
                    <Upload size={18} />
                    上传录音
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-4 shadow-lg border border-wood-100 max-h-[400px] overflow-y-auto scrollbar-hide">
            <h3 className="font-semibold text-wood-800 mb-4">录音列表</h3>
            <div className="space-y-2">
              {recordings.map((recording) => (
                <button
                  key={recording.id}
                  onClick={() => setSelectedRecording(recording)}
                  className={`w-full p-3 rounded-xl text-left transition-all ${
                    selectedRecording?.id === recording.id
                      ? 'bg-wood-100 border-2 border-wood-400'
                      : 'hover:bg-wood-50 border-2 border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-wood-800 text-sm truncate max-w-[150px]">
                      {recording.filename}
                    </span>
                    {getStatusIcon(recording.status)}
                  </div>
                  <div className="flex items-center justify-between text-xs text-wood-500">
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {formatDuration(recording.duration)}
                    </span>
                    <span>{getStatusText(recording.status)}</span>
                  </div>
                  {recording.status === 'uploaded' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleProcess(recording.id);
                      }}
                      disabled={processing === recording.id}
                      className="mt-2 w-full py-2 bg-green-500 text-white rounded-lg text-xs font-medium hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                      {processing === recording.id ? (
                        <>
                          <Loader2 className="animate-spin" size={14} />
                          处理中...
                        </>
                      ) : (
                        '开始处理'
                      )}
                    </button>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          {selectedRecording ? (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-wood-800">{selectedRecording.filename}</h2>
                  <p className="text-sm text-wood-500">
                    {selectedRecording.workshop} · {formatDuration(selectedRecording.duration)} · {new Date(selectedRecording.recorded_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(selectedRecording.status)}
                  <span className="text-sm font-medium text-wood-600">{getStatusText(selectedRecording.status)}</span>
                </div>
              </div>

              {transcripts.length > 0 ? (
                <div className="space-y-4 max-h-[500px] overflow-y-auto scrollbar-hide">
                  <h3 className="font-semibold text-wood-800 flex items-center gap-2">
                    <FileAudio size={18} />
                    转写结果
                  </h3>
                  <div className="space-y-3">
                    {transcripts.map((transcript, index) => (
                      <div
                        key={transcript.id || index}
                        className="p-4 bg-wood-50 rounded-xl border-l-4 border-wood-400"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getSchoolColor(transcript.predicted_school)}`}>
                              {transcript.predicted_school || transcript.speaker_label}
                            </span>
                            {transcript.confidence !== undefined && (
                              <span className="text-xs text-wood-500">
                                置信度: {(transcript.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-wood-400">
                            {formatDuration(transcript.start_time)} - {formatDuration(transcript.end_time)}
                          </span>
                        </div>
                        <p className="text-wood-700 leading-relaxed">{transcript.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-20 text-wood-500">
                  <FileAudio size={48} className="mx-auto mb-4 opacity-50" />
                  <p>暂无转写结果</p>
                  {selectedRecording.status === 'uploaded' && (
                    <p className="text-sm mt-2">请点击"开始处理"按钮进行音频转写</p>
                  )}
                  {selectedRecording.status === 'processing' && (
                    <div className="flex items-center justify-center gap-2 mt-4">
                      <Loader2 className="animate-spin" size={18} />
                      <span>正在处理音频，请稍候...</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-wood-100 text-center py-20 text-wood-500">
              <Mic size={48} className="mx-auto mb-4 opacity-50" />
              <p>请选择一个录音文件查看详情</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
