import React from 'react';
import TermTooltip from './TermTooltip';

const ResponseRenderer = ({ response, terms = [], glossary = {} }) => {
  const renderContent = (content) => {
    if (!content) return null;

    // If content is already formatted HTML (from formatContent), don't decode entities again
    let processedContent = content;
    
    // Only decode HTML entities if content looks like raw content (contains &quot; etc)
    if (typeof content === 'string' && content.includes('&quot;')) {
      const textarea = document.createElement('textarea');
      textarea.innerHTML = content;
      processedContent = textarea.value;
    }
    
    // Split content by term tags and render with tooltips
    const termPattern = /<term id="([^"]+)">([^<]+)<\/term>/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = termPattern.exec(processedContent)) !== null) {
      // Add text before the term
      if (match.index > lastIndex) {
        parts.push(processedContent.slice(lastIndex, match.index));
      }

      // Add the term with tooltip
      const [fullMatch, termId, termText] = match;
      parts.push(
        <TermTooltip key={`${termId}-${match.index}`} termId={termId} glossary={glossary}>
          {termText}
        </TermTooltip>
      );

      lastIndex = match.index + fullMatch.length;
    }

    // Add remaining text
    if (lastIndex < processedContent.length) {
      parts.push(processedContent.slice(lastIndex));
    }

    return parts.length > 0 ? (
      <div>
        {parts.map((part, index) => 
          typeof part === 'string' ? (
            <span key={index} dangerouslySetInnerHTML={{ __html: part }} />
          ) : (
            part
          )
        )}
      </div>
    ) : (
      <div dangerouslySetInnerHTML={{ __html: processedContent }} />
    );
  };

  return (
    <div className="response-content">
      {renderContent(response)}
    </div>
  );
};

export default ResponseRenderer;