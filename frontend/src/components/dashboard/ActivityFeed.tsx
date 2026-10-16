import React from 'react';
import type { RunSummary } from '../../api/types';
import './ActivityFeed.css';

interface ActivityFeedProps {
  runs: RunSummary[];
  isLoading?: boolean;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ runs, isLoading }) => {
  if (isLoading) {
    return (
      <div className="activity-feed-card">
        <div className="activity-feed-header">
          <span className="activity-feed-title">Recent Activity</span>
        </div>
        <div className="chart-empty-state">
          <span>Loading activity log...</span>
        </div>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="activity-feed-card">
        <div className="activity-feed-header">
          <span className="activity-feed-title">Recent Activity</span>
        </div>
        <div className="chart-empty-state">
          <span>No platform events logged yet.</span>
        </div>
      </div>
    );
  }

  // Derive meaningful events from actual run records
  const events = runs.slice(0, 5).map((r) => {
    const isSuccess = r.status.toLowerCase() === 'completed';
    const scoreStr =
      r.pass_rate !== null && r.pass_rate !== undefined
        ? `with ${(Number(r.pass_rate) * 100).toFixed(1)}% pass rate`
        : '';

    return {
      id: r.run_id,
      text: `Evaluation run "${r.name}" (${r.run_id.substring(0, 12)}) ${isSuccess ? 'completed successfully' : r.status} ${scoreStr} (${r.completed_cases}/${r.total_cases} cases).`,
      time: r.completed_at || r.started_at || 'Just now',
    };
  });

  return (
    <div className="activity-feed-card">
      <div className="activity-feed-header">
        <span className="activity-feed-title">Recent Activity</span>
        <span className="text-label">Platform Events</span>
      </div>

      <div className="activity-list">
        {events.map((e) => (
          <div key={e.id} className="activity-item">
            <span className="activity-dot" aria-hidden="true" />
            <div className="activity-content">
              <div className="activity-desc">{e.text}</div>
              <div className="activity-time">
                {e.time !== 'Just now' ? new Date(e.time).toLocaleString() : e.time}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
