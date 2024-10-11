import { memo, useEffect, useState } from 'react';
import { parseUrlParams } from 'Utils/urlUtils.js';
import routes from './Router/index';
import { useRoutes } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import locale from 'antd/locale/zh_CN';
import { useSystemStore } from 'stores/useSystemStore.js';
import i18n from './i18n.js';
import { inWechat, wechatLogin } from 'constants/uiConstants.js';
import { getBoolEnv } from 'Utils/envUtils.js';
import { userInfoStore } from 'Service/storeUtil.js';
if (getBoolEnv('REACT_APP_ERUDA')) {
  import('eruda').then(eruda => eruda.default.init());
}

const RouterView = () => useRoutes(routes);

const App = () => {
  const { updateChannel, channel, wechatCode, updateWechatCode, updateCourseId } =
    useSystemStore();


  var initLang = useSystemStore().language;

  if (userInfoStore.get()) {

    initLang = userInfoStore.get().language;
  }


  console.log('initLang', initLang);
  const [language, setLanguage] = useState(initLang);
  const [loading, setLoading] = useState(true);
  const params = parseUrlParams();
  console.log('params', params);
  const currChannel = params.channel || '';

  if (channel !== currChannel) {
    updateChannel(currChannel);
  }



  useEffect(() => {
    if (inWechat()) {
      setLoading(true);
      const currCode = params.code;
      if (!currCode) {
        wechatLogin({
          appId: process.env.REACT_APP_APP_ID,
        });
        return
      }
      if (currCode !== wechatCode) {
        updateWechatCode(currCode);
      }
    }
    setLoading(false);
  }, [params.code, updateWechatCode, wechatCode])

  useEffect(() => {
    if (params.courseId) {
      updateCourseId(params.courseId);
    }
  }, [params.courseId, updateCourseId]);

  console.log('courseId', useSystemStore.getState().courseId);
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
