import React from 'react';
import {Composition} from 'remotion';
import {VisualPodcast} from './visual-podcast';

export const Root = () => (
  <Composition
    id="AstroRoshniVisualPodcast"
    component={VisualPodcast}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={2700}
    defaultProps={{
      durationSeconds: 90,
      scenes: [],
      turns: [],
      chart: {planets: []},
      episodeTitle: 'Your Career Transition',
    }}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(30, Math.round(Number(props.durationSeconds || 90) * 30)),
    })}
  />
);

