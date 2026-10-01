import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { BottomNav } from './BottomNav';
import './AppLayout.css';

export function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-shell-content">
        <Navbar />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
