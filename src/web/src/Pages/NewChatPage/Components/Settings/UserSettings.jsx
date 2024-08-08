/**
 * 用户配置界面
 */
import styles from './UserSettings.module.scss';
import MainButton from 'Components/MainButton.jsx';
import SettingHeader from './SettingHeader.jsx';
import classNames from 'classnames';
import ChangeAvatar from './ChangeAvatar.jsx';
import IndustrySettingModal from './IndustrySettingModal.jsx';
import JobSettingModal from './JobSettingModal.jsx';
import SexSettingModal from './SexSettingModal.jsx';
import { useState } from 'react';
import { useCallback } from 'react';
import { SettingRadioElement } from './SettingRadioElement.jsx';
import { SettingInputElement } from './SettingInputElement.jsx';
import { SEX_NAMES } from 'constants/userConstants.js';
import SettingSelectElement from './SettingSelectElement.jsx';

export const UserSettings = ({ onHomeClick, className }) => {
  const [industrySettingModalOpen, setIndustrySettingModalOpen] =
    useState(false);
  const [jobSettingModalOpen, setJobSettingModalOpen] = useState(false);
  const [sexSettingModalOpen, setSexSettingModalOpen] = useState(false);
  const onSaveSettingsClick = useCallback(() => {}, []);

  const [nickName, setNickName] = useState('');
  const onNickNameChanged = useCallback(
    (e) => {
      setNickName(e.target.value);
    },
    [setNickName]
  );

  const [sex, setSex] = useState('');
  const onSexSettingModalOk = useCallback(
    (e) => {
      setSex(e.sex);
      setSexSettingModalOpen(false);
    },
    [setSex]
  );

  const onSexSelectClick = useCallback(() => {
    setSexSettingModalOpen(true);
  }, [])

  const [industry, setIndustry] = useState('');
  const onIndustryChanged = useCallback(
    (e) => {
      setIndustry(e.target.value);
    },
    [setIndustry]
  );

  const [job, setJob] = useState('');
  const onJobChanged = useCallback(
    (e) => {
      setJob(e.target.value);
    },
    [setJob]
  );

  return (
    <>
      <IndustrySettingModal
        open={industrySettingModalOpen}
        onClose={() => setIndustrySettingModalOpen(false)}
      />
      <SexSettingModal
        open={sexSettingModalOpen}
        onOk={onSexSettingModalOk}
        onClose={() => setSexSettingModalOpen(false)}
        initialValues={{ sex }}
      />
      <JobSettingModal
        open={jobSettingModalOpen}
        onClose={() => setJobSettingModalOpen(false)}
      />
      <div className={classNames(styles.UserSettings, className)}>
        <SettingHeader
          onHomeClick={onHomeClick}
          className={styles.settingHeader}
        />
        <div className={styles.settingBody}>
          <div className={styles.centerWrapper}>
            <ChangeAvatar img={''} />
            <div className={styles.basicInfoTitle}>基础信息</div>
            <SettingInputElement
              title="昵称"
              placeholder="请输入姓名"
              onChange={onNickNameChanged}
            />
            <SettingSelectElement
              title="性别"
              placeholder="请选择性别"
              value={sex ? SEX_NAMES[sex] : SEX_NAMES.secret}
              className={styles.inputUnit}
              onClick={onSexSelectClick}
            />
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择生日"
                readOnly={true}
              />
              <img
                className={styles.icon}
                src={require('@Assets/newchat/light/icon16-arrow-down.png')}
                alt="icon"
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择行业"
                value={industry}
                onChange={onIndustryChanged}
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择职业"
                value={job}
                onChange={onJobChanged}
              />
            </div>
          </div>
          <SettingInputElement />
          <SettingRadioElement />
        </div>
        <div className={styles.settingFooter}>
          <div className={styles.centerWrapper}>
            <MainButton
              className={styles.saveBtn}
              onClick={onSaveSettingsClick}
            >
              保存
            </MainButton>
          </div>
        </div>
      </div>
    </>
  );
};

export default UserSettings;
