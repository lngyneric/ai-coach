import { memo, useEffect, useState } from 'react';
import { parseUrlParams } from 'Utils/urlUtils.js';
import routes from './Router/index';
import { useRoutes } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import locale from 'antd/locale/zh_CN';
import { useSystemStore } from 'stores/useSystemStore.js';
import i18n from './i18n.js';
import { inWechat, wechatLogin } from 'constants/uiConstants.js';

const RouterView = () => useRoutes(routes);

const App = () => {
  const { language, updateChannel, channel, wechatCode, updateWechatCode } =
    useSystemStore();
  const [loading, setLoading] = useState(true);

  const params = parseUrlParams();
  console.log('params', params);
  const currChannel = params.channel || '';

  if (channel !== currChannel) {
    updateChannel(currChannel);
  }

  if (inWechat()) {
    console.log('inWechat...');
    const currCode = params.code;

    let isExit = false;
    if (!currCode) {
      wechatLogin({
        appId: process.env.REACT_APP_APP_ID,
      });
      isExit = true;
    }
    if (currCode !== wechatCode) {
      updateWechatCode(currCode);
    }

    if (!isExit) {
      setLoading(false);
    }
  } else {
    setLoading(false);
  }

  // 挂载 debugger
  useEffect(() => {
    window.ztDebug = {};

    return () => {
      delete window.ztDebug;
    };
  });

  useEffect(() => {
    i18n.changeLanguage(language);
  }, [language]);

  return (
    <ConfigProvider locale={locale}>
      {!loading && <RouterView></RouterView>}
    </ConfigProvider>
  );
};

export default memo(App);
