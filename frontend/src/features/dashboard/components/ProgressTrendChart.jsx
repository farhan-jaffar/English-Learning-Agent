import React, { useState } from 'react';
import { Sparkles, Activity } from 'lucide-react';
import Badge from '../../../components/ui/Badge';
import './ProgressTrendChart.css';

/**
 * Pure SVG responsive trendline visualization for Speaking Pace (WPM) across practice sessions.
 * @param {Array} data - Array of session points from backend time_series
 */
export default function ProgressTrendChart({ data = [] }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  // Filter valid points with numeric WPM
  const points = (data || []).filter((d) => typeof d.wpm === 'number' && d.wpm > 0);

  if (points.length === 0) {
    return (
      <div className="trend-chart-empty">
        <Activity size={36} className="empty-chart-icon" />
        <h4>No Practice Cadence Data Yet</h4>
        <p>Complete your first spoken exercise to begin tracking your speaking pace trajectory.</p>
      </div>
    );
  }

  // Dimensions
  const svgWidth = 700;
  const svgHeight = 220;
  const paddingX = 45;
  const paddingTop = 25;
  const paddingBottom = 35;

  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  // Min/max calculation with padding
  const wpmValues = points.map((p) => p.wpm);
  const minWpm = Math.max(40, Math.min(...wpmValues, 70) - 15);
  const maxWpm = Math.min(200, Math.max(...wpmValues, 140) + 20);

  const getX = (index) => {
    if (points.length === 1) return paddingX + chartWidth / 2;
    return paddingX + (index / (points.length - 1)) * chartWidth;
  };

  const getY = (wpm) => {
    const clamped = Math.max(minWpm, Math.min(maxWpm, wpm));
    const ratio = (clamped - minWpm) / (maxWpm - minWpm);
    return paddingTop + chartHeight - ratio * chartHeight;
  };

  // Build SVG path
  const coords = points.map((p, idx) => ({ x: getX(idx), y: getY(p.wpm), point: p }));
  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L ${coords[coords.length - 1].x.toFixed(1)} ${paddingTop + chartHeight} L ${coords[0].x.toFixed(1)} ${paddingTop + chartHeight} Z`;

  // Fluent optimal zone coordinates (110 - 150 WPM)
  const zoneTopY = getY(150);
  const zoneBottomY = getY(110);
  const zoneHeight = Math.max(0, zoneBottomY - zoneTopY);

  // Grid lines
  const gridTicks = [80, 110, 140, 170].filter((t) => t >= minWpm && t <= maxWpm);

  return (
    <div className="trend-chart-wrapper">
      <div className="trend-chart-header">
        <div className="trend-chart-title">
          <Activity size={18} />
          <span>Speaking Pace Trajectory (Words Per Minute)</span>
        </div>
        <div className="optimal-zone-legend">
          <span className="legend-box" />
          <span>Ideal Flow Zone (110–150 WPM)</span>
        </div>
      </div>

      <div className="svg-container">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="trend-svg"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="trendAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FFFF66" stopOpacity="0.45" />
              <stop offset="70%" stopColor="#B3B347" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#FAFAF7" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="trendLineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#B3B347" />
              <stop offset="50%" stopColor="#92400E" />
              <stop offset="100%" stopColor="#B3B347" />
            </linearGradient>
          </defs>

          {/* Optimal Fluency Zone (110 - 150 WPM) */}
          <rect
            x={paddingX}
            y={zoneTopY}
            width={chartWidth}
            height={zoneHeight}
            className="optimal-zone-rect"
          />

          {/* Grid lines */}
          {gridTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={paddingX}
                y1={getY(tick)}
                x2={paddingX + chartWidth}
                y2={getY(tick)}
                className="grid-line"
              />
              <text
                x={paddingX - 8}
                y={getY(tick) + 4}
                className="axis-label y-axis"
              >
                {tick}
              </text>
            </g>
          ))}

          {/* Area Fill */}
          <path d={areaPath} fill="url(#trendAreaGradient)" />

          {/* Trendline */}
          <path
            d={linePath}
            fill="none"
            stroke="url(#trendLineGradient)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="chart-stroke"
          />

          {/* Data Points */}
          {coords.map((c, i) => {
            const isHovered = hoveredPoint?.point?.id === c.point.id;
            return (
              <g key={c.point.id || i}>
                <circle
                  cx={c.x}
                  cy={c.y}
                  r={isHovered ? 7 : 4.5}
                  className={`data-point-circle ${isHovered ? 'hovered' : ''}`}
                  onMouseEnter={() => setHoveredPoint(c)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
              </g>
            );
          })}

          {/* X-axis date extremes */}
          {points.length > 1 && (
            <>
              <text x={paddingX} y={svgHeight - 8} className="axis-label x-axis-start">
                {points[0].date?.split(' ')[0] || ''}
              </text>
              <text
                x={paddingX + chartWidth}
                y={svgHeight - 8}
                className="axis-label x-axis-end"
                textAnchor="end"
              >
                {points[points.length - 1].date?.split(' ')[0] || ''}
              </text>
            </>
          )}
        </svg>

        {/* Hover Tooltip Card */}
        {hoveredPoint && (
          <div
            className="chart-tooltip"
            style={{
              left: `${(hoveredPoint.x / svgWidth) * 100}%`,
              top: `${Math.max(10, (hoveredPoint.y / svgHeight) * 100 - 35)}%`,
            }}
          >
            <div className="tooltip-header">
              <span className="tooltip-title">
                {hoveredPoint.point.exercise_title || 'Speaking Exercise'}
              </span>
              {hoveredPoint.point.cefr_estimate && (
                <Badge variant="lemon" size="sm">
                  {hoveredPoint.point.cefr_estimate}
                </Badge>
              )}
            </div>
            <div className="tooltip-metrics">
              <div className="tooltip-stat">
                <span>Pace:</span>
                <strong>{hoveredPoint.point.wpm} WPM</strong>
              </div>
              <div className="tooltip-stat">
                <span>Pauses:</span>
                <span>{hoveredPoint.point.pause_count ?? 0}</span>
              </div>
              <div className="tooltip-stat">
                <span>Fillers:</span>
                <span>{hoveredPoint.point.filler_count ?? 0}</span>
              </div>
            </div>
            <div className="tooltip-date">{hoveredPoint.point.date}</div>
          </div>
        )}
      </div>
    </div>
  );
}
