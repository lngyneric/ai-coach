import { memo } from 'react';
import logoBlue from 'Assets/logos/logo-blue-120.png';
import logoColor from 'Assets/logos/logo-color-120.png';
import logoTextRow from 'Assets/logos/logo-text-horiz-160.png';
import logoTextColumn from 'Assets/logos/logo-text-verti-160.png';

/**
 *
 * @param {direction} 'row' | 'col'
 * @param {size} number
 * @param { color } 'blue' | 'color' | 'white'
 * @returns
 */
export const LogoWithText = ({ direction, size = 64, color = 'blue' }) => {
  const isRow = direction === 'row';
  const flexFlow = isRow ? 'row nowrap' : 'column nowrap';

  const commonStyles = {
    width: isRow ? 'auto' : size + 'px',
    height: isRow ? size + 'px' : 'auto',
  };

  const textStyles = {
    width: isRow ? 'auto' : size * 0.8 + 'px',
    height: isRow ? size * 0.8 + 'px' : 'auto',
    marginLeft: isRow ? size * 0.3 + 'px' : '0',
    marginTop: isRow ? '0' : size * 0.3 + 'px',
  };

  return (
    <div
      style={{
        display: 'flex',
        flexFlow: flexFlow,
        alignItems: 'center',
        ...commonStyles,
      }}
    >
      {color === 'color' ? (
        <img src={logoColor} alt="logo" style={{ ...commonStyles }} />
      ) : (
        <img src={logoBlue} alt="logo" style={{ ...commonStyles }} />
      )}

      {isRow ? (
        <img src={logoTextRow} alt="logotext" style={{ ...textStyles }} />
      ) : (
        <img src={logoTextColumn} alt="logotext" style={{ ...textStyles }} />
      )}
    </div>
  );
};

export default memo(LogoWithText);
