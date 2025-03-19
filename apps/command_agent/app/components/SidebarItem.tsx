import React from 'react';
import { SidebarItem as SidebarItemType } from './type';

interface SidebarItemProps {
    item: SidebarItemType;
    handleDragStart: (e: React.MouseEvent, nodeId: string, fromSidebar: boolean) => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ item, handleDragStart }) => {
    return (
        <div
            key={item.id}
            className="sidebar-item p-2.5 rounded-lg border border-gray-200/50 cursor-grab transition-transform hover:translate-x-1 active:translate-x-0 hover:shadow-md active:shadow-sm bg-white/80"
            draggable="true"
            onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', item.id);
                e.dataTransfer.effectAllowed = 'copy';
            }}
            onMouseDown={(e) => handleDragStart(e, item.id, true)}
        >
            <div className="flex items-center">
                <div className="w-8 h-8 rounded-md bg-primary/10 text-primary flex items-center justify-center mr-3">
                    {item.icon}
                </div>
                <div>
                    <h3 className="text-sm font-medium">{item.type}</h3>
                    <p className="text-xs text-gray-500">{item.description}</p>
                </div>
            </div>
        </div>
    );
};

export default SidebarItem;