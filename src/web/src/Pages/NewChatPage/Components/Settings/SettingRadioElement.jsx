import { Radio, Space } from 'antd';
import { useCallback } from 'react';
import { useEffect } from 'react';
import { useState } from 'react';

export const SettingRadioElement = ({
  title = '',
  options = [],
  value = '',
  onChange = (e) => {},
}) => {
  const [curr, setCurr] = useState(value);

  useEffect(() => {
    setCurr(value);
  }, [value]);

  const _onChange = useCallback(
    (e) => {
      setCurr(e.target.value);
      onChange(e.target.value);
    },
    [setCurr, onChange]
  );

  return (
    <div>
      <div>{title}</div>
      <div>
        <Radio.Group onChange={_onChange} value={curr}>
          <Space direction="vertical">
            {options.map((v) => {
              const { label, value } = v;
              <Radio value={value}>{label}</Radio>;
            })}
          </Space>
        </Radio.Group>
      </div>
    </div>
  );
};
