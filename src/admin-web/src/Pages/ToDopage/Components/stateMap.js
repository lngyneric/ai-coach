const stateMap = {
  toDo: {
    label: "待办",
    color: "#FDB813",
    backgroundColor: "#FDB81322",
    code: 0,
  },
  //   inProgress: {
  //     label: "进行中",
  //     color: "#3498DB",
  //     backgroundColor: "#3498DB2",
  //   },
  completed: {
    label: "完成",
    color: "#27AE60",
    backgroundColor: "#27AE602",
    code: 1,
  },
  //   delayed: { label: "延迟", color: "#E74C3C", backgroundColor: "#E74C3C2" },
  //   cancelled: { label: "取消", color: "#A9A9A9", backgroundColor: "#A9A9A92" },
  //   paused: { label: "暂停", color: "#9B59B6", backgroundColor: "#9B59B62" },
  //   undefined: { label: "--", color: "#9B59B6", backgroundColor: "#9B59B62" },
};

const stateList = (() => {
  return Object.keys(stateMap).map((key) => {
    return { value: stateMap[key].code, ...stateMap[key] };
  });
})();

export { stateMap, stateList };
