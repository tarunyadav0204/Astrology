import styled from 'styled-components';

export const WidgetContainer = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  
  @media (max-width: 768px) {
    min-height: 350px;
  }
`;

export const WidgetHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid rgba(225, 112, 85, 0.15);
  background: linear-gradient(135deg, #ffb3a7 0%, #ffa094 100%);
  border-radius: 15px 15px 0 0;
  flex-shrink: 0;
  
  @media (max-width: 768px) {
    padding: 0.6rem 1rem;
  }
`;

export const WidgetTitle = styled.h3`
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #8b4513;
  text-shadow: none;
  
  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

export const StyleToggle = styled.button`
  padding: 0.3rem 0.8rem;
  background: rgba(255, 255, 255, 0.9);
  color: #8b4513;
  border: none;
  border-radius: 15px;
  cursor: pointer;
  font-size: 0.7rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
  min-height: 32px;

  &:hover {
    background: rgba(255, 255, 255, 1);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(255, 255, 255, 0.5);
  }
  
  @media (max-width: 768px) {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    min-height: 36px;
  }
`;

export const ChartContainer = styled.div`
  flex: 1;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 0 0 15px 15px;
  position: relative;
  
  svg {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    min-height: 300px;
  }
  
  @media (max-width: 768px) {
    padding: 0.5rem;
    
    svg {
      min-height: 280px;
      width: 100%;
      height: auto;
      aspect-ratio: 1;
    }
  }
`;