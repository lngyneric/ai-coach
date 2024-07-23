import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid"; // a plugin!
import timegrid from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import "./SchedulePage.css";
import { createRef } from "react";
import { useEffect } from "react";
import { useState } from "react";
import EditScheduleModal from "./Modal/EditScheduleModal";
import ScheduleDetailModal from "./Modal/ScheduleDetailModal";
import { GetAllSchedules } from "../../Api/schedule";
import { formatDate } from "../../Utils/DateUtils";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-icons/font/bootstrap-icons.css"; // needs additional webpack config!
import bootstrap5Plugin from "@fullcalendar/bootstrap5";

const SchedulePage = () => {
  const schedulePageRef = createRef();
  const [pageHeight, setPageHeight] = useState();
  const [events, setEvents] = useState([]);

  const [scheduleDetailModalProps, setScheduleDetailModalProps] = useState({
    open: false,
  });

  let [calendarDateInfo, setCalendarDateInfo] = useState({});

  /**
   * @description 查看所有的日程
   */
  const queryAllEventList = () => {
    GetAllSchedules(calendarDateInfo.startStr, calendarDateInfo.endStr).then(
      (res) => {
        setEvents(res.data);
      }
    );
  };

  const onEventClick = (ref, ifno) => {
    setScheduleDetailModalProps({
      ...scheduleDetailModalProps,
      open: true,
      scheduleId: ref.event.id,
    });
  };

  /**
   * @description fullcalendar 的回调函数用来获取时间范围
   * @param {*} dateInfo -  https://fullcalendar.io/docs/datesSet
   */
  const datesSet = (dateInfo) => {
    const startStr = formatDate(dateInfo.start);
    const endStr = formatDate(dateInfo.end);
    calendarDateInfo.startStr = startStr;
    calendarDateInfo.endStr = endStr;
    setCalendarDateInfo({
      startStr,
      endStr,
    });
    queryAllEventList();
  };

  /**
   * @description 点击关闭详情弹窗的方法
   */
  const onScheduleDetailModalCancel = () => {
    setScheduleDetailModalProps({
      ...scheduleDetailModalProps,
      open: false,
    });
  };

  /**
   * @description 点击保存的方法
   */
  const onScheduleDetailModalCompleted = () => {
    setScheduleDetailModalProps({
      ...scheduleDetailModalProps,
      open: false,
    });
    queryAllEventList();
  };

  /**
   * @description 设置周末的单元格的类名
   * @param {*} arg
   * @returns
   */
  const setWeekendClassName = (arg) => {
    if (arg.date.getDay() === 0) {
      return "fullcalendar_day-header-sunday";
    } else if (arg.date.getDay() === 6)
      return "fullcalendar_day-header-saturday";
  };

  /**
   *
   * @description 给日历中今天所在的单元格设置一个类名
   * @param {*} arg
   * @param {*} createElement
   * @return {*}
   */
  const setTodayClassName = (arg, createElement) => {
    if (arg.isToday) {
      return "fullcalendar_cell-today";
    }
    return "";
  };

  const setHeaderClassName = (arg) => {
    const headerCellClassNameViewTypeMapping = {
      dayGridMonth: "fullcalendar_day-header__align-right",
      timeGridWeek: "fullcalendar_day-header__align-center",
      timeGridDay: "fullcalendar_day-header__align-left",
    };

    if (arg.isToday === true) {
      headerCellClassNameViewTypeMapping.timeGridWeek =
        headerCellClassNameViewTypeMapping.timeGridWeek +
        " fullcalendar_day-header__today";
    }
    return headerCellClassNameViewTypeMapping[arg.view.type];
  };

  const setTodayCellContent = (arg) => {
    if (arg.view.type === "dayGridMonth") {
      return (
        <div className="date-Number_container">
          <div className="date-number">{arg.date.getDate()}</div>
          <div>日</div>
        </div>
      );
    }
  };

  useEffect(() => {
    const getPageHeight = () => {
      const pageEl = schedulePageRef.current;
      if (pageEl === null) return false;
      const computedStyle = document.defaultView.getComputedStyle(pageEl);
      const { paddingTop, paddingBottom } = computedStyle;

      setPageHeight(
        pageEl.clientHeight -
          paddingTop.replace("px", "") -
          paddingBottom.replace("px", "")
      );
    };
    getPageHeight();
    window.addEventListener("resize", () => {
      getPageHeight();
    });
  }, [pageHeight, schedulePageRef]);

  return (
    <div className="schedule_page" ref={schedulePageRef}>
      <FullCalendar
        height={pageHeight + "px"}
        locale="zh-cn"
        plugins={[dayGridPlugin, timegrid, interactionPlugin, bootstrap5Plugin]}
        initialView="dayGridMonth"
        selectable={true}
        eventClick={onEventClick}
        headerToolbar={{
          left: "title,today,prev,next",
          right: "dayGridMonth,timeGridWeek,timeGridDay",
        }}
        events={events}
        datesSet={datesSet}
        buttonText={{
          today: "今天",
          month: "月视图",
          week: "周视图",
          day: "日视图",
          list: "日程",
        }}
        customButtons={{}}
        allDayText="全天"
        dayHeaderClassNames={(arg) => {
          return [
            setWeekendClassName(arg),
            "fullcalendar_day-cell",
            setHeaderClassName(arg),
          ];
        }}
        dayCellClassNames={(arg) => {
          return [
            setWeekendClassName(arg),
            setTodayClassName(arg),
            "fullcalendar_day-cell",
          ];
        }}
        dayCellContent={setTodayCellContent}
        themeSystem="bootstrap5"
      />
      <ScheduleDetailModal
        open={scheduleDetailModalProps.open}
        onCancel={onScheduleDetailModalCancel}
        scheduleId={scheduleDetailModalProps.scheduleId}
        onCompleted={onScheduleDetailModalCompleted}
      ></ScheduleDetailModal>
    </div>
  );
};

export default SchedulePage;
