import React from 'react';

/** Hide DB metadata accidentally shown as bullets (e.g. {"tier": true}). */
function displayBenefits(benefits) {
  return (benefits || []).filter((line) => {
    const s = String(line).trim();
    if (!s) return false;
    if (s.startsWith('{') && s.endsWith('}')) return false;
    return true;
  });
}

function tierAccentClass(tierName) {
  const t = (tierName || '').toLowerCase();
  if (t.includes('platinum')) return 'subscription-plan-card--platinum';
  if (t.includes('gold')) return 'subscription-plan-card--gold';
  if (t.includes('silver')) return 'subscription-plan-card--silver';
  return '';
}

function SubscriptionPlanCard({
  plan,
  onAction,
  busy = false,
  disabled = false,
  highlight = false,
  actionLabel = 'Subscribe',
  busyLabel = 'Please wait…',
  isCurrentPlan = false,
}) {
  const monthlyPrice = plan.formatted_price || plan.amount_display || '—';
  const features = Array.isArray(plan.feature_pricing) ? plan.feature_pricing : [];
  const benefits = displayBenefits(plan.benefits);
  const accent = tierAccentClass(plan.tier_name);
  const isPlatinum = accent === 'subscription-plan-card--platinum';
  const isVip = (plan.subscription_family || 'vip') === 'vip';

  return (
    <article
      className={[
        'subscription-plan-card',
        accent,
        highlight ? 'subscription-plan-card--highlight' : '',
        isPlatinum ? 'subscription-plan-card--popular' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {isPlatinum && <span className="subscription-plan-card__badge">Most popular</span>}

      <header className="subscription-plan-card__header">
        <h3>{plan.tier_name}</h3>
        <p className="subscription-plan-card__discount">
          {isVip ? `${plan.discount_percent}% off all credit features` : 'Professional astrology tools'}
        </p>
      </header>

      <div className="subscription-plan-card__price-block">
        <p className="subscription-plan-card__price">{monthlyPrice}</p>
        <p className="subscription-plan-card__price-period">per month</p>
      </div>

      {benefits.length > 0 && (
        <ul className="subscription-plan-card__benefits">
          {benefits.slice(0, 3).map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}

      {features.length > 0 && (
        <div className="subscription-plan-card__features">
          <div className="subscription-plan-card__features-head">
            <span className="subscription-plan-card__col-feature">Feature</span>
            <span className="subscription-plan-card__col-price">Was</span>
            <span className="subscription-plan-card__col-price">You pay</span>
          </div>
          <div className="subscription-plan-card__features-scroll">
            <ul className="subscription-plan-card__features-list">
              {features.map((row) => (
                <li key={row.key} className="subscription-plan-card__feature-row">
                  <span className="subscription-plan-card__feature-label" title={row.label}>
                    {row.label}
                  </span>
                  <span className="subscription-plan-card__feature-regular">
                    {row.regular_credits}
                    <span className="subscription-plan-card__credits-unit"> cr</span>
                  </span>
                  <span className="subscription-plan-card__feature-tier">
                    {row.tier_credits}
                    <span className="subscription-plan-card__credits-unit"> cr</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <button
        type="button"
        className="subscription-btn subscription-btn--primary subscription-plan-card__cta"
        onClick={() => onAction(plan)}
        disabled={disabled || busy || isCurrentPlan}
      >
        {isCurrentPlan ? 'Current plan' : busy ? busyLabel : actionLabel}
      </button>
    </article>
  );
}

export default SubscriptionPlanCard;
