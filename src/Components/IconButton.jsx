import { useState, useRef } from 'react';
import styles from './IconButton.module.scss';
import { useEffect } from 'react';

export const IconButton = ({
  icon = '',
  hoverIcon = '',
  activeIcon = '',
  selectedIcon = '',
  width = 36,
  selected = false
}) => {
  const [bgImage, setBgImage] = useState(selected ? selectedIcon : icon);
  const [isHover, setIsHover] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const topRef = useRef();

  useEffect(() => {

  }, selected);

  useEffect(() => {
    const onMouseEnter = () => {
      setIsHover(true);
    }

    const onMouseLeave = () => {
      setIsHover(false);
    }

    const onMouseDown = () => {
      setIsActive(true);
    }

    const onMouseUp = () => {
      setIsActive(false);
    }
    
    const elem = topRef.current;
    if (elem) {
      elem.addEventListener('mouseenter', onMouseEnter);
      elem.addEventListener('mouseleave', onMouseLeave);
      elem.addEventListener('mousedown', onMouseDown);
      elem.addEventListener('mouseup', onMouseUp);
    }


    return () => {
      elem.removeEventListener('mouseenter', onMouseEnter);
      elem.removeEventListener('mouseleave', onMouseLeave);
      elem.removeEventListener('mousedown', onMouseDown);
      elem.removeEventListener('mouseup', onMouseUp);
    }

  }, []);

  return <div ref={topRef} className={styles.IconButton} style={{width: width}}>
    <img src={bgImage} alt="" className={styles.innerIcon} />
  </div>
}
