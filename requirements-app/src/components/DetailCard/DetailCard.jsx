import React, { useState } from 'react';
import { requirementsAPI } from '../../services/api';

const DetailCard = ({ 
  item, 
  projectStatus, 
  onClose, 
  onUpdate 
}) => {
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState(item.content);
  
  // Keep track of the current item content
  const [currentContent, setCurrentContent] = useState(item.content);

  const handleRegenerateWithFeedback = async () => {
    if (!feedback.trim()) {
      setMessage('Please provide feedback for regeneration');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      console.log('🔍 [DEBUG] Sending feedback request:', {
        thread_id: projectStatus.thread_id,
        indexes: [item.index],
        feedback: feedback,
        regenerate_type: item.type
      });

      const result = await requirementsAPI.regenerateWithFeedback({
        thread_id: projectStatus.thread_id,
        indexes: [item.index],
        feedback: feedback,
        regenerate_type: item.type
      });

      console.log('🔍 [DEBUG] Received response:', result);

      // Update local content immediately to show changes
      if (item.type === 'requirement' && result.requirements?.[item.index]) {
        setCurrentContent(result.requirements[item.index]);
        setEditedContent(result.requirements[item.index]);
      } else if (item.type === 'risk' && result.risks?.[item.index]) {
        setCurrentContent(result.risks[item.index]);
        setEditedContent(result.risks[item.index]);
      }

      setMessage(`${item.type} regenerated successfully! ✓`);
      setFeedback('');
      
      // Update the parent component but KEEP the dialog open
      if (onUpdate) {
        console.log('🔍 [DEBUG] Calling onUpdate with result');
        onUpdate(result);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
      
    } catch (error) {
      console.error('🔍 [DEBUG] Error regenerating with feedback:', error);
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleManualUpdate = async () => {
    if (!editedContent.trim()) {
      setMessage('Content cannot be empty');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const result = await requirementsAPI.updateItem({
        thread_id: projectStatus.thread_id,
        index: item.index,
        type: item.type,
        new_content: editedContent,
        update_related: true
      });

      // Update local content
      setCurrentContent(editedContent);
      setMessage(`${item.type} updated successfully! ✓`);
      setEditMode(false);
      
      if (onUpdate) {
        onUpdate(result);
      }

     setTimeout(() => setMessage(''), 3000);
      
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const getRelatedItems = () => {
    if (item.type === 'requirement') {
      return projectStatus.risks?.[item.index] ? [projectStatus.risks[item.index]] : [];
    } else {
      return projectStatus.requirements?.[item.index] ? [projectStatus.requirements[item.index]] : [];
    }
  };

  const relatedItems = getRelatedItems();

  return (
    <div className="detail-card-overlay" onClick={onClose}>
      <div className="detail-card" onClick={(e) => e.stopPropagation()}>
        <div className="detail-card-header">
          <h3>
            {item.type === 'requirement' ? '📋' : '⚠️'} 
            {item.type.charAt(0).toUpperCase() + item.type.slice(1)} #{item.index + 1}
          </h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="detail-card-content" style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#fff' }}>
  
          {/* Message Display - Moved to top for better visibility */}
          {message && (
            <div 
              className={`alert ${message.includes('Error') ? 'alert-error' : 'alert-success'}`}
              style={{
                padding: '12px 16px',
                marginBottom: '20px',
                borderRadius: '6px',
                backgroundColor: message.includes('Error') ? '#fee2e2' : '#d1fae5',
                color: message.includes('Error') ? '#991b1b' : '#065f46',
                border: message.includes('Error') ? '1px solid #fecaca' : '1px solid #86efac',
                fontSize: '14px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{message.includes('Error') ? '❌' : '✅'}</span>
              <span>{message}</span>
            </div>
          )}
  
          {/* Current Content */}
          <div className="content-section" style={{ marginBottom: '24px' }}>
            <h3 style={{ 
              borderBottom: '2px solid #e1e5e9', 
              paddingBottom: '8px', 
              marginBottom: '12px',
              fontWeight: '700',
              color: '#1e293b',
              fontSize: '16px'
            }}>
              Current Content
            </h3>
    
            {editMode ? (
              <div className="edit-section" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <textarea
                  className="form-input textarea edit-textarea"
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  rows={6}
                  disabled={loading}
                  style={{ 
                    border: '1px solid #cbd5e1', 
                    borderRadius: '6px', 
                    padding: '12px', 
                    fontSize: '14px', 
                    resize: 'vertical',
                    fontFamily: 'inherit',
                    lineHeight: '1.6',
                    backgroundColor: loading ? '#f8fafc' : 'white'
                  }}
                />
                <div className="edit-actions" style={{ display: 'flex', gap: '12px' }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleManualUpdate}
                    disabled={loading}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: loading ? '#94a3b8' : '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    {loading ? (
                      <>
                        <span className="spinner">⏳</span>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <span>💾</span>
                        <span>Save Changes</span>
                      </>
                    )}
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setEditMode(false);
                      setEditedContent(currentContent);
                      setMessage('');
                    }}
                    disabled={loading}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#e2e8f0',
                      color: '#475569',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: loading ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="content-display" style={{ position: 'relative' }}>
                <p style={{ 
                  marginBottom: '16px', 
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.6',
                  padding: '16px',
                  backgroundColor: '#f8fafc',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  fontSize: '14px',
                  color: '#334155'
                }}>
                  {currentContent}
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setEditMode(true);
                    setMessage('');
                  }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#467fdaff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
          
                  <span>Edit Content</span>
                </button>
              </div>
            )}
          </div>

          {/* Related Items */}
          {relatedItems.length > 0 && (
            <div className="related-section" style={{ marginBottom: '24px' }}>
              <h4 style={{ 
                borderBottom: '2px solid #e1e5e9', 
                paddingBottom: '8px', 
                marginBottom: '12px',
                fontWeight: '700',
                color: '#1e293b',
                fontSize: '15px'
              }}>
                {item.type === 'requirement' ? 'Associated Risk' : 'Related Requirement'}
              </h4>
              <div className="related-items" style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '8px',
                padding: '16px',
                backgroundColor: '#fef3c7',
                borderRadius: '6px',
                border: '1px solid #fde047'
              }}>
                {relatedItems.map((related, idx) => (
                  <p key={idx} className="related-content" style={{ 
                    margin: 0, 
                    fontSize: '14px', 
                    color: '#713f12',
                    lineHeight: '1.5'
                  }}>
                    {related}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Feedback for Regeneration */}
          <div className="feedback-section" style={{
            padding: '20px',
            backgroundColor: '#f0f9ff',
            borderRadius: '8px',
            border: '1px solid #bae6fd'
          }}>
            <h4 style={{ 
              borderBottom: '2px solid #7dd3fc', 
              paddingBottom: '8px', 
              marginBottom: '16px',
              fontWeight: '700',
              color: '#0c4a6e',
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
      
              <span>Regenerate with AI Feedback</span>
            </h4>
            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontWeight: '600',
                fontSize: '13px',
                color: '#0c4a6e'
              }}>
                What would you like to improve about this {item.type}?
              </label>
              <textarea
                className="form-input textarea"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder={`Example: "Make it more specific and add technical details" or "Simplify the language"`}
                rows={4}
                disabled={loading}
                style={{ 
                  width: '100%',
                  border: '1px solid #7dd3fc', 
                  borderRadius: '6px', 
                  padding: '12px', 
                  fontSize: '14px', 
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  backgroundColor: loading ? '#f0f9ff' : 'white'
                }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleRegenerateWithFeedback}
              disabled={loading || !feedback.trim()}
              style={{
                width: '100%',
                padding: '12px 20px',
                backgroundColor: (loading || !feedback.trim()) ? '#94a3b8' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: (loading || !feedback.trim()) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              {loading ? (
                <>
                  <span className="spinner">⏳</span>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>✨</span>
                  <span>Regenerate with Feedback</span>
                </>
              )}
            </button>
            {!feedback.trim() && !loading && (
              <p style={{
                marginTop: '8px',
                fontSize: '12px',
                color: '#64748b',
                fontStyle: 'italic',
                textAlign: 'center'
              }}>
                💡 Tip: Provide clear feedback to get better results
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailCard;