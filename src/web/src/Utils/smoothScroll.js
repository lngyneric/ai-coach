export function smoothScroll({ el, to, duration = 300, scrollLeft = false }) {
  let count = 0;
  const attr = scrollLeft ? 'scrollLeft' : 'scrollTop';
  const from = el[attr];
  const frames = Math.round(duration / 16);
  const step = (to - from) / frames;

  if (!requestAnimationFrame) {
    el[attr] = to;
    return;
  }

  function animate() {
    // eslint-disable-next-line no-param-reassign
    el[attr] += step;

    // eslint-disable-next-line no-plusplus
    if (++count < frames) {
      requestAnimationFrame(animate);
    }
  }

  animate();
}
