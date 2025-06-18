import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/router';
import { 
  Home, 
  FileText, 
  Upload, 
  Settings, 
  LogOut, 
  X,
  Brain,
  MessageSquare
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen }) => {
  const router = useRouter();
  const { user, logout } = useAuth();

  const menuItems = [
    { icon: Home, label: 'Dashboard', href: '/' },
    { icon: FileText, label: 'Documents', href: '/documents' },
    { icon: MessageSquare, label: 'AI Chat', href: '/chat' },
    { icon: Upload, label: 'Visualizations', href: '/visualizations' },

  ];

  const handleNavigation = (href: string) => {
    router.push(href);
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={{ x: -280 }}
        animate={{ x: isOpen ? 0 : -280 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-dark-900 to-dark-850 border-r border-blue-500/20 z-50 lg:relative lg:translate-x-0"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-blue-500/20">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">DocAnalyzer</h2>
              <p className="text-xs text-blue-300/70">AI Powered</p>
            </div>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
            className="lg:hidden text-blue-300 hover:text-white"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.href;
            
            return (
              <motion.button
                key={item.href}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleNavigation(item.href)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-500/20 border border-blue-500/30 text-blue-300'
                    : 'text-blue-200/70 hover:text-white hover:bg-blue-500/10'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </motion.button>
            );
          })}
        </nav>
        {/* User Profile */}
        <div className="p-6 border-b border-blue-500/20">
          <div className="flex items-center space-x-3 p-3 rounded-xl bg-dark-800/50 border border-blue-500/20">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium truncate">{user?.full_name || 'User'}</p>
              <p className="text-blue-300/70 text-sm truncate">{user?.email || 'user@example.com'}</p>
            </div>
          </div>
        </div>
        {/* Footer */}
        <div className="p-4 border-t border-blue-500/20 space-y-2">
          {/* <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-blue-200/70 hover:text-white hover:bg-blue-500/10"
            icon={<Settings />}
            onClick={() => handleNavigation('/settings')}
          >
            Settings
          </Button> */}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/10"
            icon={<LogOut />}
          >
            Sign Out
          </Button>
        </div>
      </motion.div>
    </>
  );
};
