import styles from './MainButton.module.scss';
import { forwardRef, memo, ReactNode } from 'react';

import clsx from 'clsx';
import { Button, ButtonProps } from '@/components/ui/Button';

interface MainButtonProps extends ButtonProps {
  height?: number;
  shape?: 'round' | 'square';
  width?: number | string;
  children?: ReactNode;
}

export const MainButton = forwardRef<HTMLButtonElement, MainButtonProps>(
  (props, ref) => {
    const {
      height = 40,
      shape = 'round',
      width,
      className,
      style,
      children,
      ...rest
    } = props;

    // Map the shape value to its corresponding className
    const shapeClass = shape === 'square' ? 'rounded-md' : 'rounded-full';

    return (
      <Button
        ref={ref}
        {...rest}
        className={clsx(styles.mainButton, shapeClass, className)}
        style={{ width, height, ...style }}
      >
        {children}
      </Button>
    );
  },
);

MainButton.displayName = 'MainButton';

export default memo(MainButton);
