import { useRef } from 'react';
import styles from './BirthdaySettingModal.module.scss';
import SettingBaseModal from './SettingBaseModal.jsx';
import { debounce } from 'throttle-debounce';
import { useEffect } from 'react';

export const BirthdaySettingModal = ({
  open,
  onClose,
  onOk = ({ birthday }) => {},
  initialValues = {},
}) => {
  const itemHeight = 30;
  const scrollerRef = useRef(null);
  const series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  const scrollGroupWrapper = useRef(null);

  const gp1 = useRef(null);
  const gp2 = useRef(null);
  const gp3 = useRef(null);
  const sTop = useRef(0);

  const onOkClick = ({ birthday }) => {
  }

  const onWrapperScroll = (e) => {
  }

  const onScrollInnerScrollInner = debounce(100, (e) => {
    console.log('onScrollInnerScrollInner', e.target.scrollTop);
    const { scrollTop } = e.target;

    const offset = scrollTop % itemHeight;
    if (offset !== 0) {
      if (offset < itemHeight / 2) {
        scrollerRef.current.scrollTo({top: scrollTop - offset,  behavior: 'smooth'});
      } else {
        scrollerRef.current.scrollTo({top: scrollTop + offset,  behavior: 'smooth'});
      }
    } else {
        scrollerRef.current.scrollTo({top: scrollTop,  behavior: 'smooth'});
    }
  });

  const onScrollInnerScroll = (e) => {
    const { scrollTop } = e.target;

    if (scrollTop < itemHeight * series.length) {
      scrollGroupWrapper.current.insertBefore(gp3.current, gp1.current);
      const tmp = gp3.current;
      gp3.current = gp2.current;
      gp2.current = gp1.current;
      gp1.current = tmp;
    } else if (scrollTop > itemHeight * series.length * 2) {
      scrollGroupWrapper.current.appendChild(gp1.current);
      const tmp = gp1.current;
      gp1.current = gp2.current;
      gp2.current = gp3.current;
      gp3.current = tmp;
    }


    onScrollInnerScrollInner(e);
  }

  useEffect(() => {
    if (!scrollGroupWrapper.current || scrollGroupWrapper.current.children.length > 0) {
      return
    }
    const createElems = (debugText) => {
      const wrap = document.createElement('div');
      wrap.className = styles.scrollGroup;

      series.forEach(v => {
        const ele = document.createElement('div');
        ele.innerText = `${debugText}${v}`;
        ele.style.height = `${itemHeight}px`;
        ele.className = styles.scrollItem;
        wrap.appendChild(ele);
      })

      return wrap;
    }

    gp1.current = createElems('v1-');
    gp2.current = createElems('v2-');
    gp3.current = createElems('v3-');

    if (!scrollGroupWrapper.current && scrollGroupWrapper) {
      return;
    }
    scrollGroupWrapper.current.appendChild(gp1.current);
    scrollGroupWrapper.current.appendChild(gp2.current);
    scrollGroupWrapper.current.appendChild(gp3.current);
    sTop.current = itemHeight * series.length;
    scrollerRef.current.scrollTo(0, sTop.current);

    const wrapper = scrollGroupWrapper.current;

    return () => {
      wrapper.innerHtml = '';
    }
  });

  const onMouseWheel = (e) => {
    let newScrollTop = 0;
    const scrollTop = sTop.current;

    console.log('newScrollTop 1', newScrollTop);

    if (e.deltaY > 0) {
      newScrollTop = scrollTop + itemHeight;
    } else if (e.deltaY < 0) {
      newScrollTop = scrollTop - itemHeight;
    }

    console.log('newScrollTop 2', newScrollTop);

    let rerange = false;
    if (newScrollTop < itemHeight * series.length) {
      scrollGroupWrapper.current.insertBefore(gp3.current, gp1.current);
      const tmp = gp3.current;
      gp3.current = gp2.current;
      gp2.current = gp1.current;
      gp1.current = tmp;
      newScrollTop = newScrollTop + itemHeight * series.length;

      console.log('newScrollTop 3 - 1', newScrollTop);
      rerange = true;
    } else if (newScrollTop > itemHeight * series.length * 2) {
      scrollGroupWrapper.current.appendChild(gp1.current);
      const tmp = gp1.current;
      gp1.current = gp2.current;
      gp2.current = gp3.current;
      gp3.current = tmp;
      newScrollTop = newScrollTop - itemHeight * series.length;
      console.log('newScrollTop 3 - 2', newScrollTop);
      rerange = true;
    }

    console.log('newScrollTop 4', newScrollTop);
    sTop.current = newScrollTop;
    if (!rerange) {
      scrollerRef.current.scrollTo({top: newScrollTop, behavior: 'smooth'});
    } else {
      scrollerRef.current.scrollTo({top: newScrollTop});
    }
  }

  const onTouchStart = (e) => {
  }

  const onTouchMove = (e) => {
  }

  const onTouchEnd = (e) => {
  }

  return <SettingBaseModal
    className={styles.SexSettingModal}
    open={open}
    onClose={onClose}
    onOk={onOkClick}
  >
    <div className={styles.birthdayWrapper}>
      <div className={styles.scrollWrapper} style={{ height: '180px' }}>
        <div ref={scrollerRef} className={styles.scrollInner} onWheel={onMouseWheel} onTouchStart={onTouchStart} onTouchEnd={onTouchEnd} onTouchMove={onTouchMove} >
          <div style={{ height: '75px' }}></div>
          <div ref={scrollGroupWrapper}></div>
          <div style={{ height: '75px' }}></div>
        </div>
        <div className={styles.selector}></div>
      </div>
    </div>
  </SettingBaseModal> 
}

export default BirthdaySettingModal;
