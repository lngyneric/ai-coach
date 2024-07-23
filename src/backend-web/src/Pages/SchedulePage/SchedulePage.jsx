import {Badge, Calendar,Spin } from "antd";
import './SchedulePage.css';
import 'dayjs/locale/zh-cn';
import locale from 'antd/es/date-picker/locale/zh_CN';
import { GetAllSchedules } from "../../Api/schedule";
import { useEffect, useState } from "react";
import { UploadEvent } from "../../Api/UploadEvent";


const  isSameDay = (dateStr1, dateStr2)=> {
  var date1 = new Date(dateStr1);
  var date2 = new Date(dateStr2);

  return date1.getFullYear() === date2.getFullYear() &&
         date1.getMonth() === date2.getMonth() &&
         date1.getDate() === date2.getDate();
}

const getListData = (value,schedules) => {
    let listData=[];
    for (let i = 0; i < schedules.length; i++) {
      if (isSameDay(schedules[i].datetime , value.format('YYYY-MM-DD'))) {
        var date = new Date(schedules[i].datetime);
        var hours = date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
        var minutes = date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();
        var timeStr = hours + ":" + minutes;

        var end_time = new Date(schedules[i].end_time);
        var end_hours = end_time.getHours() < 10 ? "0" + end_time.getHours() : end_time.getHours();
        var end_minutes = end_time.getMinutes() < 10 ? "0" + end_time.getMinutes() : end_time.getMinutes();
        var end_timeStr = end_hours + ":" + end_minutes;
        timeStr = timeStr + " - " + end_timeStr;
        console.log(schedules[i]);
        listData.push({ 
          id:schedules[i].schedule_id, 
          content: <>{timeStr} {schedules[i].description}</>,
          type: 'success' });
        // break;
      }
    }
    return listData || [];
  };


  const getMonthData = (value) => {
    if (value.month() === 8) {
      return 1394;
    }
  };

const SchedeleComponent = () => {
  UploadEvent(
    'schedule',{
      "page":"schedule",
    })

  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  
    const monthCellRender = (value) => {
        const num = getMonthData(value,schedules);
        return num ? (
          <div className="notes-month">
            <section>{num}</section>
            <span>Backlog number</span>
          </div>
        ) : null;
      };


      const dateCellRender = (value) => {
        const listData = getListData(value,schedules);
        return (
          <ul className="events">
            {listData.map((item) => (
              <li key={item.id}>
                <Badge 
                  status={item.type} 
                  text={item.content} />
              </li>
            ))}
          </ul>
        );
      };

      const cellRender = (current, info) => {
        if (info.type === 'date') return dateCellRender(current);
        if (info.type === 'month') return monthCellRender(current);
        return info.originNode;
      };

      
    useEffect(() => {
        setLoading();
        GetAllSchedules().then((res) => {
          setSchedules(res.data);
          setLoading(false);
        });
    }, []);
    return (
        <div>
          <Spin
            spinning={loading}>
          <Calendar 
              locale={locale}
              cellRender={cellRender} />
          </Spin>
        </div>
    );
};

export default SchedeleComponent;
