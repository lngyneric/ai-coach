import { useState, useRef } from 'react';

const DEFAULT_COUNTDOWN = 5;

export const useSendCode = ({ countDownTime = DEFAULT_COUNTDOWN }) => {
  const [countDown, setCountDown] = useState(0);
  let timer = useRef();

  const sendCode = async (mobile) => {
    if (!!countDown) {
      throw new Error(`${countDownTime}秒内只能发送一次`);
    }

    // send code logic
    setCountDown(countDownTime);

    timer.current = setInterval(() => {
      setCountDown(countDown => {
        console.log('sendCode', countDown);
        if (countDown === 0) {
          clearInterval(timer.current);
          timer.current = null;
          return 0;
        }
        return countDown - 1
      });
    }, 1000);
  }

  const reset = () => {
    setCountDown(0);
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }

  return [countDown, sendCode, reset];
}

export default useSendCode;
