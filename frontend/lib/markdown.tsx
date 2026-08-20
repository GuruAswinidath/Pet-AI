import React, { Fragment } from "react";

// Small markdown-lite renderer: paragraphs, "- " bullet lists, **bold**.
// The Conversation/Knowledge agents reply in plain sentences, but this
// lets richer structured answers render nicely without a markdown library.

function renderInline(text: string, keyPrefix: string): React.ReactNode {
  const parts = text.split(/(\*\*.+?\*\*)/g).filter((p) => p.length > 0);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
    ) : (
      <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>
    )
  );
}

export function renderContent(text: string): React.ReactNode {
  const lines = text.split(/\r?\n/);
  const blocks: React.ReactNode[] = [];
  let listItems: string[] = [];
  let blockIndex = 0;

  const flushList = () => {
    if (listItems.length) {
      const key = `list-${blockIndex++}`;
      blocks.push(
        <ul className="bubble-list" key={key}>
          {listItems.map((item, i) => (
            <li key={i}>{renderInline(item, `${key}-li-${i}`)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      flushList();
      continue;
    }
    const listMatch = line.match(/^[-*]\s+(.*)/);
    if (listMatch) {
      listItems.push(listMatch[1]);
      continue;
    }
    flushList();
    const key = `p-${blockIndex++}`;
    blocks.push(<p key={key}>{renderInline(line, key)}</p>);
  }
  flushList();
  return blocks;
}
