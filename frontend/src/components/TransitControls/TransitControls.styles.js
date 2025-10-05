import styled from 'styled-components';
import { APP_CONFIG } from '../../config/app.config';

export const ControlsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;

  @media (max-width: 768px) {
    gap: 0.3rem;
  }
`;

export const DateDisplay = styled.div`
  font-size: 0.8rem;
  font-weight: 600;
  color: #ffffff;
  min-width: 80px;
  text-align: center;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  padding: 0.3rem 0.6rem;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  
  @media (max-width: 768px) {
    font-size: 0.7rem;
    min-width: 60px;
    padding: 0.25rem 0.4rem;
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
  shouldForwardProp: (prop) => !['primary'].includes(prop),
})`
  padding: 0.25rem 0.4rem;
  border: none;
  background: ${props => props.primary ? 'rgba(255, 193, 7, 0.9)' : 'rgba(255, 255, 255, 0.9)'};
  color: ${props => props.primary ? '#ffffff' : '#ff7043'};
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.65rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  min-width: 28px;
  min-height: 28px;

  &:hover {
    background: ${props => props.primary ? 'rgba(255, 193, 7, 1)' : 'rgba(255, 255, 255, 1)'};
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  @media (max-width: 768px) {
    padding: 0.2rem 0.3rem;
    font-size: 0.6rem;
    min-width: 24px;
    min-height: 24px;
  }
`;