const config = {
  rootDir: 'src',
  project: ['src/**/*.{js,jsx}!'],
  ignore: [
  ],
  ignoreBinaries: ['only-allow'],
  paths: {
    'public/*': ['public/*'],
  },
  "ignoreExportsUsedInFile": false
};

export default config;
