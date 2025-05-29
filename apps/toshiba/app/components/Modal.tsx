import React, { useEffect, useState } from 'react';
import './Modal.scss';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaUrls: string[];
  mediaTypes: ('image' | 'video')[];
  mediaNames: string[];
  currentIndex: number;
  onNext: () => void;
  onPrevious: () => void;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  mediaUrls,
  mediaTypes,
  mediaNames,
  currentIndex,
  onNext,
  onPrevious,
}) => {
  const [videoSrc, setVideoSrc] = useState<string | undefined>(undefined); // Use undefined instead of null

  useEffect(() => {
    if (isOpen) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, onClose]);

  useEffect(() => {
    if (mediaTypes[currentIndex] === 'video') {
      setVideoSrc(mediaUrls[currentIndex]); // Set video source when in view
    } else {
      setVideoSrc(undefined); // Clear video source if it's an image
    }
  }, [currentIndex, mediaTypes, mediaUrls]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} aria-modal="true" role="dialog">
        {mediaTypes[currentIndex] === 'video' && videoSrc ? ( // Conditional rendering
          <video controls src={videoSrc} />
        ) : (
          <img src={mediaUrls[currentIndex]} alt={mediaNames[currentIndex] || "Media"} loading="lazy" />
        )}
        <div className="slider-info">
          <p>Creative: {mediaNames[currentIndex]}</p>
          <p>
            {currentIndex + 1} of {mediaUrls.length}
          </p>
        </div>
        <div className="slider-controls">
          <button className="slider-buttons" onClick={onPrevious} disabled={mediaUrls.length <= 1}>Previous</button>
          <button className="slider-buttons" onClick={onNext} disabled={mediaUrls.length <= 1}>Next</button>
        </div>
        <button className="close-button" onClick={onClose}>Close</button>
      </div>
    </div>
  );
};

export default Modal;
