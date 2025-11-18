# Credit System

A comprehensive credit-based monetization system for the Astrology App.

## Features

- **User Credit Management**: Track credit balance and transactions
- **Promo Code System**: Redeem codes for credits
- **Feature Gating**: Restrict premium features to credit-paying users
- **Admin Panel**: Manage promo codes and user credits
- **Transaction History**: Complete audit trail of all credit movements

## Setup

1. **Initialize the system**:
   ```bash
   cd backend/credits
   python init_credits.py
   ```

2. **The system will create**:
   - Database tables for credits, transactions, and promo codes
   - Initial promo codes (WELCOME, PREMIUM, VIP series)

## API Endpoints

### User Endpoints
- `GET /api/credits/balance` - Get user's credit balance
- `GET /api/credits/history` - Get transaction history
- `POST /api/credits/redeem` - Redeem promo code
- `POST /api/credits/spend` - Spend credits on features

### Admin Endpoints
- `POST /api/credits/admin/promo-codes` - Create single promo code
- `POST /api/credits/admin/bulk-promo-codes` - Create bulk promo codes
- `GET /api/credits/admin/promo-codes` - List all promo codes
- `GET /api/credits/admin/stats` - Get usage statistics
- `POST /api/credits/admin/add-credits` - Manually add credits to user

## Mobile Integration

### 1. Add Credit Provider to App
```javascript
import { CreditProvider } from './src/credits/CreditContext';

export default function App() {
  return (
    <CreditProvider>
      {/* Your app components */}
    </CreditProvider>
  );
}
```

### 2. Use Credits in Components
```javascript
import { useCredits } from './src/credits/CreditContext';
import { CREDIT_COSTS } from './src/credits/creditService';

const MyComponent = () => {
  const { credits, spendCredits } = useCredits();
  
  const handlePremiumFeature = async () => {
    const success = await spendCredits(
      CREDIT_COSTS.PREMIUM_ANALYSIS,
      'premium_analysis',
      'Premium Chart Analysis'
    );
    
    if (success) {
      // Proceed with premium feature
    }
  };
};
```

### 3. Credit Gate Component
```javascript
import CreditGate from './src/credits/CreditGate';

<CreditGate
  cost={10}
  feature="premium_analysis"
  description="Premium Chart Analysis"
  onPurchase={() => {
    // Feature unlocked, proceed
  }}
>
  <PremiumFeatureComponent />
</CreditGate>
```

## Credit Costs

Default credit costs for features:
- Premium Analysis: 10 credits
- Detailed Prediction: 15 credits
- Compatibility Report: 20 credits
- Yearly Forecast: 25 credits
- Personalized Remedies: 12 credits

## Promo Code Types

### WELCOME Series
- **Credits**: 50
- **Usage**: New user onboarding
- **Expiry**: 90 days

### PREMIUM Series
- **Credits**: 200
- **Usage**: Marketing campaigns
- **Expiry**: 60 days

### VIP Series
- **Credits**: 500
- **Usage**: Special promotions
- **Expiry**: 30 days

## Database Schema

### user_credits
- `userid` - User ID (FK)
- `credits` - Current balance
- `created_at`, `updated_at` - Timestamps

### credit_transactions
- `userid` - User ID (FK)
- `transaction_type` - 'earned', 'spent', 'refunded'
- `amount` - Credit amount (positive/negative)
- `balance_after` - Balance after transaction
- `source` - Transaction source
- `reference_id` - Reference (promo code, etc.)
- `description` - Human-readable description

### promo_codes
- `code` - Unique promo code
- `credits` - Credits to award
- `max_uses` - Maximum usage count
- `used_count` - Current usage count
- `is_active` - Active status
- `expires_at` - Expiration date

### promo_code_usage
- `promo_code_id` - Promo code ID (FK)
- `userid` - User ID (FK)
- `credits_earned` - Credits earned from redemption
- `used_at` - Usage timestamp

## Future Enhancements

1. **Payment Integration**: Add Stripe/PayPal for credit purchases
2. **Subscription Plans**: Monthly credit allowances
3. **Referral System**: Earn credits for referrals
4. **Daily Rewards**: Login bonuses
5. **Achievement System**: Credits for app engagement