import React from 'react';
import { Tag, AlertCircle, CheckCircle2, ArrowUpRight } from 'lucide-react';
import Badge from '../../../components/ui/Badge';
import './WeaknessDistributionCard.css';

/**
 * Visual breakdown of recurring grammatical & pronunciation weakness tags.
 * @param {Object} weaknessFrequency - Key-value pair of tag names to occurrence counts
 */
export default function WeaknessDistributionCard({ weaknessFrequency = {} }) {
  const entries = Object.entries(weaknessFrequency || {}).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return (
      <div className="weakness-card empty">
        <div className="weakness-header">
          <div className="weakness-title">
            <Tag size={18} />
            <span>Target Weakness Focus</span>
          </div>
        </div>
        <div className="weakness-empty-body">
          <CheckCircle2 size={32} className="empty-check-icon" />
          <p>No recurring weakness patterns identified in this window. Outstanding linguistic accuracy!</p>
        </div>
      </div>
    );
  }

  const maxCount = Math.max(...entries.map(([, count]) => count), 1);
  const totalOccurrences = entries.reduce((acc, [, count]) => acc + count, 0);

  return (
    <div className="weakness-card">
      <div className="weakness-header">
        <div className="weakness-title">
          <Tag size={18} />
          <span>Target Weakness Distribution</span>
        </div>
        <span className="total-occurrences-badge">
          {totalOccurrences} total areas flagged
        </span>
      </div>

      <p className="weakness-subtitle">
        Recurring linguistic patterns identified by the AI coach. Focus on these areas during your upcoming practice turns.
      </p>

      <div className="weakness-bars-list">
        {entries.map(([tag, count]) => {
          const percent = Math.min(100, Math.round((count / maxCount) * 100));
          return (
            <div key={tag} className="weakness-bar-item">
              <div className="bar-label-row">
                <span className="tag-name">{tag}</span>
                <span className="tag-count">
                  <strong>{count}</strong> {count === 1 ? 'flag' : 'flags'}
                </span>
              </div>

              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
