import React from 'react';

/**
 * Lightweight formatter for chatbot responses.
 * Formats **bold**, *italic*, bullet points (`•`, `-`), numbered lists (`1. `), and paragraphs.
 */
export default function FormattedMessage({ text }) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (!line) {
      elements.push(<div key={`spacer-${i}`} style={{ height: '8px' }} />);
      continue;
    }

    // Check for bullet point
    const isBullet = line.startsWith('• ') || line.startsWith('- ') || line.startsWith('* ');
    const isNumbered = /^\d+\.\s/.test(line);

    const cleanLine = isBullet
      ? line.replace(/^[•\-\*]\s+/, '')
      : isNumbered
      ? line.replace(/^\d+\.\s+/, '')
      : line;

    // Parse **bold** within the line
    const parts = [];
    const regex = /\*\*(.*?)\*\*/g;
    let lastIdx = 0;
    let match;

    while ((match = regex.exec(cleanLine)) !== null) {
      if (match.index > lastIdx) {
        parts.push(cleanLine.substring(lastIdx, match.index));
      }
      parts.push(<strong key={`b-${i}-${match.index}`}>{match[1]}</strong>);
      lastIdx = regex.lastIndex;
    }
    if (lastIdx < cleanLine.length) {
      parts.push(cleanLine.substring(lastIdx));
    }

    if (isBullet) {
      elements.push(
        <div key={`line-${i}`} style={{ display: 'flex', gap: '8px', margin: '3px 0' }}>
          <span style={{ color: 'var(--lime)', flexShrink: 0 }}>•</span>
          <span>{parts}</span>
        </div>
      );
    } else if (isNumbered) {
      const numMatch = line.match(/^(\d+)\.\s/);
      const num = numMatch ? numMatch[1] : '';
      elements.push(
        <div key={`line-${i}`} style={{ display: 'flex', gap: '8px', margin: '3px 0' }}>
          <span style={{ color: 'var(--lime)', fontWeight: 600, flexShrink: 0 }}>{num}.</span>
          <span>{parts}</span>
        </div>
      );
    } else {
      elements.push(
        <p key={`line-${i}`} style={{ margin: '3px 0', lineHeight: 1.55 }}>
          {parts}
        </p>
      );
    }
  }

  return <div className="formatted-msg">{elements}</div>;
}
