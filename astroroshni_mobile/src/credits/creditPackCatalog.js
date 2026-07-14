/**
 * Live credit pack catalog — Shuruaat / Aashirwad / Sadhak / Guru.
 * 1 credit = ₹1.99. Regular Q = 22 credits. Premium Q = 59 credits.
 * Never show credit math first in UI; lead with ₹.
 */

export const CREDIT_INR_VALUE = 1.99;

/** Pack marketing metadata keyed by credit amount (matches Play SKU credits_N). */
export const CREDIT_PACK_META = {
  50: {
    name: 'Shuruaat Pack',
    badge: null,
    questions: 2,
    savePercent: 0,
    valueProp: 'New Users - 2 Questions',
    bonusCredits: 0,
  },
  100: {
    name: 'Aashirwad Pack',
    badge: 'Most Popular',
    questions: 4,
    savePercent: 10,
    valueProp: 'Most Popular - 4 Questions',
    bonusCredits: 0,
  },
  250: {
    name: 'Sadhak Pack',
    badge: 'Best Value',
    questions: 11,
    savePercent: 25,
    valueProp: 'Best Value - Save 25%',
    bonusCredits: 0,
  },
  999: {
    name: 'Guru Pack',
    badge: 'For Serious Seekers',
    questions: 45,
    savePercent: 0,
    valueProp: '45 Questions with Tara',
    bonusCredits: 50, // 5% → 1049 total
  },
};

export function getCreditPackMeta(credits) {
  const n = Number(credits) || 0;
  return (
    CREDIT_PACK_META[n] || {
      name: `${n} Credits`,
      badge: null,
      questions: null,
      savePercent: 0,
      valueProp: null,
      bonusCredits: 0,
    }
  );
}

/** Round credits → display rupees (22 → ₹44, 59 → ₹117). */
export function creditsToDisplayInr(credits) {
  const n = Number(credits);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.round(n * CREDIT_INR_VALUE);
}

export function formatCreditsInr(credits) {
  const rupees = creditsToDisplayInr(credits);
  return `₹${rupees}`;
}
