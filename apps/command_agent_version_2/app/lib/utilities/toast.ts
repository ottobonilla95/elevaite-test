// utils/toast.ts
export interface ToastOptions {
  duration?: number;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center";
}

class ToastManager {
  private container: HTMLDivElement | null = null;
  private toasts: HTMLDivElement[] = [];

  private getContainerStyles(position: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center"): string {
    const baseStyles = `
      position: fixed;
      z-index: 10000;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    `;

    const positionStyles = {
      "top-right": "top: 75px; right: 20px;",
      "top-left": "top: 75px; left: 20px;",
      "top-center": "top: 75px; left: 50%; transform: translateX(-50%);",
      "bottom-right": "bottom: 20px; right: 20px;",
      "bottom-left": "bottom: 20px; left: 20px;",
      "bottom-center": "bottom: 20px; left: 50%; transform: translateX(-50%);"
    };

    return baseStyles + positionStyles[position];
  }

  private createContainer(position: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center" = "top-center"): HTMLDivElement {
    if (this.container && document.body.contains(this.container)) {
      return this.container;
    }

    const container = document.createElement("div");
    container.id = "toast-container";
    container.style.cssText = this.getContainerStyles(position);
    document.body.appendChild(container);
    this.container = container;
    return container;
  }

  private createToast(message: string, type: "success" | "error" | "info" | "warning", options: ToastOptions = {}): HTMLDivElement {
    const toast = document.createElement("div");
    
    const colors = {
      success: { bg: "#10B981", border: "#059669" },
      error: { bg: "#EF4444", border: "#DC2626" },
      info: { bg: "#3B82F6", border: "#2563EB" },
      warning: { bg: "#F59E0B", border: "#D97706" }
    };

    const icons = {
      success: "✓",
      error: "✕",
      info: "ℹ",
      warning: "⚠"
    };

    toast.style.cssText = `
      background: ${colors[type].bg};
      color: white;
      padding: 12px 16px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      max-width: 400px;
      word-wrap: break-word;
      pointer-events: auto;
      transform: translateX(100%);
      opacity: 0;
      transition: all 0.3s ease;
      border-left: 4px solid ${colors[type].border};
    `;

    toast.innerHTML = `
      <span style="font-size: 16px;">${icons[type]}</span>
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" style="
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 18px;
        padding: 0;
        margin-left: auto;
        opacity: 0.7;
        hover: opacity: 1;
      ">×</button>
    `;

    return toast;
  }

  private showToast(message: string, type: "success" | "error" | "info" | "warning", options: ToastOptions = {}): void {
    const position = options.position || "top-right";
    const container = this.createContainer(position);
    const toast = this.createToast(message, type, options);
    
    container.appendChild(toast);
    this.toasts.push(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.style.transform = "translateX(0)";
      toast.style.opacity = "1";
    });

    // Auto remove
    const duration = options.duration ?? (type === "error" ? 5000 : 4000);
    setTimeout(() => {
      this.removeToast(toast);
    }, duration);

    // Limit number of toasts
    if (this.toasts.length > 5) {
      const oldestToast = this.toasts.shift();
      if (oldestToast) {
        this.removeToast(oldestToast);
      }
    }
  }

  private removeToast(toast: HTMLDivElement): void {
    toast.style.transform = "translateX(100%)";
    toast.style.opacity = "0";
    
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
      this.toasts = this.toasts.filter(t => t !== toast);
    }, 300);
  }

  success(message: string, options?: ToastOptions): void {
    this.showToast(message, "success", options);
  }

  error(message: string, options?: ToastOptions): void {
    this.showToast(message, "error", options);
  }

  info(message: string, options?: ToastOptions): void {
    this.showToast(message, "info", options);
  }

  warning(message: string, options?: ToastOptions): void {
    this.showToast(message, "warning", options);
  }
}

export const toast = new ToastManager();