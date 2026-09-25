export interface Craftsman {
  id: number;
  name: string;
  school: string;
  generation?: number;
  bio?: string;
  avatar?: string;
  contact?: string;
  created_at: string;
}

export interface Message {
  id: number;
  content: string;
  craftsman_id?: number;
  timestamp: string;
  message_type: string;
  craftsman?: Craftsman;
}

export interface AudioRecording {
  id: number;
  filename: string;
  original_path: string;
  processed_path?: string;
  duration?: number;
  workshop?: string;
  recorded_at: string;
  status: string;
}

export interface Transcript {
  id: number;
  recording_id: number;
  craftsman_id?: number;
  content: string;
  start_time?: number;
  end_time?: number;
  language: string;
  created_at: string;
  speaker_label?: string;
  predicted_school?: string;
  confidence?: number;
}

export interface SpeakerDiarization {
  id: number;
  recording_id: number;
  speaker_label: string;
  start_time: number;
  end_time: number;
  predicted_school?: string;
  confidence?: number;
}

export interface CraftArchive {
  id: number;
  title: string;
  summary: string;
  content?: any;
  keywords?: string[];
  related_transcript_ids?: number[];
  generated_at: string;
  sent_to_feiyi: number;
  sent_at?: string;
}

export interface WoodMaterial {
  id: number;
  name: string;
  scientific_name?: string;
  origin?: string;
  description?: string;
  texture_image?: string;
  suitable_parts?: string[];
  properties?: {
    density?: number;
    hardness?: string;
    elasticity?: string;
    durability?: string;
  };
  traditional_usage?: string;
}

export interface BowPart {
  id: number;
  name: string;
  traditional_name?: string;
  description?: string;
  diagram_coords?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  materials?: string[];
  crafting_steps?: {
    step: number;
    description: string;
  }[];
}
