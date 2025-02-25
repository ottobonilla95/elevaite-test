import React from 'react';
import { MessageCircle, Moon, Sun, Share } from "lucide-react";

// Individual icon components
export const MessageIcon: React.FC = () => <MessageCircle className="h-4 w-4" />;
export const MoonIcon: React.FC = () => <Moon className="h-4 w-4" />;
export const SunIcon: React.FC = () => <Sun className="h-4 w-4" />;
export const ShareIcon: React.FC = () => <Share className="h-4 w-4" />;

// Icons object for centralized access
export const Icons = {
  Message: MessageIcon,
  Moon: MoonIcon,
  Sun: SunIcon,
  Share: ShareIcon,
};

