import {
  getMockRunFixtureMode,
  shouldUseMockStuckRunFixture,
} from './mockRunStreamFixture';

const setPageSearch = (search: string) => {
  // jsdom 20 不会在 history.pushState 时同步 window.location，直接替换 location 以
  // 让被测代码读到预期的 query string。
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: new URL(`http://localhost:3000/${search}`),
  });
};

describe('mock run stream fixture mode', () => {
  afterEach(() => {
    setPageSearch('');
  });

  it('enables the full test fixture for normal run requests', () => {
    setPageSearch('?mock_run_sse_fixture=test');

    expect(getMockRunFixtureMode({ input_type: 'normal' })).toBe('test');
  });

  it('keeps the stuck fixture mode for the existing debug flag', () => {
    setPageSearch('?mock_run_sse_fixture=stuck');

    expect(getMockRunFixtureMode({ input_type: 'normal' })).toBe('stuck');
    expect(shouldUseMockStuckRunFixture({ input_type: 'normal' })).toBe(true);
  });

  it('ignores fixture flags for non-normal requests', () => {
    setPageSearch('?mock_run_sse_fixture=test');

    expect(getMockRunFixtureMode({ input_type: 'ask' })).toBeNull();
  });
});
