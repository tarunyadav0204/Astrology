import styled from 'styled-components';
import { APP_CONFIG } from '../../config/app.config';

export const ControlsContainer = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    gap: 0.3rem;
  }
`;

export const DateDisplay = styled.div.withConfig({
  shouldForwardProp: (prop) => !['$variant', '$clickable', '$textColor'].includes(prop),
})`
  font-size: 0.8rem;
  font-weight: 600;
  color: ${({ $variant, $textColor }) => $textColor || ($variant === 'light' ? 'var(--color-text)' : 'var(--color-text-inverse)')};
  min-width: 80px;
  text-align: center;
  text-shadow: ${({ $variant }) => ($variant === 'light' ? 'none' : '0 2px 10px rgba(0, 0, 0, 0.3)')};
  padding: 0.3rem 0.6rem;
  background: ${({ $variant }) => ($variant === 'light' ? 'var(--color-surface-raised)' : 'color-mix(in srgb, var(--color-text-inverse) 12%, transparent)')};
  border-radius: 15px;
  border: 1px solid ${({ $variant }) => ($variant === 'light' ? 'var(--color-border)' : 'var(--color-border-inverse)')};
  backdrop-filter: blur(10px);
  box-shadow: ${({ $variant }) => ($variant === 'light' ? 'var(--shadow-sm)' : 'none')};
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  font: inherit;
  line-height: 1.2;

  ${({ $clickable }) =>
    $clickable &&
    `
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;

    &:hover {
      filter: brightness(0.98);
      box-shadow: 0 2px 8px rgba(40, 20, 10, 0.12);
    }

    &:focus-visible {
      outline: 2px solid var(--color-focus);
      outline-offset: 2px;
    }
  `}
  
  @media (max-width: 768px) {
    font-size: 0.7rem;
    min-width: 60px;
    padding: 0.25rem 0.4rem;
  }
`;

export const DatePickerInput = styled.input`
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
  border: 0;
  padding: 0;
  margin: 0;
`;

export const TimeInput = styled.input.withConfig({
  shouldForwardProp: (prop) => !['$variant', '$textColor'].includes(prop),
})`
  font: inherit;
  font-size: 0.72rem;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
  color: ${({ $variant, $textColor }) => $textColor || ($variant === 'light' ? 'var(--color-text)' : 'var(--color-text-inverse)')};
  min-width: 5.2rem;
  padding: 0.22rem 0.35rem;
  border-radius: 12px;
  border: 1px solid ${({ $variant }) => ($variant === 'light' ? 'var(--color-border)' : 'var(--color-border-inverse)')};
  background: ${({ $variant }) => ($variant === 'light' ? 'var(--color-surface-raised)' : 'color-mix(in srgb, var(--color-text-inverse) 12%, transparent)')};
  box-shadow: ${({ $variant }) => ($variant === 'light' ? 'var(--shadow-sm)' : 'none')};

  &:focus-visible {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
  }

  @media (max-width: 768px) {
    font-size: 0.64rem;
    min-width: 4.6rem;
    padding: 0.18rem 0.28rem;
  }
`;

export const ButtonGroup = styled.div`
  display: flex;
  gap: 0.2rem;
  
  @media (max-width: 768px) {
    gap: 0.15rem;
  }
`;

export const NavButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['primary', '$variant', '$textColor'].includes(prop),
})`
  padding: 0.25rem 0.4rem;
  border: none;
  background: ${({ primary, $variant }) => {
    if (primary) return $variant === 'light' ? 'var(--transit-primary-color, var(--color-brand))' : 'var(--color-accent-soft)';
    return $variant === 'light' ? 'var(--color-surface-raised)' : 'color-mix(in srgb, var(--color-text-inverse) 12%, transparent)';
  }};
  color: ${({ primary, $variant, $textColor }) => {
    if (primary) return $variant === 'light' ? 'var(--color-on-brand)' : 'var(--color-on-accent)';
    if ($textColor) return $textColor;
    return $variant === 'light' ? 'var(--color-brand)' : 'var(--color-accent-soft)';
  }};
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.65rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: ${({ $variant }) => ($variant === 'light' ? 'var(--shadow-sm)' : 'none')};
  backdrop-filter: blur(10px);
  min-width: 28px;
  min-height: 28px;
  border: ${({ $variant }) => ($variant === 'light' ? '1px solid var(--color-border)' : '1px solid var(--color-border-inverse)')};

  &:hover {
    background: ${({ primary, $variant }) => {
      if (primary) return $variant === 'light' ? 'var(--transit-primary-color, var(--color-brand-hover))' : 'var(--color-accent)';
      return $variant === 'light' ? 'var(--color-canvas-subtle)' : 'color-mix(in srgb, var(--color-text-inverse) 18%, transparent)';
    }};
    transform: translateY(-1px);
    box-shadow: ${({ $variant }) => ($variant === 'light' ? 'var(--shadow-card)' : 'none')};
  }

  @media (max-width: 768px) {
    padding: 0.2rem 0.3rem;
    font-size: 0.6rem;
    min-width: 24px;
    min-height: 24px;
  }
`;
