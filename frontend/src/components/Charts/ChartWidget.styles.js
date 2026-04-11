import styled, { css } from 'styled-components';

export const WidgetContainer = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;

  ${({ $embedInDashboard }) =>
    $embedInDashboard &&
    css`
      border-radius: 0;
      border: 1px solid #e5e0e3;
      box-shadow: none;
      background: #fff;
    `}
  
  @media (max-width: 768px) {
    min-height: 350px;
    overflow: visible;

    ${({ $embedInDashboard }) =>
      $embedInDashboard &&
      css`
        width: 100%;
        max-width: 100%;
        min-height: 0;
        flex: 1;
        border: none;
        border-radius: 0;
        margin: 0;
        box-sizing: border-box;
      `}
  }
  
  .nadi-mobile & {
    background: transparent;
    border-radius: 0;
    border: none;
    box-shadow: none;
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
  gap: 0.5rem;
  min-width: 0;

  ${({ $embedInDashboard }) =>
    $embedInDashboard &&
    css`
      background: #f3f1f2;
      border-bottom: 1px solid #e5e0e3;
      border-radius: 0;
      padding: 0.32rem 0.5rem;
    `}
  
  @media (max-width: 768px) {
    padding: 0.5rem 0.75rem;
    gap: 0.25rem;
    min-height: 44px;
    flex-wrap: nowrap;

    ${({ $embedInDashboard }) =>
      $embedInDashboard &&
      css`
        padding: 0 max(0px, env(safe-area-inset-left, 0px)) 0 max(0px, env(safe-area-inset-right, 0px));
        min-height: 36px;
      `}
  }
`;

export const WidgetTitle = styled.h3`
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #8b4513;
  text-shadow: none;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  ${({ $embedInDashboard }) =>
    $embedInDashboard &&
    css`
      color: #3d3a3c;
      font-weight: 600;
      font-size: 0.8rem;
      letter-spacing: 0.01em;
    `}
  
  @media (max-width: 768px) {
    font-size: 0.85rem;
    flex: 0 1 auto;
    max-width: 120px;

    ${({ $embedInDashboard }) =>
      $embedInDashboard &&
      css`
        font-size: 0.78rem;
        max-width: min(42%, 140px);
      `}
  }
`;

export const StyleToggle = styled.button`
  padding: 4px 8px;
  background: white;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  font-size: 10px;
  font-weight: 500;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 1);
    transform: translateY(-1px);
  }
  
  @media (max-width: 768px) {
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 500;
    min-width: auto;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
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
  overflow: hidden;

  ${({ $embedInDashboard }) =>
    $embedInDashboard &&
    css`
      border-radius: 0;
      background: #fff;
      padding: 0.15rem 0.2rem 0.35rem;
    `}
  
  svg {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    min-height: 300px;
  }
  
  @media (max-width: 768px) {
    padding: 0;

    ${({ $embedInDashboard }) =>
      $embedInDashboard &&
      css`
        padding: 0;
        margin: 0;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
      `}
    
    svg {
      min-height: 280px;
      width: 100%;
      height: auto;
      aspect-ratio: 1;
    }

    ${({ $embedInDashboard }) =>
      $embedInDashboard &&
      css`
        svg {
          min-height: 0;
          width: 100%;
          max-width: 100%;
        }
      `}
  }
`;