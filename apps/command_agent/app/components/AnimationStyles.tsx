import React from 'react';

export const AnimationStyles: React.FC = () => {
    return (
        <style>{`
      @keyframes draw-line {
        from {
          stroke-dasharray: 1000;
          stroke-dashoffset: 1000;
        }
        to {
          stroke-dasharray: 1000;
          stroke-dashoffset: 0;
        }
      }
      
      .animate-draw-line {
        animation: draw-line 0.8s ease-out forwards;
      }
      
      .grid-pattern {
        background-image: linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
        background-size: 20px 20px;
      }
      
      .glass-panel {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
      }
      
      .node-shadow {
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
      }
      
      .node-shadow:hover {
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
        transform: translateY(-1px);
      }
      
      /* New animations for the enhanced metrics and node states */
      @keyframes pulse {
        0% {
          opacity: 1;
        }
        50% {
          opacity: 0.7;
        }
        100% {
          opacity: 1;
        }
      }
      
      .animate-pulse {
        animation: pulse 1.5s infinite ease-in-out;
      }
      
      /* Data flow animation */
      @keyframes data-flow {
        0% {
          stroke-dashoffset: 1000;
        }
        100% {
          stroke-dashoffset: 0;
        }
      }
      
      .animate-data-flow {
        stroke-dasharray: 10, 5;
        animation: data-flow 20s linear infinite;
      }
      
      /* Glow effect for active nodes */
      .active-node {
        filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
      }
      
      .active-node-emerald {
        filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5));
      }
      
      .active-node-amber {
        filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.5));
      }
      
      /* Scale animation for nodes when activated */
      @keyframes scale-up {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.05);
        }
        100% {
          transform: scale(1);
        }
      }
      
      .animate-scale {
        animation: scale-up 0.5s ease-out;
      }
      
      /* Fade transition for metrics */
      .fade-transition {
        transition: opacity 0.3s ease-in-out, background-color 0.3s ease-in-out;
      }
    `}</style>
    );
};

export default AnimationStyles;