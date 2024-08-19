import { memo } from 'react';
import LogoWithText from 'Components/logo/LogoWithText.jsx';
import styles from './PayLeft.module.scss';

export const PayLeft = () => {
  return (
    <div className={styles.payLeft}>
      <div className={styles.logoWrapper}>
        <LogoWithText direction="row" color="white" size={40} />
      </div>
      <div className={styles.description}>
        专家把关课程体系，AI 授课个性学习，真人助教答疑兜底
      </div>
      <div className={styles.infoTitle}>跟 AI 学 Python</div>
      <div className={styles.infoLines}>
        <div className={styles.infoLine}>1. <b>零基础</b>掌握 GitHub Copilot / 通义灵码编写 Python 程序</div>
        <div className={styles.infoLine}>2. <b>AI 一对一个性化</b>教学，贴合你的背景和偏好</div>
        <div className={styles.infoLine}>3. N 个实战任务训练，<b>真人助教</b>陪伴指导</div>
        <div className={styles.infoLine}>4. <b>AI 答疑</b>即将上线，不懂就问，I 人福音</div>
        <div className={styles.infoLine}>5. 录播课的价格，<b>一对一的享受</b></div>
        <div className={styles.infoLine}>6. <b>限时早鸟价</b>，一个月后恢复原价 299</div>
      </div>
    </div>
  );
};

export default memo(PayLeft);
