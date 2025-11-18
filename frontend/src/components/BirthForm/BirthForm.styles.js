import styled from 'styled-components';
import { APP_CONFIG } from '../../config/app.config';

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
  
  @media (max-width: 768px) {
    min-width: unset;
  }
`;

export const ChartsPanel = styled.div`
  max-width: 440px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: none;
  border: none;
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 3;
  
  @media (max-width: 768px) {
    padding: 20px;
    border-radius: 16px;
    max-width: 100%;
  }
  
  h3 {
    display: none;
  }
`;

export const SearchInput = styled.input`
  width: 100%;
  max-width: 440px;
  margin: 0 auto 16px auto;
  display: block;
  padding: 16px 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  color: #1f2937;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:focus {
    outline: none;
    border-color: rgba(255, 255, 255, 0.8);
    box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.3), 0 12px 40px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 1);
    transform: translateY(-2px);
  }
  
  &:hover {
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-1px);
    box-shadow: 0 10px 36px rgba(0, 0, 0, 0.12);
  }
  
  &::placeholder {
    color: #9ca3af;
  }
`;

export const ChartsList = styled.div`
  height: 450px;
  overflow-y: auto;
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #ff6b6b, #ee5a24);
    border-radius: 10px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #ff5252, #d63031);
  }
`;

export const FormContainer = styled.div`
  max-width: 480px;
  margin: 0 auto;
  padding: 0;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%);
  border-radius: 0;
  box-shadow: none;
  border: none;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.9) 0%, rgba(238, 90, 36, 0.9) 50%, rgba(255, 159, 243, 0.9) 100%);
    z-index: 1;
  }
  
  &::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: float 6s ease-in-out infinite;
    z-index: 2;
  }
  
  @keyframes float {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    33% { transform: translate(30px, -30px) rotate(120deg); }
    66% { transform: translate(-20px, 20px) rotate(240deg); }
  }
  
  @media (max-width: 768px) {
    padding: 0;
    margin: 0;
    border-radius: 0;
    max-width: 100%;
  }
  
  h2 {
    display: none;
  }
  
  @keyframes sparkle {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.2) rotate(180deg); opacity: 0.8; }
  }
`;

export const FormField = styled.div`
  margin-bottom: 24px;
  position: relative;
  z-index: 3;
  
  .error {
    color: #fecaca;
    font-size: 13px;
    margin-top: 8px;
    display: block;
    font-weight: 500;
    background: rgba(239, 68, 68, 0.1);
    padding: 6px 12px;
    border-radius: 8px;
    border-left: 3px solid #ef4444;
  }
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 12px;
  color: white;
  font-weight: 600;
  font-size: 15px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
`;

export const Input = styled.input`
  width: 100%;
  padding: 16px 20px;
  border: 2px solid ${props => props.error ? 'rgba(239, 68, 68, 0.5)' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 16px;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  color: #1f2937;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 18px 20px;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#ef4444' : 'rgba(255, 255, 255, 0.8)'};
    box-shadow: 0 0 0 4px ${props => props.error ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.3)'}, 0 12px 40px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 1);
    transform: translateY(-2px);
  }
  
  &::placeholder {
    color: #9ca3af;
    font-weight: 400;
  }
  
  &:hover {
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-1px);
    box-shadow: 0 10px 36px rgba(0, 0, 0, 0.12);
  }
`;

export const Select = styled.select`
  width: 100%;
  padding: 16px 20px;
  border: 2px solid ${props => props.error ? 'rgba(239, 68, 68, 0.5)' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 16px;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  cursor: pointer;
  color: #1f2937;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 5"><path fill="%236b7280" d="M2 0L0 2h4zm0 5L0 3h4z"/></svg>');
  background-repeat: no-repeat;
  background-position: right 20px center;
  background-size: 14px;
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 18px 20px;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#ef4444' : 'rgba(255, 255, 255, 0.8)'};
    box-shadow: 0 0 0 4px ${props => props.error ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.3)'}, 0 12px 40px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 1);
    transform: translateY(-2px);
  }
  
  &:hover {
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-1px);
    box-shadow: 0 10px 36px rgba(0, 0, 0, 0.12);
  }
  
  option {
    color: #1f2937;
    background: white;
    padding: 8px;
  }
`;

export const AutocompleteContainer = styled.div`
  position: relative;
`;

export const SuggestionList = styled.ul`
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-bottom: none;
  border-radius: 16px 16px 0 0;
  max-height: 200px;
  overflow-y: auto;
  z-index: 999999;
  box-shadow: 0 -12px 40px rgba(0, 0, 0, 0.15);
`;

export const SuggestionItem = styled.li`
  padding: 16px 20px;
  cursor: pointer;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #1f2937;
  font-weight: 500;
  
  &:hover {
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(238, 90, 36, 0.1));
    transform: translateX(4px);
    color: #ee5a24;
  }
  
  &:first-child {
    border-top: none;
    border-radius: 16px 16px 0 0;
  }
`;

export const Button = styled.button`
  width: 100%;
  padding: 18px 32px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #ff9ff3 100%);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  position: relative;
  overflow: hidden;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 12px 40px rgba(255, 107, 107, 0.4);
  z-index: 3;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.6s;
  }
  
  &::after {
    content: '🚀';
    font-size: 20px;
    animation: rocket 2s ease-in-out infinite;
  }
  
  @keyframes rocket {
    0%, 100% { transform: translateX(0) rotate(0deg); }
    50% { transform: translateX(4px) rotate(10deg); }
  }
  
  @media (max-width: 768px) {
    padding: 20px 32px;
    font-size: 18px;
  }
  
  &:hover {
    background: linear-gradient(135deg, #ff5252 0%, #d63031 50%, #fd79a8 100%);
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 20px 60px rgba(255, 107, 107, 0.6);
    
    &::before {
      left: 100%;
    }
  }
  
  &:active {
    transform: translateY(-2px) scale(1.01);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;



export const ChartItem = styled.div`
  padding: 16px;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    
    > div:last-child {
      align-self: stretch;
      justify-content: center;
    }
  }
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }
  
  &:last-child {
    margin-bottom: 0;
  }
`;

export const TabContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
`;

export const TabNavigation = styled.div`
  display: flex;
  background: rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px !important;
  margin: 0 0 24px 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  padding: 4px !important;
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 3;
`;

export const TabButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['isFirst', 'isLast', 'active'].includes(prop)
})`
  flex: 1;
  padding: 12px 20px !important;
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.9) !important' : 'transparent !important'};
  color: ${props => props.active ? '#ee5a24 !important' : 'rgba(255, 255, 255, 0.8) !important'};
  border: none !important;
  border-radius: 12px !important;
  cursor: pointer;
  font-weight: ${props => props.active ? '700' : '500'};
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  margin: 0 !important;
  backdrop-filter: blur(10px);
  box-shadow: ${props => props.active ? '0 4px 20px rgba(238, 90, 36, 0.3) !important' : 'none !important'};
  
  &:hover {
    background: ${props => props.active ? 'rgba(255, 255, 255, 0.95) !important' : 'rgba(255, 255, 255, 0.2) !important'};
    color: ${props => props.active ? '#ee5a24 !important' : 'white !important'};
    transform: translateY(-1px);
  }
`;

export const TabContent = styled.div`
  height: 600px;
  overflow: auto;
  padding: 0;
  background: transparent;
  position: relative;
  z-index: 3;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #ff6b6b, #ee5a24);
    border-radius: 10px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #ff5252, #d63031);
  }
`;