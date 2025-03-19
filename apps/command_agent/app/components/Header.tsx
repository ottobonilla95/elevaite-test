import React from 'react';
import { Menu } from 'lucide-react';

interface HeaderProps {
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    showFlow: boolean;
    setShowFlow: (show: boolean) => void;
    showMetrics: boolean;
    setShowMetrics: (show: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({
    sidebarOpen,
    setSidebarOpen,
    showFlow,
    setShowFlow,
    showMetrics,
    setShowMetrics
}) => {
    return (
        <header className="glass-panel border-b border-gray-200/50 p-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center space-x-4">
                <button
                    className="p-2 rounded-md hover:bg-gray-100/50 transition-colors"
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                >
                    <Menu className="w-5 h-5" />
                </button>
                <h1 className="text-xl font-medium">Agent Flow Designer</h1>
            </div>

            <div className="flex space-x-2">
                <button
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${showFlow
                            ? 'bg-primary/10 text-primary'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                        }`}
                    onClick={() => setShowFlow(true)}
                >
                    Flow View
                </button>
                <button
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${!showFlow
                            ? 'bg-primary/10 text-primary'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                        }`}
                    onClick={() => setShowFlow(false)}
                >
                    Chat View
                </button>
                {showFlow && (
                    <button
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${showMetrics
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                            }`}
                        onClick={() => setShowMetrics(!showMetrics)}
                    >
                        {showMetrics ? 'Hide Metrics' : 'Show Metrics'}
                    </button>
                )}
            </div>
        </header>
    );
};

export default Header;