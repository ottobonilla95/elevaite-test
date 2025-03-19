import React from 'react';
import SidebarItem from './SidebarItem';
import { SidebarItem as SidebarItemType } from './type';

interface SidebarProps {
    sidebarOpen: boolean;
    sidebarCategory: 'agents' | 'components' | 'tools';
    setSidebarCategory: (category: 'agents' | 'components' | 'tools') => void;
    sidebarItems: Record<string, SidebarItemType[]>;
    handleDragStart: (e: React.MouseEvent, nodeId: string, fromSidebar: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    sidebarOpen,
    sidebarCategory,
    setSidebarCategory,
    sidebarItems,
    handleDragStart
}) => {
    return (
        <div
            className={`glass-panel border-r border-gray-200/50 h-full transition-all duration-300 ease-in-out ${sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
                }`}
        >
            <div className="p-4 border-b border-gray-200/50">
                <h2 className="text-lg font-medium">Agent Flow Designer</h2>
                <p className="text-sm text-gray-500 mt-1">Drag items to workspace</p>
            </div>

            <div className="flex border-b border-gray-200/50">
                {Object.keys(sidebarItems).map((cat) => (
                    <button
                        key={cat}
                        className={`flex-1 py-2.5 text-sm font-medium transition-colors ${sidebarCategory === cat
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                        onClick={() => setSidebarCategory(cat as 'agents' | 'components' | 'tools')}
                    >
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </button>
                ))}
            </div>

            <div className="p-3 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 130px)' }}>
                {sidebarItems[sidebarCategory]?.map((item) => (
                    <SidebarItem
                        key={item.id}
                        item={item}
                        handleDragStart={handleDragStart}
                    />
                ))}
            </div>
        </div>
    );
};

export default Sidebar;