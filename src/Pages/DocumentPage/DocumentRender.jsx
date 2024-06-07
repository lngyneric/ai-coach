import { ReactMarkdown } from "react-markdown/lib/react-markdown";
import "./DocumentRender.css";
import { Empty, Spin } from "antd";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
/**
 *
 * @param {String} markdownData - markdown 文档内容
 * @param {String} documentName - markdonw 文档名称
 * @param {Boolean} loading - loading 状态
 * @returns
 */
const DocumentRender = ({ markdownData, documentName, loading }) => {
  const renderMarkdown = (() => {
    if (markdownData) {
      return (
        <div className="document-content">
          <ReactMarkdown
            children={markdownData}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || "");
                return !inline && match ? (
                  <SyntaxHighlighter
                    {...props}
                    children={String(children).replace(/\n$/, "")}
                    style={vscDarkPlus}
                    language={match[1]}
                    showLineNumbers={true}
                    wrapLongLines={true}
                  />
                ) : (
                  <code {...props} className={className}>
                    {children}
                  </code>
                );
              },
              img(props) {
                return <img {...props} style={{ maxWidth: "100%" }} />;
              },
            }}
          ></ReactMarkdown>
        </div>
      );
    } else {
      return (
        <div className="document-content_emty">
          <Empty description="还没有打开文档"></Empty>
        </div>
      );
    }
  })();

  return (
    <div className="document-render">
      <Spin tip="Loading" size="large" spinning={loading}>
        <div
          style={{ display: documentName ? "block" : "none" }}
          className="document-name_header"
        >
          {documentName}
        </div>
        {renderMarkdown}
      </Spin>
    </div>
  );
};

export default DocumentRender;
