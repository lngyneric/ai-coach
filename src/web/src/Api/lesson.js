import request from "../Service/Request";

export const getLessonTree = async () => {
  return request({
    url: `/api/study/get_lesson_tree?course_id=${process.env.REACT_APP_COURSE_ID}`,
    method: "get",
  });
}

export const getScriptInfo = async (scriptId) => {
  return request({
    url: `/api/study/query-script-into?script_id=${scriptId}`,
    method: 'GET',
    
  })
};
