import React, { useState, useEffect } from 'react';
import { useCart } from '../context/CartContext';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

interface AbandonmentOffer {
  offer_type: string;
  offer_value: number;
  offer_description: string;
}

const AbandonmentPopup: React.FC = () => {
  const { cart } = useCart();
  const [showPopup, setShowPopup] = useState(false);
  const [offer, setOffer] = useState<AbandonmentOffer | null>(null);

  useEffect(() => {
    let timeoutId: number;
    
    // Show popup if user has items in cart and hasn't interacted for 60 seconds
    if (cart.items.length > 0) {
      timeoutId = setTimeout(() => {
        generateOffer();
      }, 60000); // 1 minute
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [cart.items.length]);

  const generateOffer = async () => {
    if (cart.cart_id) {
      try {
        const response = await axios.post(`${API_BASE}/cart/${cart.cart_id}/generate-recovery-email`);
        setOffer(response.data.offer);
        setShowPopup(true);
      } catch (error) {
        console.error('Error generating offer:', error);
      }
    }
  };

  const handleAcceptOffer = () => {
    // In a real app, apply the discount and redirect to checkout
    setShowPopup(false);
    window.location.href = '/checkout';
  };

  const handleDismiss = () => {
    setShowPopup(false);
  };

  if (!showPopup || !offer) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md mx-4 p-6">
        <div className="text-center">
          <div className="mb-4">
            <svg className="w-16 h-16 text-yellow-500 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            Wait! Don't leave empty-handed
          </h3>
          
          <p className="text-gray-600 mb-4">
            You have {cart.items.length} item{cart.items.length > 1 ? 's' : ''} in your cart worth ${cart.total_value.toFixed(2)}
          </p>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <svg className="w-6 h-6 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-green-800 font-medium">Special Offer!</p>
                <p className="text-green-700 text-sm">{offer.offer_description}</p>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleAcceptOffer}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              Accept Offer
            </button>
            
            <button
              onClick={handleDismiss}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              No Thanks
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-3">
            This offer expires in 10 minutes
          </p>
        </div>
      </div>
    </div>
  );
};

export default AbandonmentPopup;
