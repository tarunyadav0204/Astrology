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
    color: #2d1b22;
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
  background: #f5eae5;
  border-radius: 14px;
  padding: 5px;
  margin: 16px 24px 18px;
  position: relative;
  z-index: 20;
  border: 1px solid rgba(105, 55, 63, 0.08);

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
    background: #ffffff;
    color: #9f1239;
    box-shadow: 0 4px 14px rgba(84, 38, 49, 0.1);
  ` : css`
    background: transparent;
    color: #725f63;
    &:hover {
      color: #3f2930;
      background: rgba(255,255,255,0.48);
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
    color: #b4233c;
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
  color: #49363c;
  font-weight: 750;
  font-size: 12px;
  letter-spacing: 0.01em;
`;

const inputStyles = css`
  width: 100%;
  min-height: 46px;
  padding: 11px 13px;
  border: 1px solid #daccc7;
  border-radius: 11px;
  font-size: 14px;
  color: #2d1b22;
  background: #fffdfb;
  transition: all 0.2s ease;
  
  &::placeholder {
    color: #9a898d;
  }

  &:hover {
    border-color: #bfa8a1;
    background: white;
  }

  &:focus {
    outline: none;
    border-color: #b53a5d;
    background: white;
    box-shadow: 0 0 0 3px rgba(181, 58, 93, 0.11);
  }

  ${props => props.error && css`
    border-color: #c73b52;
    background: #fff7f7;
    
    &:focus {
      border-color: #c73b52;
      box-shadow: 0 0 0 3px rgba(199, 59, 82, 0.1);
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
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: left 14px center;
  background-size: 20px;
  padding-left: 44px;
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
  background: white;
  border-radius: 12px;
  padding: 6px;
  list-style: none;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid #daccc7;
  z-index: 2000;
  max-height: min(240px, 40vh);
  overflow-y: auto;
`;

export const SuggestionItem = styled.li`
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #475569;
  transition: all 0.15s;

  &:hover {
    background: #fff1ed;
    color: #7f1838;
  }
`;

// --- Action Buttons ---

export const Button = styled.button`
  width: 100%;
  min-height: 48px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #a71945 0%, #c54a43 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 20px rgba(159, 18, 57, 0.2);
  margin-top: 0;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 26px rgba(159, 18, 57, 0.28);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: #d9cbc7;
    color: #8b7a7e;
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
    background: #cbd5e1;
    border-radius: 999px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
`;

export const LoadMoreButton = styled.button`
  width: 100%;
  margin-top: 12px;
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  background: #f3e7e2;
  color: #5c3b43;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;

  &:hover:not(:disabled) {
    background: rgba(0, 0, 0, 0.1);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

export const ChartItem = styled.div`
  background: #fffdfb;
  border: 1px solid #e4d7d1;
  border-radius: 14px;
  padding: 13px 14px;
  margin-bottom: 9px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s;
  cursor: pointer;

  &:hover {
    border-color: #c66a78;
    box-shadow: 0 8px 20px rgba(79, 38, 48, 0.08);
    transform: translateY(-1px);
  }

  strong {
    display: block;
    color: #332127;
    font-size: 14px;
    margin-bottom: 4px;
  }

  small {
    color: #79676b;
    font-size: 11px;
  }

`;
