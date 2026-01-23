"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getPortalRoot } from "../components/common/PortalRoot";

export interface FloatingPosition {
  top?: number;
  bottom?: number;
  left?: number;
  right?: number;
}

export interface UseFloatingElementOptions {
  isOpen: boolean;
  offset?: number;
  placement?: "top" | "bottom" | "left" | "right";
  align?: "left" | "right";
  onClose?: () => void;
}

export interface UseFloatingElementReturn {
  position: FloatingPosition;
  anchorRef: React.RefObject<HTMLElement | null>;
  floatingRef: React.RefObject<HTMLElement | null>;
  renderPortal: (content: React.ReactNode) => React.ReactPortal | null;
}

export function useFloatingElement(
  options: UseFloatingElementOptions,
): UseFloatingElementReturn {
  const {
    isOpen,
    offset = 4,
    placement = "bottom",
    align = "left",
    onClose,
  } = options;
  const anchorRef = useRef<HTMLElement>(null);
  const floatingRef = useRef<HTMLElement>(null);
  const [position, setPosition] = useState<FloatingPosition>({});
  const [portalRoot, setPortalRoot] = useState<HTMLElement | null>(null);
  const animationFrameRef = useRef<number>(undefined);
  const onCloseRef = useRef(onClose);

  // Keep onClose ref up to date without triggering effects
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const root = getPortalRoot();
    if (root) {
      setPortalRoot(root);
    } else {
      // eslint-disable-next-line no-console -- Leave this since it's only dev-relevant
      console.warn(
        "PortalRoot not found. Make sure <PortalRoot /> is mounted at AppLayout.",
      );
    }
  }, []);

  const updatePosition = useCallback(() => {
    if (!anchorRef.current || !floatingRef.current || !isOpen) {
      return;
    }

    const anchorRect = anchorRef.current.getBoundingClientRect();
    const floatingRect = floatingRef.current.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    const isAnchorVisible =
      anchorRect.top < viewportHeight &&
      anchorRect.bottom > 0 &&
      anchorRect.left < viewportWidth &&
      anchorRect.right > 0;

    if (!isAnchorVisible) {
      onCloseRef.current?.();
      return;
    }

    const newPosition: FloatingPosition = {};

    switch (placement) {
      case "bottom": {
        newPosition.top = anchorRect.bottom + offset;

        if (align === "left") {
          newPosition.left = anchorRect.left;
        } else {
          newPosition.right = viewportWidth - anchorRect.right;
        }

        // Shift up if it would go off bottom of screen
        const bottomOverflow =
          newPosition.top + floatingRect.height - viewportHeight;
        if (bottomOverflow > 0) {
          newPosition.top = Math.max(0, newPosition.top - bottomOverflow);
        }

        // Check horizontal overflow
        if (newPosition.left !== undefined) {
          const rightOverflow =
            newPosition.left + floatingRect.width - viewportWidth;
          if (rightOverflow > 0) {
            newPosition.left = Math.max(0, newPosition.left - rightOverflow);
          }
        } else if (newPosition.right !== undefined) {
          const leftEdge =
            viewportWidth - newPosition.right - floatingRect.width;
          if (leftEdge < 0) {
            newPosition.right = Math.max(0, newPosition.right + leftEdge);
          }
        }
        break;
      }

      case "top": {
        newPosition.top = anchorRect.top - floatingRect.height - offset;

        if (align === "left") {
          newPosition.left = anchorRect.left;
        } else {
          newPosition.right = viewportWidth - anchorRect.right;
        }

        // Shift down if it would go off top of screen
        if (newPosition.top < 0) {
          newPosition.top = Math.min(
            viewportHeight - floatingRect.height,
            anchorRect.bottom + offset,
          );
        }

        // Check horizontal overflow
        if (newPosition.left !== undefined) {
          const rightOverflow =
            newPosition.left + floatingRect.width - viewportWidth;
          if (rightOverflow > 0) {
            newPosition.left = Math.max(0, newPosition.left - rightOverflow);
          }
        } else if (newPosition.right !== undefined) {
          const leftEdge =
            viewportWidth - newPosition.right - floatingRect.width;
          if (leftEdge < 0) {
            newPosition.right = Math.max(0, newPosition.right + leftEdge);
          }
        }
        break;
      }

      case "right": {
        newPosition.left = anchorRect.right + offset;
        newPosition.top = anchorRect.top;

        // Shift left if it would go off right of screen
        const rightOverflow =
          newPosition.left + floatingRect.width - viewportWidth;
        if (rightOverflow > 0) {
          newPosition.left = Math.max(0, newPosition.left - rightOverflow);
        }

        // Check vertical overflow
        const bottomOverflow =
          newPosition.top + floatingRect.height - viewportHeight;
        if (bottomOverflow > 0) {
          newPosition.top = Math.max(0, newPosition.top - bottomOverflow);
        }
        if (newPosition.top < 0) {
          newPosition.top = 0;
        }
        break;
      }

      case "left": {
        newPosition.left = anchorRect.left - floatingRect.width - offset;
        newPosition.top = anchorRect.top;

        // Shift right if it would go off left of screen
        if (newPosition.left < 0) {
          newPosition.left = Math.min(
            viewportWidth - floatingRect.width,
            anchorRect.right + offset,
          );
        }

        // Check vertical overflow
        const bottomOverflow =
          newPosition.top + floatingRect.height - viewportHeight;
        if (bottomOverflow > 0) {
          newPosition.top = Math.max(0, newPosition.top - bottomOverflow);
        }
        if (newPosition.top < 0) {
          newPosition.top = 0;
        }
        break;
      }
    }

    setPosition(newPosition);
  }, [isOpen, offset, placement, align]);

  // Update position on open, scroll, and resize
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    updatePosition();

    function handleUpdate(): void {
      animationFrameRef.current = requestAnimationFrame(() => {
        updatePosition();
      });
    }

    function scrollHandler(): void {
      handleUpdate();
    }

    function resizeHandler(): void {
      handleUpdate();
    }

    window.addEventListener("scroll", scrollHandler, true);
    window.addEventListener("resize", resizeHandler);

    return () => {
      window.removeEventListener("scroll", scrollHandler, true);
      window.removeEventListener("resize", resizeHandler);

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isOpen, updatePosition]);

  const renderPortal = useCallback(
    (content: React.ReactNode): React.ReactPortal | null => {
      if (!portalRoot || !isOpen) {
        return null;
      }
      return createPortal(content, portalRoot);
    },
    [portalRoot, isOpen],
  );

  return {
    position,
    anchorRef,
    floatingRef,
    renderPortal,
  };
}
