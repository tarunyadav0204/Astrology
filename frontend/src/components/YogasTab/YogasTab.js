import React from 'react';
import DeskYogasPanel from '../BirthChart/DeskYogasPanel';

// Both web entry points deliberately use the canonical backend renderer.
export default function YogasTab({ birthData }) {
  return <DeskYogasPanel birthData={birthData} />;
}
