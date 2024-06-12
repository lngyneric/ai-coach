const MODAL_DEFAULT_WIDTH = '360px';
export const calModalWidth = ({ inMobile, width = MODAL_DEFAULT_WIDTH }) => {
  return inMobile ? '100%' : width;
}
