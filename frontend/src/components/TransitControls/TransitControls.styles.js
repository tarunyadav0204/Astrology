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
  shouldForwardProp: (prop) => !['$variant', '$clickable'].includes(prop),
})`
  font-size: 0.8rem;
  font-weight: 600;
  color: ${({ $variant }) => ($variant === 'light' ? '#7a2850' : '#ffffff')};
  min-width: 80px;
  text-align: center;
  text-shadow: ${({ $variant }) => ($variant === 'light' ? 'none' : '0 2px 10px rgba(0, 0, 0, 0.3)')};
  padding: 0.3rem 0.6rem;
  background: ${({ $variant }) => ($variant === 'light' ? 'rgba(255, 255, 255, 0.92)' : 'rgba(255, 255, 255, 0.15)')};
  border-radius: 15px;
  border: 1px solid ${({ $variant }) => ($variant === 'light' ? 'rgba(194, 24, 91, 0.14)' : 'rgba(255, 255, 255, 0.2)')};
  backdrop-filter: blur(10px);
  box-shadow: ${({ $variant }) => ($variant === 'light' ? '0 8px 16px rgba(194, 24, 91, 0.06)' : 'none')};
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
      outline: 2px solid #c2185b;
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

export const ButtonGroup = styled.div`
  display: flex;
  gap: 0.2rem;
  
  @media (max-width: 768px) {
    gap: 0.15rem;
  }
`;

export const NavButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['primary', '$variant'].includes(prop),
})`
  padding: 0.25rem 0.4rem;
  border: none;
  background: ${({ primary, $variant }) => {
    if (primary) return $variant === 'light' ? '#f59e0b' : 'rgba(255, 193, 7, 0.9)';
    return 'rgba(255, 255, 255, 0.96)';
  }};
  color: ${({ primary, $variant }) => {
    if (primary) return '#ffffff';
    return $variant === 'light' ? '#f97316' : '#ff7043';
  }};
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.65rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: ${({ $variant }) => ($variant === 'light' ? '0 6px 14px rgba(194, 24, 91, 0.08)' : '0 2px 8px rgba(0, 0, 0, 0.1)')};
  backdrop-filter: blur(10px);
  min-width: 28px;
  min-height: 28px;
  border: ${({ $variant }) => ($variant === 'light' ? '1px solid rgba(194, 24, 91, 0.12)' : 'none')};

  &:hover {
    background: ${({ primary, $variant }) => {
      if (primary) return $variant === 'light' ? '#f59e0b' : 'rgba(255, 193, 7, 1)';
      return 'rgba(255, 255, 255, 1)';
    }};
    transform: translateY(-1px);
    box-shadow: ${({ $variant }) => ($variant === 'light' ? '0 10px 18px rgba(194, 24, 91, 0.12)' : '0 4px 12px rgba(0, 0, 0, 0.15)')};
  }

  @media (max-width: 768px) {
    padding: 0.2rem 0.3rem;
    font-size: 0.6rem;
    min-width: 24px;
    min-height: 24px;
  }
`;
