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
  flex: 1;
  min-width: 300px;
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  
  @media (max-width: 768px) {
    min-width: unset;
    padding: 20px;
    border-radius: 12px;
  }
  
  h3 {
    color: #1f2937;
    margin-bottom: 20px;
    font-weight: 600;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
`;

export const SearchInput = styled.input`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #d1d5db;
  border-radius: 10px;
  font-size: 14px;
  margin-bottom: 16px;
  background: white;
  color: #1f2937;
  
  &:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }
  
  &::placeholder {
    color: #9ca3af;
  }
`;

export const ChartsList = styled.div`
  height: 450px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
`;

export const FormContainer = styled.div`
  max-width: 480px;
  margin: 0 auto;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  
  @media (max-width: 768px) {
    padding: 20px;
    margin: 0;
    border-radius: 12px;
    max-width: 100%;
  }
  
  h2 {
    text-align: center;
    color: #1f2937;
    margin-bottom: 24px;
    font-weight: 600;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    
    &::before {
      content: '🌟';
      font-size: 20px;
    }
  }
`;

export const FormField = styled.div`
  margin-bottom: 20px;
  
  .error {
    color: #ef4444;
    font-size: 13px;
    margin-top: 6px;
    display: block;
    font-weight: 500;
  }
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
  font-size: 14px;
`;

export const Input = styled.input`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid ${props => props.error ? '#ef4444' : '#d1d5db'};
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s ease;
  background: white;
  color: #1f2937;
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 14px 16px;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#ef4444' : '#2563eb'};
    box-shadow: 0 0 0 3px ${props => props.error ? 'rgba(239, 68, 68, 0.1)' : 'rgba(37, 99, 235, 0.1)'};
  }
  
  &::placeholder {
    color: #9ca3af;
  }
`;

export const Select = styled.select`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid ${props => props.error ? '#ef4444' : '#d1d5db'};
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.2s ease;
  background: white;
  cursor: pointer;
  color: #1f2937;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 5"><path fill="%236b7280" d="M2 0L0 2h4zm0 5L0 3h4z"/></svg>');
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 12px;
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 14px 16px;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#ef4444' : '#2563eb'};
    box-shadow: 0 0 0 3px ${props => props.error ? 'rgba(239, 68, 68, 0.1)' : 'rgba(37, 99, 235, 0.1)'};
  }
  
  option {
    color: #1f2937;
    background: white;
  }
`;

export const AutocompleteContainer = styled.div`
  position: relative;
`;

export const SuggestionList = styled.ul`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e1e8ed;
  border-top: none;
  border-radius: 0 0 8px 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

export const SuggestionItem = styled.li`
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: #f8f9fa;
  }
  
  &:last-child {
    border-bottom: none;
  }
`;

export const Button = styled.button`
  width: 100%;
  padding: 14px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  
  @media (max-width: 768px) {
    padding: 16px 24px;
    font-size: 16px;
  }
  
  &::before {
    content: '✨';
    font-size: 16px;
  }
  
  &:hover {
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;



export const ChartItem = styled.div`
  padding: 16px;
  margin-bottom: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  
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
    background: #f3f4f6;
    border-color: #d1d5db;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  background: #f8f9fa !important;
  border-radius: 0 !important;
  margin: 0 !important;
  border-bottom: 2px solid #e5e7eb !important;
  padding: 0 !important;
`;

export const TabButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['isFirst', 'isLast', 'active'].includes(prop)
})`
  flex: 1;
  padding: 12px 20px !important;
  background: ${props => props.active ? 'white !important' : 'transparent !important'};
  color: ${props => props.active ? '#2563eb !important' : '#6b7280 !important'};
  border: none !important;
  border-radius: 0 !important;
  cursor: pointer;
  font-weight: ${props => props.active ? '600' : '500'};
  transition: all 0.2s ease;
  font-size: 14px;
  border-bottom: ${props => props.active ? '2px solid #2563eb !important' : '2px solid transparent !important'};
  margin: 0 !important;
  
  &:hover {
    background: ${props => props.active ? 'white !important' : 'rgba(255, 255, 255, 0.7) !important'};
    color: #2563eb !important;
  }
`;

export const TabContent = styled.div`
  height: 600px;
  overflow: auto;
  padding: 20px;
  background: white;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
`;