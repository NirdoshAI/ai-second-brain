import "./components.css";

/**
 * Displays a source attribution badge.
 *
 * @param {{ source: { source_file: string, page_numbers: number[] } }} props
 */
export default function SourceBadge({ source }) {
  const { source_file, page_numbers } = source;

  let pageLabel = "";
  if (page_numbers && page_numbers.length > 0) {
    const first = page_numbers[0];
    const last = page_numbers[page_numbers.length - 1];
    pageLabel = first === last ? ` · p. ${first}` : ` · p. ${first}–${last}`;
  }

  return (
    <span className="source-badge" title={`${source_file}${pageLabel}`}>
      {source_file}
      {pageLabel}
    </span>
  );
}
