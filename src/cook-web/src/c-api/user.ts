import request from '@/lib/request';
import { useSystemStore } from '@/c-store/useSystemStore';

/**
 * @description User registration endpoint
 * @param {*} username
 * @param {*} password
 * @param {*} name
 * @param {*} mobile
 * @param {*} email
 * @returns
 */
export const register = ({ username, password, mobile, email }) => {
  return request.post('/api/user/register', {
    username,
    password,
    email,
    mobile,
  });
};

/**
 * User login endpoint
 * @param {*} username
 * @param {*} password
 * @returns
 */
export const login = (username, password) => {
  return request.post('/api/user/login', { username, password });
};

/**
 * @description Fetch user information
 * @returns
 */
export const getUserInfo = () => {
  return request.get('/api/user/info');
};

/**
 *
 */
export const updateUserInfo = name => {
  return request.post('/api/user/update_info', { name });
};

export const updatePassword = (old_password, new_password) => {
  return request.post('/api/user/update_password', {
    old_password,
    new_password,
  });
};

export const requireResetPasswordCode = username => {
  return request.post('/api/user/require_reset_code', { username });
};

export const resetPassword = (username, new_password, code) => {
  return request.post('/api/user/reset_password', {
    username,
    new_password,
    code,
  });
};

/**
 * Obtain a temporary token, also required when a user logs in normally
 * @param tmp_id Client-generated id, used to exchange for a token
 * @returns
 *
 * https://agiclass.feishu.cn/docx/WyXhdgeVzoKVqDx1D4wc0eMknmg
 */
export const registerTmp = ({ temp_id }) => {
  const {
    channel: source,
    wechatCode: wxcode,
    language,
  } = useSystemStore.getState();

  return request.post('/api/user/require_tmp', {
    temp_id,
    source,
    wxcode,
    language,
  });
};

/**
 * Update WeChat code
 * @returns
 */
export const updateWxcode = ({ wxcode }) => {
  // const { wechatCode: wxcode } = useSystemStore.getState();
  return request.post('/api/user/update_openid', { wxcode });
};

/**
 * Request image captcha
 */
export const genCheckCode = mobile => {
  return request.post('/api/user/generate_chk_code', { mobile });
};

/**
 * Send SMS verification code
 * @param {string} mobile Phone number
 * @param {string} check_code Image captcha code
 */
export const sendSmsCode = ({ mobile, check_code }) => {
  return request.post('/api/user/send_sms_code', { mobile, check_code });
};

// Fetch detailed user profile
export const getUserProfile = courseId => {
  return request
    .get('/api/user/get_profile?course_id=' + courseId)
    .then(res => {
      return res.profiles || [];
    });
};

// Upload avatar
export const uploadAvatar = ({ avatar }) => {
  const formData = new FormData();
  formData.append('avatar', avatar);
  return request.post('/api/user/upload_avatar', formData);
};

// Update detailed user profile
export const updateUserProfile = (data, courseId) => {
  return request.post('/api/user/update_profile', {
    profiles: data,
    course_id: courseId,
  });
};

// submit feedback
export const submitFeedback = feedback => {
  return request.post('/api/user/submit-feedback', { feedback });
};
