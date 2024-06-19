import { useState } from "react";
import { getLessonTree } from '@Api/lesson.js';
import { produce } from 'immer';
import { SECTION_STATUS } from "constants/courseContants.js";

export const checkChapterCanLearning = ({ status }) => {
  return status === SECTION_STATUS.LEARNING || status === SECTION_STATUS.COMPLETED || status === SECTION_STATUS.PREPARE_LEARNING;
}

const getCurrElementInner = (tree) => {
  for (let catalog of tree.catalogs) {
    const chapter = catalog.chapters.find(v => v.selected === true);

    if (chapter) {
      return { catalog, chapter };
    }
  }

  return null;
}

export const initialSelectedChapter = (tree) => {
  let catalog = tree.catalogs.find(v => v.status === SECTION_STATUS.LEARNING);
  if (catalog) {
    const chapter = catalog.chapters.find(v => v.status === SECTION_STATUS.LEARNING);

    chapter && (chapter.selected = true);
  } else {
    catalog = tree.catalogs.find(v => v.status === SECTION_STATUS.PREPARE_LEARNING);
    if (catalog) {
      const chapter = catalog.chapters.find(v => v.status === SECTION_STATUS.PREPARE_LEARNING);
      chapter && (chapter.selected =true);
    }
  }
}

export const useLessonTree = () => {
  const [tree, setTree] = useState(null);
  const [treeLoaded, setLoadedTree] = useState(false);

  const loadTree = async () => {
    setLoadedTree(false);
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
          canLearning: checkChapterCanLearning(c),
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
    initialSelectedChapter(newTree);
    setTree(newTree);
    setLoadedTree(true);

    return newTree;
  }

  const setCurr = async(chapterId, forceExpand = false) => {
    if (!tree) {
      return
    }

    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        c.chapters.forEach(ch => {
          if (ch.id === chapterId) {
            if (forceExpand) {
              c.collapse = false;
            }
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

    return catalog.status === SECTION_STATUS.LEARNING || catalog.status === SECTION_STATUS.COMPLETED || catalog.status === SECTION_STATUS.PREPARE_LEARNING;
  }

  const getRunningElement = () => {
    if (!tree) {
      return null;
    }

    return getCurrElementInner(tree);
  }

  const updateChapter = (chapterId, val) => {
    if (!tree) {
      return
    }

    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        const idx = c.chapters.findIndex(ch => ch.id === chapterId)
        if (idx !== -1) {
          c.chapters[idx] = {
            ...c.chapters[idx],
            ...val
          };
        }
      })
    });

    setTree(nextState);
  }


  return { tree, loadTree, treeLoaded, setCurr, setCurrCatalog, toggleCollapse, catalogAvailable, getRunningElement, updateChapter }
}
