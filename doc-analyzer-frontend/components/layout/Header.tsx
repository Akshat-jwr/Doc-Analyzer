import React from 'react';
import { motion } from 'framer-motion';
import { Menu, Plus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  onMenuClick: () => void;
  title: string;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick, title }) => {
  const { user } = useAuth();

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-dark-900/90 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4"
    >
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onMenuClick}
            className="lg:hidden text-blue-300 hover:text-white hover:bg-blue-500/20"
          >
            <Menu className="w-5 h-5" />
          </Button>
          
          <div>
            <h1 className="text-2xl font-bold text-white">{title}</h1>
            <p className="text-blue-300/70 text-sm">
              Welcome back, {user?.full_name?.split(' ')[0] || 'User'}!
            </p>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            icon={<Plus />}
            className="bg-blue-500/20 border border-blue-500/30 text-blue-300 hover:text-white hover:bg-blue-500/30"
          >
            Upload
          </Button>

          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold">
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </motion.header>
  );
};
