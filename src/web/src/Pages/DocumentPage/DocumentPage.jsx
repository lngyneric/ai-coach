import { Row, Col } from "antd";
import DocumentList from "./DocumentList";
import DocumentRender from "./DocumentRender";
import { useState } from "react";
import { GetDocumentById } from "../../Api/document";
import { UploadEvent } from "../../Api/UploadEvent";
import "./DocumentPage.css";
// import inputText from "./设计文档.js";

const DocumentPage = () => {
  UploadEvent("DocumentPage", { page: "document" });
  const [input, setInput] = useState();
  const [documentName, setDocumentName] = useState("");
  const onClickListItem = (documentInfo) => {
    UploadEvent("view_document", { page: "document" });
    setDocumentName(documentInfo.title);
    const document_id = documentInfo.document_id;

    GetDocumentById(document_id).then((res) => {
      console.log(res);
      // input = res.data.
      setInput(res.data.content);
    });
  };

  return (
    <div className="full-height document-page" gutter={16}>
      <DocumentList onClickListItem={onClickListItem}></DocumentList>
      <DocumentRender
        markdownData={input}
        loading={false}
        documentName={documentName}
      ></DocumentRender>
    </div>
  );
};

export default DocumentPage;
