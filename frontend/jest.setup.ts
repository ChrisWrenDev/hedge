import "@testing-library/jest-dom";

// Mock ResizeObserver for recharts ResponsiveContainer
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any;
