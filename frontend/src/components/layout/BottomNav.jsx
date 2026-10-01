import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, PlayCircle, Mic, TrendingUp, Settings, MessageSquare } from 'lucide-react';
import './BottomNav.css';

const MOBILE_NAV_ITEMS = [
  { to: '/', label: 'Home', icon: LayoutDashboard, end: true },
  { to: '/practice', label: 'Practice', icon: PlayCircle },
  { to: '/conversations', label: 'AI Partner', icon: MessageSquare },
  { to: '/recordings', label: 'Recordings', icon: Mic },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
  { to: '/settings', label: 'Settings', icon: Settings },
];


export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Mobile navigation">
      {MOBILE_NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `bottom-nav-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
