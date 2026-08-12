import {
  appendCustomButtonAfterContent,
  hasCustomButtonAfterContent,
  inheritCustomButtonAfterContent,
  resolveAssetSrc,
  sanitizeEmptyImageBlocks,
  syncCustomButtonAfterContent,
} from './chatUiUtils';

describe('chatUiUtils', () => {
  const buttonMarkup =
    '<custom-button-after-content><span>Ask</span></custom-button-after-content>';

  it('re-appends the follow-up button when read mode restores mobile content', () => {
    const contentWithoutButton = 'Lesson summary';

    expect(
      syncCustomButtonAfterContent({
        content: contentWithoutButton,
        buttonMarkup,
        shouldShowButton: true,
      }),
    ).toBe(appendCustomButtonAfterContent(contentWithoutButton, buttonMarkup));
  });

  it('removes the follow-up button when listen mode content is rendered', () => {
    const contentWithButton = appendCustomButtonAfterContent(
      'Lesson summary',
      buttonMarkup,
    );

    expect(
      syncCustomButtonAfterContent({
        content: contentWithButton,
        buttonMarkup,
        shouldShowButton: false,
      }),
    ).toBe('Lesson summary');
  });

  it('detects the follow-up button markup in content', () => {
    const contentWithButton = appendCustomButtonAfterContent(
      'Lesson summary',
      buttonMarkup,
    );

    expect(hasCustomButtonAfterContent(contentWithButton)).toBe(true);
    expect(hasCustomButtonAfterContent('Lesson summary')).toBe(false);
  });

  it('inherits the follow-up button from previous finalized content', () => {
    const previousContent = appendCustomButtonAfterContent(
      'Lesson summary',
      buttonMarkup,
    );

    expect(
      inheritCustomButtonAfterContent({
        nextContent: 'Updated lesson summary',
        previousContent,
        buttonMarkup,
      }),
    ).toBe(
      appendCustomButtonAfterContent('Updated lesson summary', buttonMarkup),
    );
  });

  it('sanitizeEmptyImageBlocks drops empty markdown/html image urls', () => {
    expect(sanitizeEmptyImageBlocks('before ![alt]() after')).toBe(
      'before  after',
    );
    expect(sanitizeEmptyImageBlocks('![x]()')).toBe('');
    expect(sanitizeEmptyImageBlocks('a <img src=""> b')).toBe('a  b');
    expect(sanitizeEmptyImageBlocks('a <img src="undefined"> b')).toBe(
      'a  b',
    );
    // non-empty urls must survive
    expect(sanitizeEmptyImageBlocks('![alt](/img/a.png)')).toBe(
      '![alt](/img/a.png)',
    );
    expect(sanitizeEmptyImageBlocks('a <img src="/x.png"> b')).toBe(
      'a <img src="/x.png"> b',
    );
    // null/undefined input
    expect(sanitizeEmptyImageBlocks(null)).toBe('');
    expect(sanitizeEmptyImageBlocks(undefined)).toBe('');
  });

  it('resolveAssetSrc normalizes string and {src} asset shapes', () => {
    expect(resolveAssetSrc('/static/icon.svg')).toBe('/static/icon.svg');
    expect(resolveAssetSrc({ src: '/static/icon.svg' })).toBe(
      '/static/icon.svg',
    );
    expect(resolveAssetSrc({ src: '' })).toBe('');
    expect(resolveAssetSrc({})).toBe('');
    expect(resolveAssetSrc(null)).toBe('');
    expect(resolveAssetSrc(undefined)).toBe('');
    expect(resolveAssetSrc('  ')).toBe('');
  });
});
