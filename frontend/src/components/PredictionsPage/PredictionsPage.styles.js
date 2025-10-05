import styled from 'styled-components';

export const PredictionsContainer = styled.div`
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;

  h2 {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 30px;
  }
`;

export const YearSelector = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;

  label {
    font-weight: 600;
    color: #34495e;
  }

  select {
    padding: 8px 15px;
    border: 2px solid #bdc3c7;
    border-radius: 8px;
    font-size: 16px;
    background: white;
    cursor: pointer;

    &:focus {
      outline: none;
      border-color: #3498db;
    }
  }
`;

export const HouseGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
`;

export const HouseCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    border-color: #3498db;
  }

  h4 {
    margin: 0 0 8px 0;
    color: #2c3e50;
    font-size: 18px;
  }

  p {
    margin: 0 0 15px 0;
    color: #7f8c8d;
    font-size: 14px;
  }

  .strength-bar {
    width: 100%;
    height: 8px;
    background: #ecf0f1;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .strength-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .strength-text {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 600;
  }
`;

export const MonthGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
`;

export const MonthCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-left: 4px solid ${props => {
    switch (props.probability) {
      case 'High': return '#4CAF50';
      case 'Medium': return '#FF9800';
      case 'Low': return '#2196F3';
      default: return '#9E9E9E';
    }
  }};

  h4 {
    margin: 0 0 15px 0;
    color: #2c3e50;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .probability-badge {
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }

  .strength {
    font-size: 14px;
    color: #7f8c8d;
    margin-bottom: 10px;
  }

  .dasha-info, .transit-info {
    font-size: 13px;
    color: #34495e;
    margin-bottom: 8px;
  }

  .events {
    margin: 15px 0;
    
    strong {
      color: #2c3e50;
      font-size: 14px;
    }

    ul {
      margin: 8px 0 0 0;
      padding-left: 20px;
    }

    li {
      font-size: 13px;
      color: #7f8c8d;
      margin-bottom: 4px;
      text-transform: capitalize;
    }
  }

  .description {
    font-size: 13px;
    color: #95a5a6;
    font-style: italic;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #ecf0f1;
  }
`;

export const LoadingSpinner = styled.div`
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
  font-size: 16px;
`;