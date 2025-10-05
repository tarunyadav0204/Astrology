import styled from 'styled-components';

export const WidgetContainer = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
`;

export const WidgetHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0.6rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #ffcc80 0%, #ff8a65 100%);
  border-radius: 16px 16px 0 0;
`;

export const WidgetTitle = styled.h3`
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  
  &::before {
    content: '🌟';
    font-size: 0.9rem;
  }
`;

export const DashaContainer = styled.div`
  flex: 1;
  padding: 0.4rem;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 0 0 16px 16px;
  backdrop-filter: blur(10px);
`;

export const DashaTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 0.7rem;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
`;

export const DashaRow = styled.tr.withConfig({
  shouldForwardProp: (prop) => !['current', 'selected'].includes(prop),
})`
  cursor: pointer;
  background: ${props => {
    if (props.selected) return 'rgba(233, 30, 99, 0.15)';
    if (props.current) return 'rgba(255, 111, 0, 0.15)';
    return 'transparent';
  }};
  color: #2d3436;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 171, 145, 0.2);
    color: #2d3436;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  
  &:nth-child(even) {
    background: ${props => {
      if (props.selected) return 'rgba(233, 30, 99, 0.15)';
      if (props.current) return 'rgba(255, 111, 0, 0.15)';
      return 'rgba(255, 243, 224, 0.3)';
    }};
  }
`;

export const DashaCell = styled.td`
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(116, 185, 255, 0.2);
  text-align: left;
  font-weight: 500;
  
  &:first-child {
    font-weight: 700;
    color: inherit;
    
    &::before {
      content: '🪐 ';
      margin-right: 0.2rem;
    }
  }
  
  &:nth-child(2), &:nth-child(3) {
    color: #000;
  }
  
  th& {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    color: #495057;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.6rem;
    letter-spacing: 0.3px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    
    &:first-child::before {
      content: '🌍 ';
    }
    
    &:nth-child(2)::before {
      content: '📅 ';
    }
    
    &:nth-child(3)::before {
      content: '🏁 ';
    }
  }
`;