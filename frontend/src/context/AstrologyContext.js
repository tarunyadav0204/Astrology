import React, { createContext, useContext, useReducer } from 'react';

const AstrologyContext = createContext();

const initialState = {
  birthData: null,
  chartData: null,
  transitData: null,
  dashaData: null,
  loading: false,
  error: null
};

const astrologyReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_BIRTH_DATA':
      return { ...state, birthData: action.payload };
    case 'SET_CHART_DATA':
      return { ...state, chartData: action.payload, loading: false };
    case 'SET_TRANSIT_DATA':
      return { ...state, transitData: action.payload };
    case 'SET_DASHA_DATA':
      return { ...state, dashaData: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
};

export const AstrologyProvider = ({ children }) => {
  const [state, dispatch] = useReducer(astrologyReducer, initialState);

  const actions = {
    setBirthData: (data) => dispatch({ type: 'SET_BIRTH_DATA', payload: data }),
    setChartData: (data) => dispatch({ type: 'SET_CHART_DATA', payload: data }),
    setTransitData: (data) => dispatch({ type: 'SET_TRANSIT_DATA', payload: data }),
    setDashaData: (data) => dispatch({ type: 'SET_DASHA_DATA', payload: data }),
    setLoading: (loading) => dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error) => dispatch({ type: 'SET_ERROR', payload: error }),
    clearError: () => dispatch({ type: 'CLEAR_ERROR' })
  };

  return (
    <AstrologyContext.Provider value={{ ...state, ...actions }}>
      {children}
    </AstrologyContext.Provider>
  );
};

export const useAstrology = () => {
  const context = useContext(AstrologyContext);
  if (!context) {
    throw new Error('useAstrology must be used within AstrologyProvider');
  }
  return context;
};