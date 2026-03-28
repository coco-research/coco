export interface Comment {
  id: string;
  entity_type: string;
  entity_id: string;
  parent_id: string | null;
  author: string;
  body: string;
  mentions: string; // JSON-encoded string array
  created_at: string;
  updated_at: string;
}

export interface CreateCommentPayload {
  entity_type: string;
  entity_id: string;
  parent_id?: string | null;
  author?: string;
  body: string;
  mentions?: string[];
}

export interface UpdateCommentPayload {
  body?: string;
  mentions?: string[];
}

export interface MentionOption {
  id: string;
  label: string;
  type: 'person' | 'agent';
}
