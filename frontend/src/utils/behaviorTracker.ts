import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export class BehaviorTracker {
  private sessionId: string;
  private isEnabled: boolean = true;

  constructor() {
    this.sessionId = localStorage.getItem('sessionId') || `session_${Date.now()}`;
    localStorage.setItem('sessionId', this.sessionId);
    
    // Track page views automatically
    this.trackEvent('page_view', { 
      page: window.location.pathname,
      title: document.title 
    });

    // Track exit intent
    this.setupExitIntentTracking();
  }

  async trackEvent(
    eventType: 'page_view' | 'product_view' | 'cart_add' | 'cart_remove' | 'checkout_start' | 'payment_attempt' | 'exit_intent',
    eventData?: any,
    pageUrl?: string
  ) {
    if (!this.isEnabled) return;

    try {
      await axios.post(`${API_BASE}/behavior/track`, {
        session_id: this.sessionId,
        event_type: eventType,
        event_data: eventData,
        page_url: pageUrl || window.location.pathname
      });
    } catch (error) {
      console.warn('Behavior tracking failed:', error);
    }
  }

  trackProductView(productId: number, productName?: string) {
    this.trackEvent('product_view', { 
      product_id: productId, 
      product_name: productName,
      timestamp: new Date().toISOString()
    });
  }

  trackCartAdd(productId: number, quantity: number, productName?: string) {
    this.trackEvent('cart_add', { 
      product_id: productId, 
      quantity: quantity,
      product_name: productName,
      timestamp: new Date().toISOString()
    });
  }

  trackCartRemove(productId: number, quantity: number) {
    this.trackEvent('cart_remove', { 
      product_id: productId, 
      quantity: quantity,
      timestamp: new Date().toISOString()
    });
  }

  trackCheckoutStart(cartValue: number, itemCount: number) {
    this.trackEvent('checkout_start', { 
      cart_value: cartValue, 
      item_count: itemCount,
      timestamp: new Date().toISOString()
    });
  }

  trackPaymentAttempt(method: string, amount: number) {
    this.trackEvent('payment_attempt', { 
      payment_method: method, 
      amount: amount,
      timestamp: new Date().toISOString()
    });
  }

  private setupExitIntentTracking() {
    let exitIntentTracked = false;

    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0 && !exitIntentTracked) {
        exitIntentTracked = true;
        this.trackEvent('exit_intent', { 
          page: window.location.pathname,
          timestamp: new Date().toISOString()
        });
        
        // Reset after 30 seconds
        setTimeout(() => {
          exitIntentTracked = false;
        }, 30000);
      }
    };

    document.addEventListener('mouseleave', handleMouseLeave);
  }

  async getAbandonmentAnalysis(): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE}/behavior/analyze/${this.sessionId}`);
      return response.data;
    } catch (error) {
      console.warn('Failed to get abandonment analysis:', error);
      return null;
    }
  }

  disable() {
    this.isEnabled = false;
  }

  enable() {
    this.isEnabled = true;
  }

  getSessionId(): string {
    return this.sessionId;
  }
}

// Global instance
export const behaviorTracker = new BehaviorTracker();

// Auto-track page changes for SPAs
let currentPath = window.location.pathname;
setInterval(() => {
  if (window.location.pathname !== currentPath) {
    currentPath = window.location.pathname;
    behaviorTracker.trackEvent('page_view', { 
      page: currentPath,
      title: document.title 
    });
  }
}, 1000);
