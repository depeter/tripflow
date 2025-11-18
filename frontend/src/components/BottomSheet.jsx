import React, { useState, useRef, useEffect } from 'react';
import './BottomSheet.css';

/**
 * BottomSheet Component
 * Swipeable bottom sheet for mobile-first UI
 * Shows event list in discovery mode
 */
const BottomSheet = ({ children, isOpen, onClose, snapPoints = [0.2, 0.5, 0.9] }) => {
  const [currentSnap, setCurrentSnap] = useState(1); // Start at middle snap point
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [currentY, setCurrentY] = useState(0);
  const sheetRef = useRef(null);

  // Calculate height based on snap point
  const getHeight = () => {
    if (!isOpen) return 0;
    const viewportHeight = window.innerHeight;
    const baseHeight = snapPoints[currentSnap] * viewportHeight;

    if (isDragging) {
      const dragDelta = startY - currentY;
      return Math.max(0, Math.min(viewportHeight, baseHeight + dragDelta));
    }

    return baseHeight;
  };

  // Handle touch start
  const handleTouchStart = (e) => {
    setIsDragging(true);
    setStartY(e.touches[0].clientY);
    setCurrentY(e.touches[0].clientY);
  };

  // Handle touch move
  const handleTouchMove = (e) => {
    if (!isDragging) return;
    setCurrentY(e.touches[0].clientY);
  };

  // Handle touch end
  const handleTouchEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);

    const dragDistance = startY - currentY;
    const viewportHeight = window.innerHeight;
    const dragThreshold = viewportHeight * 0.1; // 10% threshold

    // Determine new snap point
    let newSnap = currentSnap;

    if (dragDistance > dragThreshold && currentSnap < snapPoints.length - 1) {
      // Swiped up
      newSnap = currentSnap + 1;
    } else if (dragDistance < -dragThreshold) {
      // Swiped down
      if (currentSnap > 0) {
        newSnap = currentSnap - 1;
      } else {
        // Close if swiped down from lowest snap point
        onClose?.();
        return;
      }
    }

    setCurrentSnap(newSnap);
  };

  // Handle mouse events for desktop
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartY(e.clientY);
    setCurrentY(e.clientY);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setCurrentY(e.clientY);
  };

  const handleMouseUp = () => {
    if (!isDragging) return;
    handleTouchEnd();
  };

  // Add mouse event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // Reset to middle snap point when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentSnap(1);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`bottom-sheet-backdrop ${isOpen ? 'visible' : ''}`}
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div
        ref={sheetRef}
        className={`bottom-sheet ${isOpen ? 'open' : ''}`}
        style={{
          height: `${getHeight()}px`,
          transition: isDragging ? 'none' : 'height 0.3s ease-out'
        }}
      >
        {/* Drag Handle */}
        <div
          className="bottom-sheet-handle"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onMouseDown={handleMouseDown}
        >
          <div className="handle-bar" />
        </div>

        {/* Content */}
        <div className="bottom-sheet-content">
          {children}
        </div>
      </div>
    </>
  );
};

export default BottomSheet;
