import styled from 'styled-components';
import { APP_CONFIG } from '../../config/app.config';

export const TwoPanelContainer = styled.div`
  display: flex;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  
  @media (max-width: ${APP_CONFIG.ui.breakpoints.tablet || '768px'}) {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
`;

export const FormPanel = styled.div`
  flex: 1;
  min-width: 400px;
`;

export const ChartsPanel = styled.div`
  flex: 1;
  min-width: 400px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 1.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  
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
  padding: 0.75rem;
  border: 2px solid rgba(233, 30, 99, 0.2);
  border-radius: 12px;
  font-size: 1rem;
  margin-bottom: 1rem;
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
  max-height: 500px;
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
  padding: 2rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  
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
    margin-bottom: 2rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    
    &::before {
      content: '✨';
      font-size: 1.5rem;
    }
  }

  @media (max-width: ${APP_CONFIG.ui.breakpoints.mobile}) {
    padding: 1.5rem;
    margin: 1rem;
  }
`;

export const FormField = styled.div`
  margin-bottom: 1.5rem;
  
  .error {
    color: #e74c3c;
    font-size: 0.875rem;
    margin-top: 0.5rem;
    display: block;
  }
`;

export const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  color: #e91e63;
  font-weight: 600;
  font-size: 0.95rem;
`;

export const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid ${props => props.error ? '#e74c3c' : 'rgba(233, 30, 99, 0.2)'};
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  
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
  padding: 1rem;
  background: linear-gradient(135deg, #e91e63 0%, #ff6f00 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
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
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(233, 30, 99, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  
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