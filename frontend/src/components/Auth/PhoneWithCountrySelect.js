import React from 'react';
import { COUNTRY_CODES, getNationalPhoneMaxLength } from '../../utils/countryCodes';

/**
 * Country code dropdown + national number input (digits only). Parents compose full phone with buildFullPhone().
 */
const PhoneWithCountrySelect = ({
  countryCode,
  onCountryCodeChange,
  nationalDigits,
  onNationalDigitsChange,
  disabled = false,
  inputId,
  inputName,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        alignItems: 'stretch',
        width: '100%',
      }}
    >
      <select
        aria-label="Country code"
        value={countryCode}
        onChange={(e) => onCountryCodeChange(e.target.value)}
        disabled={disabled}
        style={{
          flex: '0 0 auto',
          width: 'min(42%, 140px)',
          padding: '0.75rem 0.45rem',
          border: '2px solid rgba(233, 30, 99, 0.2)',
          borderRadius: '12px',
          fontSize: '16px',
          background: 'rgba(255, 255, 255, 0.8)',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        {COUNTRY_CODES.map((c) => (
          <option key={c.code} value={c.code}>
            {c.flag} {c.code}
          </option>
        ))}
      </select>
      <input
        id={inputId}
        name={inputName}
        type="tel"
        inputMode="numeric"
        autoComplete="tel-national"
        value={nationalDigits}
        onChange={(e) => {
          const d = e.target.value.replace(/[^0-9]/g, '');
          const max = getNationalPhoneMaxLength(countryCode);
          onNationalDigitsChange(d.slice(0, max));
        }}
        placeholder="Phone number"
        disabled={disabled}
        style={{
          flex: 1,
          minWidth: 0,
          padding: '0.75rem',
          border: '2px solid rgba(233, 30, 99, 0.2)',
          borderRadius: '12px',
          fontSize: '16px',
          background: 'rgba(255, 255, 255, 0.8)',
          WebkitAppearance: 'none',
        }}
      />
    </div>
  );
};

export default PhoneWithCountrySelect;
