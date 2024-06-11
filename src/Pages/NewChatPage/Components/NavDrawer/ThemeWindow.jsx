import PopupModal from '@Components/PopupModal';

export const ThemeWindow = ({ open, onClose, style }) => {
  return (
    <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style}}>
      <div style={{ 
        display: 'flex', 
        height: '100px', 
        verticalAlign: 'middle', 
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        敬请期待
      </div>
    </PopupModal>
  )
}

export default ThemeWindow;
