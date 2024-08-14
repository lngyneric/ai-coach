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
import { memo } from 'react';
import { getUserProfile } from 'Api/user.js';
import { useEffect } from 'react';
import BirthdaySettingModal from './BirthdaySettingModal.jsx';

export const UserSettings = ({ onHomeClick, className }) => {
  const [sexSettingModalOpen, setSexSettingModalOpen] = useState(false);
  const [birthModalOpen, setBirthModalOpen] = useState(false);

  const onSaveSettingsClick = useCallback(() => {}, []);
  // 头像
  const [avatar, setAvatar] = useState(''); 
  // 昵称
  const [nickName, setNickName] = useState('');
  // 性别
  const [sex, setSex] = useState('');
  // 生日
  const [birth, setBirth] = useState('');

  const onNickNameChanged = useCallback(
    (e) => {
      setNickName(e.target.value);
    },
    [setNickName]
  );

  const onSexSettingModalOk = useCallback(
    (e) => {
      setSex(e.sex);
      setSexSettingModalOpen(false);
    },
    [setSex]
  );

  const onSexSelectClick = useCallback(() => {
    setSexSettingModalOpen(true);
  }, []);

  const onBirthClick = useCallback(() => {
    setBirthModalOpen(true);
  },[])

  const onBackgroundChange = useCallback((e) => {}, []);

  const loadData = useCallback(async () => {
    const { data: respData } = await getUserProfile();
    respData.forEach((v) => {
      const keyArr = [];
      if (v.key === 'nickname') {
        setNickName(v.value);
      } else if (v.key === 'avatar') {
        setAvatar(v.value);
      } else if (v.key === 'sex') {
        setSex('sex');
      } else if (v.key === 'birth') {
        setBirth(v.value);
      }
    });
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <>
      <div className={classNames(styles.UserSettings, className)}>
        <SettingHeader
          onHomeClick={onHomeClick}
          className={styles.settingHeader}
        />
        <div className={styles.settingBody}>
          <div className={styles.centerWrapper}>
            <ChangeAvatar img={avatar} />
            <div className={styles.basicInfoTitle}>基础信息</div>
            <SettingInputElement
              title="昵称"
              placeholder="请输入姓名"
              onChange={onNickNameChanged}
              className={styles.inputUnit}
              value={nickName}
            />
            <SettingSelectElement
              title="性别"
              placeholder="请选择性别"
              value={sex}
              className={styles.inputUnit}
              onClick={onSexSelectClick}
            />
            <SettingSelectElement
              title="生日"
              placeholder="请选择生日"
              className={styles.inputUnit}
              onClick={onBirthClick}
            />
            <SettingInputElement
              title="生日"
              placeholder="请选择生日"
              className={styles.inputUnit}
              value={birth}
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
          </div>
          <SettingRadioElement options={[{ label: 'item1', value: 1 }]} />
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
      <BirthdaySettingModal opne={birthModalOpen} />
      <SexSettingModal
        open={sexSettingModalOpen}
        onOk={onSexSettingModalOk}
        onClose={() => setSexSettingModalOpen(false)}
        initialValues={{ sex }}
      />
    </>
  );
};

export default memo(UserSettings);
