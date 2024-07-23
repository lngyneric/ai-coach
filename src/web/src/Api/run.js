import { run } from "@Api/chat";

const runHandler = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).end(); // Method Not Allowed
    return;
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const { lesson_id, input } = req.body;

  try {
    const response = await run({ lesson_id, input, input_type: "continue" });

    // 订阅流并发送消息
    response.on("data", (message) => {
      res.write(`data: ${JSON.stringify(message)}\n\n`);
    });

    response.on("end", () => {
      res.end();
    });

  } catch (error) {
    console.error("Error sending message:", error);
    res.status(500).end();
  }
};

export default runHandler;
