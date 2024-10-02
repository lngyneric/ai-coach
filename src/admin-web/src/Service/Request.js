import { SSE } from "sse.js";
import axios from "axios";
import Cookies from "js-cookie";
import { message } from "antd";
import store from "store";
/**
 *
 * @param {*} token
 * @param {*} chatId
 * @param {*} text
 * @param {*} onMessage
 * @returns
 */
export const SendMsg = (token,chatId, text, onMessage) => {
  Cookies.set("token", token);
  var source = new SSE(process.env.REACT_APP_BASEURL+"/chat/chat-assistant?token="+token, {
    headers: { "Content-Type": "application/json" ,"Cookie":"token="+token},
    payload: JSON.stringify({
      token: token,
      msg: text,
      chat_id: chatId,
    }),

  });
  source.onmessage = (event) => {
    try {

      var response =JSON.parse (event.data)
      console.log("response", response,new Date());
      if (onMessage) {
        onMessage(response);
      }
    } catch (e) {
      console.log("error", e);
    }
  };
  source.onerror = (event) => {
    console.log("连接错误");
    console.log(event);
    // this.searchBoll = true;
  };
  source.onclose = (event) => {
    console.log("会话完成断开连接");
    // this.searchBoll = true;
    console.log(event);
  };
  source.stream();
  return source;
}


console.log(process.env.REACT_APP_BASEURL);

/**
 * @description 创建 axios 实例
 * @type {*}
 * */
const axiosrequest = axios.create({
  baseURL:process.env.REACT_APP_BASEURL,
  withCredentials: true, // 跨域请求时发送 cookies
  headers:{"Content-Type":"application/json"}
});

const downloadFileRequest = axios.create({
  baseURL:process.env.REACT_APP_BASEURL,
  withCredentials: true,
  responseType: 'blob',
  headers:{"Content-Type":"application/json"}
});
// 创建请求拦截器
axiosrequest.interceptors.request.use(async(config)=>{
  config.headers.token = store.get("token");
  return config;
})

// 创建响应拦截器
axiosrequest.interceptors.response.use(
  response => {
    console.log('url',response.config.url)
    console.log('response',response)
    // download file if response is blob
    console.log(response.headers)
    // check the header Content-Disposition
    if(response.headers['content-disposition']){
      console.log(response.data.length)
      const blob = new Blob([response.data], { type: response.headers['content-type'] });

      // get filename from header
      let filename = 'downloadfile';
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          filename = decodeURIComponent(matches[1].replace(/['"]/g, ''));
        }
      }

      //  create download href
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // clear
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      return;
    }
    if(response.data.code !== 0){
      message.error({content:response.data.message});
      const apiError = new CustomEvent("apiError", {detail:response.data, bubbles:true,});
      document.dispatchEvent(apiError);
      return Promise.reject(response.data);
    }
    return response.data;
  },error => {
    const apiError = new CustomEvent("apiError", {detail:error});
    document.dispatchEvent(apiError);
    message.error("api error");
    return Promise.reject(error);
  })





export default axiosrequest;
export {downloadFileRequest};
