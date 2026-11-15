// A handful of simple outline icons, drawn inline so no icon library is needed.
const PATHS = {
  check: 'M20 6 9 17l-5-5',
  plus: 'M12 5v14M5 12h14',
  arrow: 'M7 17 17 7M8 7h9v9',
  box: 'M21 8 12 3 3 8v8l9 5 9-5V8zM3 8l9 5 9-5M12 13v8',
  pulse: 'M3 12h4l3-8 4 16 3-8h4',
  rupee: 'M7 5h10M7 10h10M10 5c5 0 6 5 0 5l7 9',
  hourglass: 'M6 3h12M6 21h12M7 3c0 6 5 6 5 9s-5 3-5 9M17 3c0 6-5 6-5 9s5 3 5 9',
  store: 'M4 9l1-5h14l1 5M4 9v11h16V9M4 9h16M9 20v-6h6v6',
  pencil: 'M4 20h4L19 9l-4-4L4 16v4zM13 7l4 4',
  bolt: 'M13 3 4 14h7l-1 7 9-11h-7l1-7z',
};

export default function Icon({ name, size = 20 }) {
  if (name === 'star') {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={PATHS[name] ?? PATHS.bolt} />
    </svg>
  );
}
