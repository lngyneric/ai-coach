const mdTxt = `# 参考
[如何让eslint、ts识别配置的路径别名，并且不报错？ - 掘金 (juejin.cn)](https://juejin.cn/post/7021084391065518087)
[eslint-import-resolver-alias - npm (npmjs.com)](https://www.npmjs.com/package/eslint-import-resolver-alias)

# 安装 Eslint 插件 dsafsafkdalsfjlkdsa;fjk;lsajd;fkljds;lfjdskl;ajf;lkdsja;flkjdsa;lkfj;dklsajf;ljs;flkjs;lakjf;lsakjfl;ksjaf;lkjsadflkja;sldkjf;ladskjf;lkjdsaf;ljkds;aljkfds;lajkfl;ddsafdsafdsafasdfsdfdsa;lfkjasd;lkjf;dlsakjkf;ldsaj;lfkjds;lkafj;lsadkjf;lsdkajf;lkjsad;lfkdjsakl;fja;sdlkjf;laksdjf;ljasd;lkfjsad;lkjf;lkasdjfl;kjdsa;ljf;ladsjf;ldjsal;fkjads;ljf;alsdkjf;lkasdjf;ldksajf;ljdksa;fljkdas;lfjk;lsadkjf;laksdjf;lksadjf;lkjsadlk;fjsad;lkfjas;dlkfj;lsadkfj;dlsakjfl;kasjas

![example image](https://ts1.cn.mm.bing.net/th/id/R-C.f4dd383a91aa149fd47da7a0cba73a95?rik=KRZB3DYDNVGq9w&riu=http%3a%2f%2fpic.zsucai.com%2ffiles%2f2013%2f0716%2fpgjlg7.jpg&ehk=yGkBxqtnGW%2bsIAxJA0yro%2bOLIk0fJU5jR1SsfId3PL0%3d&risl=&pid=ImgRaw&r=0)

\`\`\`zsh
npm install eslint-plugin-import eslint-import-resolver-alias --save-dev
\`\`\`
# 配置 Eslint 

\`\`\`javascript
// .eslintrc.js

module.exports = {

  settings: {

    'import/resolver': {

      alias: {

        map: [

          ['babel-polyfill', 'babel-polyfill/dist/polyfill.min.js'],

          ['helper', './utils/helper'],

          ['material-ui/DatePicker', '../custom/DatePicker'],

          ['material-ui', 'material-ui-ie10']

        ],

        extensions: ['.ts', '.js', '.jsx', '.json']

      }

    }

  }

};
\`\`\`
`;
export default mdTxt;
