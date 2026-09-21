/**
 * AnalyticsView.tsx — RAKSHYA VISION Phase 8
 * Safety Metrics & Incident Distribution Analytics.
 * Strict No-Fake-Data: Calculates real distributions from actual database records.
 * Renders explicit 'NO HISTORICAL DATA AVAILABLE' if database has zero records.
 */

import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Alert, Incident, RiskSummary } from '../types';

interface AnalyticsViewProps {
  alerts: Alert[];
  incidents: Incident[];
  summary: RiskSummary | null;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ alerts, incidents, summary }) => {
  const hasData = alerts.length > 0 || incidents.length > 0;

  // Real calculations
  const totalAlerts = alerts.length;
  const criticalAlerts = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highAlerts = alerts.filter((a) => a.severity === 'HIGH').length;
  const mediumAlerts = alerts.filter((a) => a.severity === 'MEDIUM').length;
  const lowAlerts = alerts.filter((a) => a.severity === 'LOW').length;

  const resolvedAlerts = alerts.filter((a) => a.status === 'RESOLVED').length;
  const ackAlerts = alerts.filter((a) => a.status === 'ACKNOWLEDGED').length;
  const activeAlerts = alerts.filter((a) => a.status === 'ACTIVE').length;
  const dismissedAlerts = alerts.filter((a) => a.status === 'DISMISSED').length;

  // Event type distribution
  const eventCounts: Record<string, number> = {};
  alerts.forEach((a) => {
    eventCounts[a.event_type] = (eventCounts[a.event_type] || 0) + 1;
  });

  // Camera distribution
  const cameraCounts: Record<string, number> = {};
  alerts.forEach((a) => {
    cameraCounts[a.camera_id] = (cameraCounts[a.camera_id] || 0) + 1;
  });

  const resolutionRate = totalAlerts > 0 ? ((resolvedAlerts / totalAlerts) * 100).toFixed(1) : '0.0';

  if (!hasData) {
    return (
      <div className="analytics-view-container">
        <div className="view-title-bar">
          <div>
            <h2 className="view-heading">
              <BarChart3 size={22} /> Safety Analytics & Risk Trends
            </h2>
            <p className="view-subheading">
              Historical distribution of safety violations, incident escalations, and resolution performance
            </p>
          </div>
        </div>

        <div className="analytics-empty-state">
          <BarChart3 size={56} className="empty-icon text-muted" />
          <h3 className="empty-title">NO HISTORICAL DATA AVAILABLE</h3>
          <p className="empty-subtitle">
            The database currently contains zero recorded alerts or incidents. As the computer vision
            pipeline identifies safety violations or thermal hazards, verified analytical metrics will populate here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-view-container">
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <BarChart3 size={22} /> Safety Analytics & Risk Trends
          </h2>
          <p className="view-subheading">
            Verified analytical metrics calculated directly from {totalAlerts} safety alerts and {incidents.length} incidents
          </p>
        </div>
      </div>

      {/* Analytics KPI Row */}
      <div className="analytics-kpi-row">
        <div className="analytics-card">
          <span className="card-label">Total Recorded Alerts</span>
          <span className="card-num font-mono">{totalAlerts}</span>
          <span className="card-sub text-muted">Across all configured cameras</span>
        </div>
        <div className="analytics-card">
          <span className="card-label">Resolution Rate</span>
          <span className="card-num text-success font-mono">{resolutionRate}%</span>
          <span className="card-sub text-muted">{resolvedAlerts} of {totalAlerts} resolved</span>
        </div>
        <div className="analytics-card">
          <span className="card-label">Critical Threat Share</span>
          <span className="card-num text-error font-mono">
            {totalAlerts > 0 ? ((criticalAlerts / totalAlerts) * 100).toFixed(1) : 0}%
          </span>
          <span className="card-sub text-muted">{criticalAlerts} critical incidents</span>
        </div>
        <div className="analytics-card">
          <span className="card-label">Open Incidents</span>
          <span className="card-num text-accent font-mono">{summary?.open_incidents ?? 0}</span>
          <span className="card-sub text-muted">Requiring safety officer action</span>
        </div>
      </div>

      {/* Distribution Charts Grid */}
      <div className="analytics-charts-grid">
        {/* Severity Distribution */}
        <div className="chart-card">
          <h4 className="chart-title">Alerts by Severity</h4>
          <div className="bar-chart-wrap">
            <div className="bar-item">
              <div className="bar-label-row">
                <span>Critical</span>
                <span className="font-mono">{criticalAlerts} ({totalAlerts > 0 ? Math.round((criticalAlerts / totalAlerts) * 100) : 0}%)</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-critical"
                  style={{ width: `${totalAlerts > 0 ? (criticalAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>High</span>
                <span className="font-mono">{highAlerts} ({totalAlerts > 0 ? Math.round((highAlerts / totalAlerts) * 100) : 0}%)</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-high"
                  style={{ width: `${totalAlerts > 0 ? (highAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>Medium</span>
                <span className="font-mono">{mediumAlerts} ({totalAlerts > 0 ? Math.round((mediumAlerts / totalAlerts) * 100) : 0}%)</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-medium"
                  style={{ width: `${totalAlerts > 0 ? (mediumAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>Low</span>
                <span className="font-mono">{lowAlerts} ({totalAlerts > 0 ? Math.round((lowAlerts / totalAlerts) * 100) : 0}%)</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-low"
                  style={{ width: `${totalAlerts > 0 ? (lowAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Lifecycle Status Breakdown */}
        <div className="chart-card">
          <h4 className="chart-title">Alert Lifecycle Status</h4>
          <div className="bar-chart-wrap">
            <div className="bar-item">
              <div className="bar-label-row">
                <span>Active / Unacknowledged</span>
                <span className="font-mono">{activeAlerts}</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-active"
                  style={{ width: `${totalAlerts > 0 ? (activeAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>Acknowledged</span>
                <span className="font-mono">{ackAlerts}</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-ack"
                  style={{ width: `${totalAlerts > 0 ? (ackAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>Resolved</span>
                <span className="font-mono">{resolvedAlerts}</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-resolved"
                  style={{ width: `${totalAlerts > 0 ? (resolvedAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-label-row">
                <span>Dismissed</span>
                <span className="font-mono">{dismissedAlerts}</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill bar-dismissed"
                  style={{ width: `${totalAlerts > 0 ? (dismissedAlerts / totalAlerts) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Event Type Breakdown */}
        <div className="chart-card">
          <h4 className="chart-title">Alerts by Event Type</h4>
          <div className="bar-chart-wrap">
            {Object.entries(eventCounts).map(([evt, cnt]) => (
              <div key={evt} className="bar-item">
                <div className="bar-label-row">
                  <span>{evt}</span>
                  <span className="font-mono">{cnt}</span>
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill bar-event"
                    style={{ width: `${(cnt / totalAlerts) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Camera Distribution */}
        <div className="chart-card">
          <h4 className="chart-title">Alerts by Camera</h4>
          <div className="bar-chart-wrap">
            {Object.entries(cameraCounts).map(([cam, cnt]) => (
              <div key={cam} className="bar-item">
                <div className="bar-label-row">
                  <span>{cam}</span>
                  <span className="font-mono">{cnt}</span>
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill bar-camera"
                    style={{ width: `${(cnt / totalAlerts) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
