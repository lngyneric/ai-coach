import { shiNiangPlugin } from './ShiNiangPlugin';

// Ensure this runs only on the client
if (typeof window !== 'undefined') {
  const plugins = window.shifuPlugins || [];
  plugins.push(shiNiangPlugin);
  window.shifuPlugins = plugins;
}

export { shiNiangPlugin };
