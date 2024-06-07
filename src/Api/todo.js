import request from "../Service/Request";

export const GetAllTodos = async (title, is_done, start_date, end_date) => {
  return request({
    url: "/api/todo/all",
    method: "get",
    params: { title, is_done, start_date, end_date },
  });
};

export const MarkTodo = async (id) => {
  return request({
    url: "/api/todo/done",
    method: "post",
    data: { todo_id: id },
  });
};

export const updateTodo = async (todoInfo) => {
  return request({
    url: "/api/todo/update",
    method: "post",
    data: todoInfo,
  });
};

export const deleteTodo = async (todo_id) => {
  return request({
    url: "/api/todo/delete",
    method: "post",
    data: { todo_id },
  });
};
