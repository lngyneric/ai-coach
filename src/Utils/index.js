const token = process.env.REACT_APP_TOKEN;
const apiUrl = `https://test-api-sifu.agiclass.cn/api/study/run?token=${token}`;
const TIMEOUT = 300;
let timerOut = null;
let timerOutCount = 0;
let errorTryCount = 0;

export const Run = (data, options, oldContent = '') => {

  let xtextContent = oldContent;
  const params = { ...data };
  console.log('datadatadata',params)
  delete params.path;

  const evtSource = new EventSource(apiUrl, {
    headers: {
      Authorization: `Bearer ${window.localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    method: 'POST',
    payload: JSON.stringify(params),
  });

  const resetTimer = () => {
    clearInterval(timerOut);
    timerOutCount = 0;
    timerOut = setInterval(() => {
      if (timerOutCount > TIMEOUT) {
        clearInterval(timerOut);
        timerOutCount = 0;
        options.onEnd({ content: xtextContent, canResend: true });
        evtSource.close();
      }
      timerOutCount += 1;
    }, 1000);
  };

  evtSource.onopen = () => {};

  evtSource.onmessage = async (e) => {
    resetTimer();
    let response;
    try {
      response = JSON.parse(evtSource?.xhr?.response || '{}');
      console.log('response',response)
    } catch (error) {
      console.error('Error parsing response:', error);
    }

    const msg = e?.data;
    const resultData = JSON.parse(msg || '{}');

    if (msg.indexOf('[DONE]') !== -1) {
      evtSource.close();
      options.onEnd({ content: xtextContent, status: 'finish' });
      clearInterval(timerOut);
      return;
    }

    xtextContent += resultData?.choices?.[0]?.delta?.content || '';
    options.onMessage({ content: xtextContent });
  };

  evtSource.onerror = (error) => {
    console.error('EventSource error:', error);
    errorTryCount += 1;
    if (errorTryCount > 3) {
      evtSource.close();
      options.onEnd({ content: xtextContent, canResend: true, error: 'Too many errors, connection closed.' });
    }
  };
};
