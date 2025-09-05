import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  image_url: string;
  stock_quantity: number;
  category: string;
}

export interface CartItem {
  product_id: number;
  quantity: number;
  name?: string;
  price?: number;
  image_url?: string;
}

export interface Cart {
  cart_id: number | null;
  items: CartItem[];
  total_value: number;
}

interface CartContextType {
  cart: Cart;
  sessionId: string;
  addToCart: (product: Product, quantity?: number) => void;
  removeFromCart: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  isLoading: boolean;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

const API_BASE = 'http://localhost:8000';

export const CartProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [cart, setCart] = useState<Cart>({ cart_id: null, items: [], total_value: 0 });
  const [sessionId] = useState(() => localStorage.getItem('sessionId') || uuidv4());
  const [isLoading, setIsLoading] = useState(false);

  // Store session ID in localStorage
  useEffect(() => {
    localStorage.setItem('sessionId', sessionId);
  }, [sessionId]);

  // Load cart from backend on mount
  useEffect(() => {
    loadCart();
  }, [sessionId]);

  const loadCart = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE}/cart/${sessionId}`);
      setCart(response.data);
    } catch (error) {
      console.error('Error loading cart:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateCartOnServer = async (items: CartItem[]) => {
    try {
      setIsLoading(true);
      await axios.post(`${API_BASE}/cart/update`, {
        session_id: sessionId,
        items: items
      });
      
      // Reload cart to get updated data
      await loadCart();
    } catch (error) {
      console.error('Error updating cart:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addToCart = (product: Product, quantity = 1) => {
    const existingItem = cart.items.find(item => item.product_id === product.id);
    let newItems;

    if (existingItem) {
      newItems = cart.items.map(item =>
        item.product_id === product.id
          ? { ...item, quantity: item.quantity + quantity }
          : item
      );
    } else {
      newItems = [...cart.items, {
        product_id: product.id,
        quantity,
        name: product.name,
        price: product.price,
        image_url: product.image_url
      }];
    }

    updateCartOnServer(newItems);
  };

  const removeFromCart = (productId: number) => {
    const newItems = cart.items.filter(item => item.product_id !== productId);
    updateCartOnServer(newItems);
  };

  const updateQuantity = (productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }

    const newItems = cart.items.map(item =>
      item.product_id === productId
        ? { ...item, quantity }
        : item
    );
    updateCartOnServer(newItems);
  };

  const clearCart = () => {
    updateCartOnServer([]);
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        sessionId,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        isLoading
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
