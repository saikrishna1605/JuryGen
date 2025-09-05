import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  Reply,
  Edit3,
  Trash2,
  Check,
  MoreVertical,
  User,
  Clock,
} from 'lucide-react';
import {
  sharingService,
  CollaborationComment,
} from '../../services/sharingService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { AccessibleMenu, AccessibleMenuItem } from '../accessibility/KeyboardNavigation';
import { cn } from '../../utils';

interface CollaborationCommentsProps {
  shareId: string;
  clauseId?: string;
  position?: { x: number; y: number };
  className?: string;
}

interface CommentFormData {
  content: string;
  parentId?: string;
}

export const CollaborationComments: React.FC<CollaborationCommentsProps> = ({
  shareId,
  clauseId,
  position,
  className,
}) => {
  const [comments, setComments] = useState<CollaborationComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const commentInputRef = useRef<HTMLTextAreaElement>(null);
  const { announceSuccess, announceError } = useAriaAnnouncements();

  // Load comments
  useEffect(() => {
    loadComments();
  }, [shareId]);

  // Focus comment input when replying
  useEffect(() => {
    if (replyingTo && commentInputRef.current) {
      commentInputRef.current.focus();
    }
  }, [replyingTo]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const allComments = await sharingService.getComments(shareId);
      
      // Filter comments by clause if specified
      const filteredComments = clauseId 
        ? allComments.filter(comment => comment.clauseId === clauseId)
        : allComments.filter(comment => !comment.clauseId);
      
      setComments(filteredComments);
    } catch (error) {
      announceError('Failed to load comments');
      console.error('Error loading comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async (formData: CommentFormData) => {
    if (!formData.content.trim()) return;

    setIsSubmitting(true);
    try {
      const newCommentData = await sharingService.addComment(
        shareId,
        formData.content,
        clauseId,
        position,
        formData.parentId
      );

      // Add to comments list
      if (formData.parentId) {
        // Add as reply
        setComments(prev => prev.map(comment => {
          if (comment.id === formData.parentId) {
            return {
              ...comment,
              replies: [...comment.replies, newCommentData],
            };
          }
          return comment;
        }));
      } else {
        // Add as new top-level comment
        setComments(prev => [newCommentData, ...prev]);
      }

      // Reset form
      setNewComment('');
      setReplyingTo(null);
      
      announceSuccess('Comment added successfully');
    } catch (error) {
      announceError('Failed to add comment');
      console.error('Error adding comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditComment = async (commentId: string, content: string) => {
    if (!content.trim()) return;

    try {
      const updatedComment = await sharingService.updateComment(commentId, content);
      
      // Update comment in list
      setComments(prev => prev.map(comment => {
        if (comment.id === commentId) {
          return updatedComment;
        }
        // Check replies
        if (comment.replies.some(reply => reply.id === commentId)) {
          return {
            ...comment,
            replies: comment.replies.map(reply => 
              reply.id === commentId ? updatedComment : reply
            ),
          };
        }
        return comment;
      }));

      setEditingComment(null);
      setEditContent('');
      announceSuccess('Comment updated successfully');
    } catch (error) {
      announceError('Failed to update comment');
      console.error('Error updating comment:', error);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    try {
      await sharingService.deleteComment(commentId);
      
      // Remove comment from list
      setComments(prev => prev.filter(comment => {
        if (comment.id === commentId) return false;
        
        // Remove from replies
        comment.replies = comment.replies.filter(reply => reply.id !== commentId);
        return true;
      }));

      announceSuccess('Comment deleted successfully');
    } catch (error) {
      announceError('Failed to delete comment');
      console.error('Error deleting comment:', error);
    }
  };

  const handleResolveComment = async (commentId: string, resolved: boolean) => {
    try {
      const updatedComment = await sharingService.resolveComment(commentId, resolved);
      
      // Update comment in list
      setComments(prev => prev.map(comment => 
        comment.id === commentId ? updatedComment : comment
      ));

      announceSuccess(resolved ? 'Comment resolved' : 'Comment reopened');
    } catch (error) {
      announceError('Failed to update comment status');
      console.error('Error resolving comment:', error);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const minutes = Math.floor(diffInHours * 60);
      return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
      const hours = Math.floor(diffInHours);
      return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 168) { // 7 days
      const days = Math.floor(diffInHours / 24);
      return `${days} day${days !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const CommentItem: React.FC<{ 
    comment: CollaborationComment; 
    isReply?: boolean;
    canReply?: boolean;
  }> = ({ comment, isReply = false, canReply = true }) => {
    const isEditing = editingComment === comment.id;

    return (
      <div className={cn(
        'border border-gray-200 rounded-lg p-4',
        isReply && 'ml-6 mt-2',
        comment.isResolved && 'bg-green-50 border-green-200'
      )}>
        {/* Comment Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600" />
            </div>
            <div>
              <div className="font-medium text-sm">{comment.userName}</div>
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                <span>{formatDate(comment.createdAt)}</span>
                {comment.isResolved && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
                    Resolved
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Comment Actions */}
          <AccessibleMenu
            trigger={
              <button
                className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
                aria-label="Comment options"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            }
            placement="bottom-end"
          >
            <AccessibleMenuItem onClick={() => {
              setEditingComment(comment.id);
              setEditContent(comment.content);
            }}>
              <Edit3 className="w-4 h-4 mr-2" />
              Edit
            </AccessibleMenuItem>
            
            <AccessibleMenuItem onClick={() => handleResolveComment(comment.id, !comment.isResolved)}>
              <Check className="w-4 h-4 mr-2" />
              {comment.isResolved ? 'Reopen' : 'Resolve'}
            </AccessibleMenuItem>
            
            <AccessibleMenuItem onClick={() => handleDeleteComment(comment.id)}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </AccessibleMenuItem>
          </AccessibleMenu>
        </div>

        {/* Comment Content */}
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              placeholder="Edit your comment..."
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setEditingComment(null);
                  setEditContent('');
                }}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={() => handleEditComment(comment.id, editContent)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Save
              </button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">
            {comment.content}
          </div>
        )}

        {/* Reply Button */}
        {!isReply && canReply && !isEditing && (
          <button
            onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
            className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
          >
            <Reply className="w-4 h-4" />
            <span>Reply</span>
          </button>
        )}

        {/* Reply Form */}
        {replyingTo === comment.id && (
          <div className="mt-3 space-y-2">
            <textarea
              ref={commentInputRef}
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              placeholder="Write a reply..."
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setReplyingTo(null);
                  setNewComment('');
                }}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSubmitComment({ content: newComment, parentId: comment.id })}
                disabled={isSubmitting || !newComment.trim()}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                <span>Reply</span>
              </button>
            </div>
          </div>
        )}

        {/* Replies */}
        {comment.replies.length > 0 && (
          <div className="mt-4 space-y-2">
            {comment.replies.map((reply) => (
              <CommentItem
                key={reply.id}
                comment={reply}
                isReply={true}
                canReply={false}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-4', className)}>
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-600">Loading comments...</span>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center space-x-2">
        <MessageSquare className="w-5 h-5 text-gray-600" />
        <h3 className="font-medium text-gray-900">
          Comments {clauseId && '(Clause-specific)'}
        </h3>
        <span className="text-sm text-gray-500">({comments.length})</span>
      </div>

      {/* New Comment Form */}
      {!replyingTo && (
        <div className="space-y-2">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            placeholder="Add a comment..."
          />
          <div className="flex justify-end">
            <button
              onClick={() => handleSubmitComment({ content: newComment })}
              disabled={isSubmitting || !newComment.trim()}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
              <span>Comment</span>
            </button>
          </div>
        </div>
      )}

      {/* Comments List */}
      <div className="space-y-4">
        {comments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No comments yet. Be the first to add one!
          </div>
        ) : (
          comments.map((comment) => (
            <CommentItem key={comment.id} comment={comment} />
          ))
        )}
      </div>
    </div>
  );
};

export default CollaborationComments;