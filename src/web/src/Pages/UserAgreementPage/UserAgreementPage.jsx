import styles from './UserAgreementPage.module.scss';
import ReactMarkdown from 'react-markdown';
import zhCNAggreement from './Contents/zh_CN_aggreement.md';
import enAggreement from './Contents/en_aggreement.md';
import { useTranslation } from 'react-i18next';

const aggreements = {
  "zh_CN": zhCNAggreement,
  "en": enAggreement,
}

export const UserAgreementPage = () => {
  const { i18n } = useTranslation();
  console.log(i18n.language)
  const markdown =  aggreements[i18n.language] || aggreements["en"];
  return <div className={styles.UserAgreementPage}>
    <ReactMarkdown
      children={markdown}
    />
  </div>
};

export default UserAgreementPage;
