import styled, { keyframes, css } from 'styled-components';

// --- Animations ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const shimmer = keyframes`
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
`;

// --- Layout Containers ---

export const TwoPanelContainer = styled.div`
  display: flex;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    padding: 0.5rem;
  }
`;

export const FormPanel = styled.div`
  flex: 1;
  min-width: 300px;
`;

export const ChartsPanel = styled.div`
  max-width: 440px;
  margin: 0 auto;
  background: white;
  border-radius: 0;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.05);
`;

// --- Main Form Container ---

export const FormContainer = styled.div`
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
  background: transparent;
  border-radius: 18px;
  position: relative;
  overflow: visible;
  animation: ${fadeIn} 0.25s ease-out;

  h2 {
    color: var(--color-text);
    font-size: 18px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.2px;
  }
`;

// --- Tabs (Segmented Control Style) ---

export const TabContainer = styled.div`
  width: 100%;
  display: flex;
  flex-direction: column;
`;

export const TabNavigation = styled.div`
  display: flex;
  gap: 6px;
  background: var(--color-surface-muted);
  border-radius: 14px;
  padding: 5px;
  margin: 16px 24px 18px;
  position: relative;
  z-index: 20;
  border: 1px solid var(--color-border);

  @media (max-width: 560px) {
    margin: 14px 16px;
  }
`;

export const TabButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['isFirst', 'isLast', 'active'].includes(prop)
})`
  flex: 1;
  min-height: 42px;
  padding: 9px 16px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 750;
  transition: all 0.2s ease;
  position: relative;
  z-index: 21;
  
  /* Active State */
  ${props => props.active ? css`
    background: var(--color-surface-raised);
    color: var(--color-brand);
    box-shadow: var(--shadow-sm);
  ` : css`
    background: transparent;
    color: var(--color-text-muted);
    &:hover {
      color: var(--color-text);
      background: color-mix(in srgb, var(--color-surface-raised) 52%, transparent);
    }
  `}
`;

export const TabContent = styled.div`
  min-height: 0;
  overflow: visible;
  position: relative;
  z-index: 3;
`;

// --- Form Fields & Inputs ---

export const FormField = styled.div`
  margin: 0;
  position: relative;
  
  .error {
    color: var(--color-danger);
    font-size: 11px;
    margin-top: 5px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4px;
    
    &::before {
      content: '⚠️';
      font-size: 10px;
    }
  }
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 6px;
  color: var(--color-text);
  font-weight: 750;
  font-size: 12px;
  letter-spacing: 0.01em;
`;

const inputStyles = css`
  width: 100%;
  min-height: 46px;
  padding: 11px 13px;
  border: 1px solid var(--color-border-strong);
  border-radius: 11px;
  font-size: 14px;
  color: var(--color-text);
  background: var(--color-surface-raised);
  color-scheme: inherit;
  transition: all 0.2s ease;
  
  &::placeholder {
    color: var(--color-text-subtle);
  }

  &:hover {
    border-color: var(--color-border-strong);
    background: var(--color-surface);
  }

  &:focus {
    outline: none;
    border-color: var(--color-focus);
    background: var(--color-surface-raised);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-focus) 18%, transparent);
  }

  ${props => props.error && css`
    border-color: var(--color-danger);
    background: color-mix(in srgb, var(--color-danger) 6%, var(--color-surface-raised));
    
    &:focus {
      border-color: var(--color-danger);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-danger) 16%, transparent);
    }
  `}
`;

export const Input = styled.input`
  ${inputStyles}
`;

export const Select = styled.select`
  ${inputStyles}
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 14px center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
`;

// --- Search & Autocomplete ---

export const SearchInput = styled(Input)`
  margin-bottom: 0;
  background-image: none;
  padding-left: 42px;
`;

export const AutocompleteContainer = styled.div`
  position: relative;
`;

export const SuggestionList = styled.ul`
  position: absolute;
  bottom: calc(100% + 6px);
  top: auto;
  left: 0;
  right: 0;
  background: var(--color-surface-raised);
  border-radius: 12px;
  padding: 6px;
  list-style: none;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  z-index: 2000;
  max-height: min(240px, 40vh);
  overflow-y: auto;
`;

export const SuggestionItem = styled.li`
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text);
  transition: all 0.15s;

  &:hover {
    background: var(--color-surface-muted);
    color: var(--color-brand);
  }
`;

// --- Action Buttons ---

export const Button = styled.button`
  width: 100%;
  min-height: 48px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--color-brand) 0%, var(--color-brand-hover) 100%);
  color: var(--color-on-brand);
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  margin-top: 0;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-card);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: var(--color-surface-muted);
    color: var(--color-text-subtle);
    box-shadow: none;
    cursor: not-allowed;
    transform: none;
  }
  
  /* Subtle Shine Effect */
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 200%;
    height: 100%;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.2), transparent);
    transform: skewX(-20deg) translateX(-150%);
    transition: 0.5s;
  }

  &:hover::after {
    transform: skewX(-20deg) translateX(50%);
    transition: 0.5s;
  }
`;

// --- Charts List ---

export const ChartsList = styled.div`
  min-height: 120px;
  max-height: min(52vh, 480px);
  overflow-y: auto;
  padding: 2px 4px 2px 2px;

  /* Custom Scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border-strong);
    border-radius: 999px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-subtle);
  }
`;

export const LoadMoreButton = styled.button`
  width: 100%;
  margin-top: 12px;
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;

  &:hover:not(:disabled) {
    background: color-mix(in srgb, var(--color-brand) 10%, var(--color-surface-muted));
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

export const ChartItem = styled.div`
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 13px 14px;
  margin-bottom: 9px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s;
  cursor: pointer;

  &:hover {
    border-color: var(--color-brand);
    box-shadow: var(--shadow-sm);
    transform: translateY(-1px);
  }

  strong {
    display: block;
    color: var(--color-text);
    font-size: 14px;
    margin-bottom: 4px;
  }

  small {
    color: var(--color-text-muted);
    font-size: 11px;
  }

`;
