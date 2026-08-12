import { memo, useMemo } from 'react';

import { useEnvStore } from '@/c-store/envStore';

import imgLogoRow from '@/c-assets/logos/ai-shifu-logo-horizontal.png';
import imgLogoColumn from '@/c-assets/logos/ai-shifu-logo-vertical.png';

/**
 *
 * @param {direction} 'row' | 'col'
 * @param {size} number
 * @returns
 */
export const LogoWithText = ({ direction, size = 64 }) => {
  const isRow = direction === 'row';
  const flexFlow = isRow ? 'row nowrap' : 'column nowrap';
  const logoHorizontal = useEnvStore(state => state.logoHorizontal);
  const logoVertical = useEnvStore(state => state.logoVertical);
  const logoWideUrl = useEnvStore(state => state.logoWideUrl);
  const logoSquareUrl = useEnvStore(state => state.logoSquareUrl);
  const homeUrl = useEnvStore(state => state.homeUrl);
  const wideLogoSrc: string = useMemo(() => {
    return logoWideUrl || logoHorizontal || '/logo.png';
  }, [logoHorizontal, logoWideUrl]);

  const squareLogoSrc: string = useMemo(() => {
    return logoSquareUrl || logoVertical || '/logo.png';
  }, [logoSquareUrl, logoVertical]);

  const wideWidth = useMemo(() => {
    const wls = wideLogoSrc as any;
    if (typeof wls === 'object' && wls && 'width' in wls && wls.width && wls.height) {
      return Math.round((size * wls.width) / wls.height);
    }
    return Math.round(size * (imgLogoRow.width / imgLogoRow.height));
  }, [size, wideLogoSrc]);

  return (
    <div
      style={{
        display: 'flex',
        flexFlow: flexFlow,
        alignItems: 'center',
        // ...commonStyles,
      }}
    >
      <a
        href={homeUrl || '/'}
        target={homeUrl && homeUrl !== '/' ? '_blank' : undefined}
        rel={homeUrl && homeUrl !== '/' ? 'noreferrer' : undefined}
      >
        <div
          style={{
            height: size,
            position: 'relative',
          }}
        >
          {/* 使用原生 <img> 而非 next/image：项目已 images.unoptimized=true，
              next/image 的 dev 尺寸一致性警告（style width:auto 与 prop width 不一致）不再触发 */}
          <img
            src={wideLogoSrc}
            alt='logo'
            width={wideWidth}
            height={size}
            style={{
              width: 'auto',
              height: size,
              position: isRow ? 'relative' : 'absolute',
              top: 0,
              left: 0,
              opacity: isRow ? 1 : 0,
              transition: 'opacity 200ms ease',
            }}
            loading='eager'
            fetchPriority='high'
          />
          <img
            src={squareLogoSrc}
            alt='logo'
            width={size}
            height={size}
            style={{
              width: size,
              height: size,
              position: !isRow ? 'relative' : 'absolute',
              top: 0,
              left: 0,
              opacity: isRow ? 0 : 1,
              transition: 'opacity 200ms ease',
            }}
            loading='eager'
            fetchPriority='high'
          />
        </div>
      </a>
    </div>
  );
};

export default memo(LogoWithText);
