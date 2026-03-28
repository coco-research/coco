import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MessageSquare, ChevronDown, Reply, Pencil, Trash2, Check, X } from 'lucide-react';
import { apiFetch, apiPost, apiPatch, apiDelete } from '../../lib/api';
import { cn, timeAgo } from '../../lib/utils';
import { CommentInput } from './CommentInput';
import type { Comment, MentionOption } from '../../types/comments';

interface CommentThreadProps {
  entityType: string;
  entityId: string;
}

interface Agent {
  id: string;
  name: string;
}

interface PeopleMap {
  [key: string]: { name?: string; email?: string };
}

function parseMentions(raw: string): string[] {
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

/** Highlight @mentions in comment body */
function renderBody(body: string) {
  const parts = body.split(/(@[\w\s-]+?)(?=\s@|\s[^@]|$)/g);
  return parts.map((part, i) => {
    if (part.startsWith('@') && part.length > 1) {
      return (
        <span
          key={i}
          className="inline-block bg-accent/20 text-accent rounded px-1 text-xs font-medium"
        >
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function authorInitial(author: string): string {
  return (author[0] ?? '?').toUpperCase();
}

function authorColor(author: string): string {
  if (author === 'user') return 'bg-info/20 text-info';
  return 'bg-accent/20 text-accent';
}

interface CommentItemProps {
  comment: Comment;
  replies: Comment[];
  mentionOptions: MentionOption[];
  onDelete: (id: string) => void;
  onEdit: (id: string, body: string, mentions: string[]) => void;
  onReply: (parentId: string, body: string, mentions: string[]) => void;
  isEditPending: boolean;
  isReplyPending: boolean;
}

function CommentItem({
  comment,
  replies,
  mentionOptions,
  onDelete,
  onEdit,
  onReply,
  isEditPending,
  isReplyPending,
}: CommentItemProps) {
  const [showReply, setShowReply] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(comment.body);

  function handleEditSave() {
    if (!editText.trim()) return;
    // Extract mentions from edited text
    const re = /@([\w\s-]+?)(?=\s@|\s[^@]|$)/g;
    const found: string[] = [];
    let m: RegExpExecArray | null;
    while ((m = re.exec(editText)) !== null) {
      const name = m[1].trim();
      const opt = mentionOptions.find(
        (o) => o.label.toLowerCase() === name.toLowerCase(),
      );
      if (opt) found.push(opt.id);
    }
    onEdit(comment.id, editText, [...new Set(found)]);
    setEditing(false);
  }

  return (
    <div className="group">
      <div className="flex gap-2">
        {/* Avatar */}
        <div
          className={cn(
            'w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold shrink-0 mt-0.5',
            authorColor(comment.author),
          )}
        >
          {authorInitial(comment.author)}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-baseline gap-2">
            <span className="text-xs font-medium text-foreground capitalize">
              {comment.author}
            </span>
            <span className="text-[10px] text-muted-foreground">
              {timeAgo(comment.created_at)}
            </span>
            {comment.updated_at !== comment.created_at && (
              <span className="text-[10px] text-muted-foreground italic">edited</span>
            )}
          </div>

          {/* Body */}
          {editing ? (
            <div className="mt-1">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={2}
                className="w-full bg-transparent border border-border rounded-lg px-2 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent/30 resize-none"
              />
              <div className="flex gap-1 mt-1">
                <button
                  onClick={handleEditSave}
                  disabled={isEditPending}
                  className="p-1 rounded hover:bg-accent/20 text-success"
                >
                  <Check className="h-3 w-3" />
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    setEditText(comment.body);
                  }}
                  className="p-1 rounded hover:bg-accent/20 text-muted-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-foreground/90 leading-relaxed mt-0.5 whitespace-pre-wrap">
              {renderBody(comment.body)}
            </p>
          )}

          {/* Actions */}
          {!editing && (
            <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => setShowReply(!showReply)}
                className="flex items-center gap-1 px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground rounded hover:bg-accent/20 transition-colors"
              >
                <Reply className="h-3 w-3" />
                Reply
              </button>
              {comment.author === 'user' && (
                <>
                  <button
                    onClick={() => {
                      setEditing(true);
                      setEditText(comment.body);
                    }}
                    className="flex items-center gap-1 px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground rounded hover:bg-accent/20 transition-colors"
                  >
                    <Pencil className="h-3 w-3" />
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(comment.id)}
                    className="flex items-center gap-1 px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-destructive rounded hover:bg-destructive/10 transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    Delete
                  </button>
                </>
              )}
            </div>
          )}

          {/* Reply input */}
          {showReply && (
            <div className="mt-2">
              <CommentInput
                mentionOptions={mentionOptions}
                onSubmit={(body, mentions) => {
                  onReply(comment.id, body, mentions);
                  setShowReply(false);
                }}
                placeholder="Write a reply..."
                autoFocus
                isPending={isReplyPending}
              />
            </div>
          )}

          {/* Replies */}
          {replies.length > 0 && (
            <div className="mt-2 pl-2 border-l border-border/50 space-y-3">
              {replies.map((reply) => (
                <CommentItem
                  key={reply.id}
                  comment={reply}
                  replies={[]}
                  mentionOptions={mentionOptions}
                  onDelete={onDelete}
                  onEdit={onEdit}
                  onReply={onReply}
                  isEditPending={isEditPending}
                  isReplyPending={isReplyPending}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function CommentThread({ entityType, entityId }: CommentThreadProps) {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const queryKey = ['comments', entityType, entityId];

  const { data: comments = [] } = useQuery({
    queryKey,
    queryFn: () =>
      apiFetch<Comment[]>(`/comments?entity_type=${entityType}&entity_id=${entityId}`),
    enabled: expanded,
  });

  // Fetch mentionable entities
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => apiFetch<Agent[]>('/agents'),
    enabled: expanded,
  });

  const { data: people = {} } = useQuery({
    queryKey: ['brain-people'],
    queryFn: () => apiFetch<PeopleMap>('/brain/people'),
    enabled: expanded,
  });

  const mentionOptions = useMemo<MentionOption[]>(() => {
    const opts: MentionOption[] = [];
    for (const agent of agents) {
      opts.push({ id: agent.id, label: agent.name, type: 'agent' });
    }
    for (const [key, person] of Object.entries(people)) {
      const label = person.name || key;
      opts.push({ id: key, label, type: 'person' });
    }
    return opts;
  }, [agents, people]);

  // Organize into threads
  const { roots, repliesByParent } = useMemo(() => {
    const r: Comment[] = [];
    const rp: Record<string, Comment[]> = {};
    for (const c of comments) {
      if (!c.parent_id) {
        r.push(c);
      } else {
        if (!rp[c.parent_id]) rp[c.parent_id] = [];
        rp[c.parent_id].push(c);
      }
    }
    return { roots: r, repliesByParent: rp };
  }, [comments]);

  const createMutation = useMutation({
    mutationFn: (payload: {
      body: string;
      mentions: string[];
      parent_id?: string;
    }) =>
      apiPost('/comments', {
        entity_type: entityType,
        entity_id: entityId,
        body: payload.body,
        mentions: payload.mentions,
        parent_id: payload.parent_id ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const editMutation = useMutation({
    mutationFn: (payload: { id: string; body: string; mentions: string[] }) =>
      apiPatch(`/comments/${payload.id}`, {
        body: payload.body,
        mentions: payload.mentions,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiDelete(`/comments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const commentCount = comments.length;

  return (
    <div className="border-t border-border pt-4">
      {/* Toggle header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full"
      >
        <MessageSquare className="h-4 w-4" />
        <span className="font-medium">
          Comments{commentCount > 0 ? ` (${commentCount})` : ''}
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 ml-auto transition-transform',
            expanded && 'rotate-180',
          )}
        />
      </button>

      {expanded && (
        <div className="mt-3 space-y-4">
          {/* Comment list */}
          {roots.length === 0 && (
            <p className="text-xs text-muted-foreground/60 italic">
              No comments yet. Start the conversation.
            </p>
          )}

          <div className="space-y-4">
            {roots.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                replies={repliesByParent[comment.id] ?? []}
                mentionOptions={mentionOptions}
                onDelete={(id) => deleteMutation.mutate(id)}
                onEdit={(id, body, mentions) =>
                  editMutation.mutate({ id, body, mentions })
                }
                onReply={(parentId, body, mentions) =>
                  createMutation.mutate({ body, mentions, parent_id: parentId })
                }
                isEditPending={editMutation.isPending}
                isReplyPending={createMutation.isPending}
              />
            ))}
          </div>

          {/* New comment input */}
          <CommentInput
            mentionOptions={mentionOptions}
            onSubmit={(body, mentions) =>
              createMutation.mutate({ body, mentions })
            }
            isPending={createMutation.isPending}
          />
        </div>
      )}
    </div>
  );
}
