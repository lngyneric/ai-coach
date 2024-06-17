import { useState } from "react";
import { getLessonTree } from '@Api/lesson.js';
import { produce } from 'immer';
import { SECTION_STATUS } from "constants/courseContants.js";

export const catalogAvailableInner = (tree, catalogId) => {
  const catalog = tree.catalogs.find(v => v.id === catalogId)

  if (!catalog) {
    return false;
  }

  return catalog.status === SECTION_STATUS.LEARNING || catalog.status === SECTION_STATUS.COMPLETED;
}

export const getRunningElementInner = (tree) => {
    const catalog = tree.catalogs.find(v => v.status === SECTION_STATUS.LEARNING)

    if (!catalog) {
      return null;
    }

    const chapter = catalog.chapters.find(v => v.status === SECTION_STATUS.LEARNING)

    return { catalog, chapter };
}

export const useLessonTree = () => {
  const [tree, setTree] = useState(null);

  const loadTree = async () => {
    const resp = await getLessonTree();
    const treeData = resp.data;

    let chapterCount = 0;    
    const catalogs = treeData.lessons.map(l => {
      const chapters = l.children.map(c => {
        chapterCount += 1;
        return {
          id: c.lesson_id,
          name: c.lesson_name,
          status: c.status,
        }
      });

      return {
        id: l.lesson_id,
        name: l.lesson_name,
        status: l.status,
        chapters,
        collapse: false,
      };
    });

    const newTree = {
      catalogCount: catalogs.length,
      catalogs,
      chapterCount,
    }
    setTree(newTree);



    return newTree;
  }

  const setCurr = async(chapterId) => {
    if (!tree) {
      return
    }

    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        c.chapters.forEach(ch => {
          if (ch.id === chapterId) {
            c.collapse = false;
            ch.selected = true;
          } else {
            ch.selected = false;
          }
        });
      });
    });

    setTree(nextState);
  }

  const setCurrCatalog = async (catalogId) => {
    if (!tree) {
      return
    }

    const ca = tree.catalogs.find(c => c.id === catalogId);
    if (!ca) {
      return
    }

    const c = ca.chapters[0];
    if (!c) {
      return
    }

    setCurr(c.id);

  }

  const toggleCollapse = ({id}) => {
    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        if (c.id === id) {
          c.collapse = !c.collapse;
        }
      })
    });

    setTree(nextState);
  }

  const catalogAvailable = (catalogId) => {

    const catalog = tree.catalogs.find(v => v.id === catalogId)

    if (!catalog) {
      return false;
    }

    return catalog.status === SECTION_STATUS.LEARNING || catalog.status === SECTION_STATUS.COMPLETED;
  }

  const getRunningElement = () => {
    if (!tree) {
      return null;
    }

    return getRunningElementInner(tree);
  }


  return { tree, loadTree, setCurr, setCurrCatalog, toggleCollapse, catalogAvailable, getRunningElement }
}
