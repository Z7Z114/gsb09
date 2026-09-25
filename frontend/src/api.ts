import axios from 'axios';
import {
  Craftsman,
  Message,
  AudioRecording,
  Transcript,
  CraftArchive,
  WoodMaterial,
  BowPart,
  SpeakerDiarization
} from './types';

const API_BASE = '/api';

export const api = {
  craftsmen: {
    list: (): Promise<Craftsman[]> =>
      axios.get(`${API_BASE}/craftsmen`).then(res => res.data),
    get: (id: number): Promise<Craftsman> =>
      axios.get(`${API_BASE}/craftsmen/${id}`).then(res => res.data),
    create: (data: Partial<Craftsman>): Promise<Craftsman> =>
      axios.post(`${API_BASE}/craftsmen`, data).then(res => res.data),
  },

  messages: {
    list: (): Promise<Message[]> =>
      axios.get(`${API_BASE}/messages`).then(res => res.data),
    create: (data: Partial<Message>): Promise<Message> =>
      axios.post(`${API_BASE}/messages`, data).then(res => res.data),
  },

  audio: {
    list: (): Promise<AudioRecording[]> =>
      axios.get(`${API_BASE}/audio/recordings`).then(res => res.data),
    get: (id: number): Promise<AudioRecording> =>
      axios.get(`${API_BASE}/audio/recordings/${id}`).then(res => res.data),
    upload: (file: File, workshop: string): Promise<any> => {
      const formData = new FormData();
      formData.append('file', file);
      return axios.post(`${API_BASE}/audio/upload?workshop=${workshop}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then(res => res.data);
    },
    process: (id: number): Promise<any> =>
      axios.post(`${API_BASE}/audio/process/${id}`).then(res => res.data),
    getTranscripts: (id: number): Promise<Transcript[]> =>
      axios.get(`${API_BASE}/audio/recordings/${id}/transcripts`).then(res => res.data),
    getDiarization: (id: number): Promise<SpeakerDiarization[]> =>
      axios.get(`${API_BASE}/audio/recordings/${id}/diarization`).then(res => res.data),
  },

  archives: {
    list: (): Promise<CraftArchive[]> =>
      axios.get(`${API_BASE}/archives`).then(res => res.data),
    get: (id: number): Promise<CraftArchive> =>
      axios.get(`${API_BASE}/archives/${id}`).then(res => res.data),
    generate: (recordingId: number): Promise<any> =>
      axios.post(`${API_BASE}/archives/generate/${recordingId}`).then(res => res.data),
    getHtml: (id: number): Promise<{ archive_id: number; html_content: string }> =>
      axios.get(`${API_BASE}/archives/${id}/html`).then(res => res.data),
    sendEmail: (data: { archive_id: number; recipient_email?: string; custom_message?: string }): Promise<any> =>
      axios.post(`${API_BASE}/archives/send-email`, data).then(res => res.data),
  },

  materials: {
    listWoods: (): Promise<WoodMaterial[]> =>
      axios.get(`${API_BASE}/materials/woods`).then(res => res.data),
    getWood: (id: number): Promise<WoodMaterial> =>
      axios.get(`${API_BASE}/materials/woods/${id}`).then(res => res.data),
    listBowParts: (): Promise<BowPart[]> =>
      axios.get(`${API_BASE}/materials/bow-parts`).then(res => res.data),
    getBowPart: (id: number): Promise<BowPart> =>
      axios.get(`${API_BASE}/materials/bow-parts/${id}`).then(res => res.data),
    seedData: (): Promise<any> =>
      axios.post(`${API_BASE}/materials/seed-data`).then(res => res.data),
  },
};
