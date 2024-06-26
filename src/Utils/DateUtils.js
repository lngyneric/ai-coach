export const formatDate = (date) => {
    return date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + date.getDate();
}

// 判断是否是闰年
export const isLeapYear = (year) => {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}
