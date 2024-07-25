import request from "../Service/Request";

export const GetAllContacts = async (name, mobile, email) => {
  return request({
    url: "/api/contact/all",
    method: "get",
    params: { name, mobile, email },
  });
};

export const updateContact = async (contactInfo) => {
  return request({
    url: "/api/contact/update",
    method: "post",
    data: contactInfo,
  });
};

/**
 * @description 删除联系人的方法
 * @param {String[]} contactIds - 联系人 id
 * @returns
 */
export const deleteContact = async (contactIds) => {
  return request({
    url: "/api/contact/delete",
    method: "post",
    data: { contactIds: contactIds.join(",") },
  });
};
