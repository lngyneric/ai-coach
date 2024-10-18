import styles from './UserAgreementPage.module.scss';
import ReactMarkdown from 'react-markdown';
import zhCNAggreement from './Contents/zh_CN_aggreement.md';
import enAggreement from './Contents/en_aggreement.md';
import { useSystemStore } from 'stores/useSystemStore.js';
import { useEffect } from 'react';
import { userInfoStore } from 'Service/storeUtil.js';
const aggreements = {
  "zh-CN": zhCNAggreement,
  "en-US": enAggreement,
}

export const UserAgreementPage = () => {



  const { language, updateLanguage } = useSystemStore();
  useEffect(() => {
    const userInfo = userInfoStore.get();
    if (userInfo) {
      updateLanguage(userInfo.language);
    }
  }, [updateLanguage]);
  const markdown =  aggreements[language];
  return <div className={styles.UserAgreementPage}>
    <ReactMarkdown
      children={markdown}
    />
  </div>
};

export default UserAgreementPage;
