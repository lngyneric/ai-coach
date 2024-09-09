import styles from './PrivacyPolicyPage.module.scss';
import ReactMarkdown from 'react-markdown';
import { useTranslation} from 'react-i18next';
import zhContent from './Contents/zh_Cn_PrivacyPlolicyContent.md';
import enContent from './Contents/en_PrivacyPlolicyContent.md';


const contents = {
  "zh_CN": zhContent,
  "en": enContent,
}

export const PrivacyPolicyPage = () => {

  const { i18n } = useTranslation();
  const markdown = contents[i18n.language] || contents["en"];
  return <div className={styles.PrivacyPolicyPage}>
    <ReactMarkdown
      children={markdown}
    />
  </div>
}

export default PrivacyPolicyPage;
