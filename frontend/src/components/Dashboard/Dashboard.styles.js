import styled from 'styled-components';
import { APP_CONFIG } from '../../config/app.config';

export const DashboardContainer = styled.div`
  height: 100vh;
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%);
  margin: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="stars" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="%23ffffff" opacity="0.3"/></pattern></defs><rect width="100" height="100" fill="url(%23stars)"/></svg>');
    pointer-events: none;
  }
`;

export const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: 55vh 25vh;
  gap: 0.3rem;
  row-gap: 0.5rem;
  padding: 0.5rem;
  max-width: 100vw;
  margin: 0;
  flex: 1;

  @media (max-width: ${APP_CONFIG.ui.breakpoints.mobile}) {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    height: auto;
    padding: 0.5rem 0.25rem;
  }
`;

export const GridItem = styled.div.withConfig({
  shouldForwardProp: (prop) => !['chart', 'dasha', 'chartSpan'].includes(prop),
})`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  backdrop-filter: blur(20px);
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
  
  &:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    border-color: rgba(255, 255, 255, 0.6);
    background: rgba(255, 255, 255, 1);
  }
  
  ${props => props.chart && `
    grid-column: span 1;
    grid-row: 1;
    height: 100%;
  `}
  
  ${props => props.dasha && `
    grid-column: span 1;
    grid-row: 2;
    height: 100%;
    overflow: hidden;
  `}
  
  ${props => props.chartSpan && `
    grid-column: span 2;
  `}
`;

export const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 1rem;
  background: linear-gradient(135deg, #e91e63 0%, #ff6f00 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 0;
  z-index: 100;
  height: 40px;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);

  @media (max-width: ${APP_CONFIG.ui.breakpoints.mobile}) {
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    height: auto;
  }
`;

export const BackButton = styled.button`
  padding: 0.2rem 0.6rem;
  background: linear-gradient(135deg, #ff8a65 0%, #e91e63 100%);
  color: white;
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 15px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 1px 4px rgba(255, 107, 107, 0.4);
  display: flex;
  align-items: center;
  gap: 0.2rem;
  
  &::before {
    content: '🏠';
    font-size: 0.8rem;
  }

  &:hover {
    background: linear-gradient(135deg, #feca57 0%, #ff6b6b 100%);
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(255, 107, 107, 0.6);
  }
`;

export const Title = styled.h1`
  margin: 0;
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: none;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  
  &::before {
    content: '✨';
    font-size: 2.2rem;
    animation: sparkle 2s ease-in-out infinite alternate;
  }
  
  @keyframes sparkle {
    0% { transform: scale(1) rotate(0deg); }
    100% { transform: scale(1.1) rotate(5deg); }
  }

  @media (max-width: ${APP_CONFIG.ui.breakpoints.mobile}) {
    font-size: 1.6rem;
    text-align: center;
  }
`;