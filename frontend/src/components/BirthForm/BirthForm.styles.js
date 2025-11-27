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
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.05);
`;

// --- Main Form Container ---

export const FormContainer = styled.div`
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
  background: #ffffff;
  border-radius: 24px;
  position: relative;
  overflow: visible;
  animation: ${fadeIn} 0.4s ease-out;

  h2 {
    color: #1e1b4b; /* Deep Indigo */
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 8px;
    text-align: center;
    letter-spacing: -0.5px;
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
  background: #f1f5f9; /* Slate 100 */
  border-radius: 16px;
  padding: 6px;
  margin-bottom: 32px;
  position: relative;
  z-index: 20; /* High Z-index to fix click issues */
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.03);
`;

export const TabButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['isFirst', 'isLast', 'active'].includes(prop)
})`
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 21;
  
  /* Active State */
  ${props => props.active ? css`
    background: white;
    color: #ea580c; /* Orange 600 */
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: scale(1);
  ` : css`
    background: transparent;
    color: #64748b; /* Slate 500 */
    &:hover {
      color: #334155;
    }
  `}
`;

export const TabContent = styled.div`
  height: 600px;
  min-height: 600px;
  overflow: visible;
  position: relative;
  z-index: 3;
`;

// --- Form Fields & Inputs ---

export const FormField = styled.div`
  margin-bottom: 20px;
  position: relative;
  
  .error {
    color: #ef4444;
    font-size: 12px;
    margin-top: 6px;
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
  margin-bottom: 8px;
  color: #334155; /* Slate 700 */
  font-weight: 600;
  font-size: 14px;
`;

const inputStyles = css`
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e2e8f0; /* Slate 200 */
  border-radius: 12px;
  font-size: 15px;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s ease;
  
  &::placeholder {
    color: #94a3b8;
  }

  &:hover {
    border-color: #cbd5e1;
    background: white;
  }

  &:focus {
    outline: none;
    border-color: #f97316; /* Orange 500 */
    background: white;
    box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
  }

  ${props => props.error && css`
    border-color: #ef4444;
    background: #fef2f2;
    
    &:focus {
      border-color: #ef4444;
      box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
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
  margin-bottom: 16px;
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
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 12px;
  padding: 8px;
  list-style: none;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.2);
  border: 1px solid #e2e8f0;
  z-index: 100;
  max-height: 240px;
  overflow-y: auto;
`;

export const SuggestionItem = styled.li`
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #475569;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    color: #0f172a;
  }
`;

// --- Action Buttons ---

export const Button = styled.button`
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); /* Orange gradient */
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
  margin-top: 12px;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(249, 115, 22, 0.4);
  }

  &:active {
    transform: translateY(0);
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
  height: 500px;
  overflow-y: auto;
  padding-right: 4px;

  /* Custom Scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
`;

export const ChartItem = styled.div`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s;
  cursor: pointer;

  &:hover {
    border-color: #fb923c;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transform: translateY(-1px);
  }

  strong {
    display: block;
    color: #1e293b;
    font-size: 16px;
    margin-bottom: 4px;
  }

  small {
    color: #64748b;
    font-size: 13px;
  }

  /* Buttons inside item */
  button {
    opacity: 0.8;
    transition: 0.2s;
    &:hover { opacity: 1; transform: scale(1.05); }
  }
`;
