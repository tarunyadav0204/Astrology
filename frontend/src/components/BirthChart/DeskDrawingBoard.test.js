import { deskDrawingPoint } from './DeskDrawingBoard';

describe('deskDrawingPoint', () => {
  const rect = { left: 100, top: 50, width: 800, height: 400 };

  it('stores points relative to the full desk surface', () => {
    expect(deskDrawingPoint(500, 250, rect)).toEqual([0.5, 0.5]);
  });

  it('clamps pointer positions to the drawing surface', () => {
    expect(deskDrawingPoint(0, 900, rect)).toEqual([0, 1]);
  });
});
