// IE does not support the second argument of classList.toggle
const toggleClass = (
  className: string,
  flag: boolean,
  el: HTMLElement = document.body,
) => {
  el.classList[flag ? 'add' : 'remove'](className);
};

export default toggleClass;
