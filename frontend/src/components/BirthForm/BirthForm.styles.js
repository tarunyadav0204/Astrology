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
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 1.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  
  @media (max-width: 768px) {
    min-width: unset;
    padding: 1rem;
    border-radius: 15px;
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #e91e63, #f06292, #ff6f00, #ff8a65, #ffab91);
    z-index: 1;
  }
  
  h3 {
    color: #e91e63;
    margin-bottom: 1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
`;

export const SearchInput = styled.input`
  width: 100%;
  padding: 0.5rem;
  border: 2px solid rgba(233, 30, 99, 0.2);
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  
  &:focus {
    outline: none;
    border-color: #e91e63;
    box-shadow: 0 0 0 3px rgba(233, 30, 99, 0.1);
    background: rgba(255, 255, 255, 1);
  }
  
  &::placeholder {
    color: #ff8a65;
  }
`;

export const ChartsList = styled.div`
  max-height: 300px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(233, 30, 99, 0.1);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #e91e63, #ff6f00);
    border-radius: 3px;
  }
`;

export const FormContainer = styled.div`
  max-width: 500px;
  margin: 0 auto;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  
  @media (max-width: 768px) {
    padding: 0.5rem;
    margin: 0;
    border-radius: 15px;
    max-width: 100%;
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #e91e63, #f06292, #ff6f00, #ff8a65, #ffab91);
    z-index: 1;
  }
  
  h2 {
    text-align: center;
    color: #e91e63;
    margin-bottom: 1rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 1.2rem;
    
    &::before {
      content: '✨';
      font-size: 1.2rem;
    }
  }


`;

export const FormField = styled.div`
  margin-bottom: 0.75rem;
  
  .error {
    color: #e74c3c;
    font-size: 0.75rem;
    margin-top: 0.25rem;
    display: block;
  }
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 0.25rem;
  color: #e91e63;
  font-weight: 600;
  font-size: 0.85rem;
`;

export const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  border: 2px solid ${props => props.error ? '#e74c3c' : 'rgba(233, 30, 99, 0.2)'};
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  min-height: 36px;
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 0.6rem;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#e74c3c' : '#e91e63'};
    box-shadow: 0 0 0 3px ${props => props.error ? 'rgba(231, 76, 60, 0.1)' : 'rgba(233, 30, 99, 0.1)'};
    background: rgba(255, 255, 255, 1);
  }
  
  &::placeholder {
    color: #ff8a65;
  }
`;

export const Select = styled.select`
  width: 100%;
  padding: 0.5rem;
  border: 2px solid ${props => props.error ? '#e74c3c' : 'rgba(233, 30, 99, 0.2)'};
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  min-height: 36px;
  cursor: pointer;
  color: #333;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 5"><path fill="%23e91e63" d="M2 0L0 2h4zm0 5L0 3h4z"/></svg>');
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 10px;
  
  @media (max-width: 768px) {
    font-size: 16px;
    padding: 0.6rem;
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.error ? '#e74c3c' : '#e91e63'};
    box-shadow: 0 0 0 3px ${props => props.error ? 'rgba(231, 76, 60, 0.1)' : 'rgba(233, 30, 99, 0.1)'};
    background: rgba(255, 255, 255, 1);
  }
  
  option {
    color: #333;
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
  padding: 0.75rem;
  background: linear-gradient(135deg, #e91e63 0%, #ff6f00 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 40px;
  
  @media (max-width: 768px) {
    padding: 0.8rem;
    font-size: 0.9rem;
  }
  
  &::before {
    content: '🚀';
    font-size: 1.2rem;
  }
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(233, 30, 99, 0.4);
    background: linear-gradient(135deg, #ff6f00 0%, #e91e63 100%);
  }
  
  &:active {
    transform: translateY(-1px);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;



export const ChartItem = styled.div`
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(233, 30, 99, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    
    > div:last-child {
      align-self: stretch;
      justify-content: center;
    }
  }
  
  &:hover {
    background: linear-gradient(135deg, rgba(233, 30, 99, 0.1) 0%, rgba(255, 111, 0, 0.1) 100%);
    border-color: #e91e63;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(233, 30, 99, 0.2);
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
  border-bottom: 2px solid rgba(233, 30, 99, 0.2);
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px 8px 0 0;
`;

export const TabButton = styled.button`
  flex: 1;
  padding: 8px 16px;
  background: ${props => props.active ? 'rgba(233, 30, 99, 0.2)' : 'transparent'};
  color: ${props => props.active ? '#e91e63' : '#666'};
  border: none;
  border-radius: ${props => props.isFirst ? '8px 0 0 0' : props.isLast ? '0 8px 0 0' : '0'};
  cursor: pointer;
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  transition: all 0.3s ease;
  font-size: 13px;
  
  &:hover {
    background: rgba(233, 30, 99, 0.1);
    color: #e91e63;
  }
`;

export const TabContent = styled.div`
  flex: 1;
  overflow: auto;
`;