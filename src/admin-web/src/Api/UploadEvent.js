import store from 'store'

// console.log('uploadEvent init');
// window.collectEvent('init',
//     { app_id:20001005,
//         channel_domain: 'https://gator.volces.com', // 设置数据上送地址
//     disable_sdk_monitor:true, //用于禁止SDK启动后自身监控事件 onload 的上报
//     log :true
//   });
// window.collectEvent('start')
// if(store.get('userInfo')){
//     console.log('user',store.get('userInfo').user_id);
//     window.collectEvent('config', {
//         user_unique_id: store.get('userInfo').user_id,
//     })

// }
export const  UploadEvent = (event,data) => {
    console.log('event',event,data);
    // window.collectEvent(event,  data)
}
