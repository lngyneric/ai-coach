import React, { useEffect, useState } from 'react';

const SSEComponent = () => {
    const [messages, setMessages] = useState([]);
    const token = process.env.REACT_APP_TOKEN;

    useEffect(() => {
        const eventSource = new EventSource(`https://test-api-sifu.agiclass.cn/api/study/run?token=${token}`);

        eventSource.onmessage = (event) => {
            const newMessage = JSON.parse(event.data);
            setMessages((prevMessages) => [...prevMessages, newMessage]);
        };

        eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [token]);

    return (
        <div>
            <h1>Server-Sent Events</h1>
            <ul>
                {messages.map((msg, index) => (
                    <li key={index}>
                        {msg.timestamp}: {msg.message}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default SSEComponent;
