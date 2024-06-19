import { useState } from "react";
import { getLessonTree } from '@Api/lesson.js';
import { produce } from 'immer';
import { LESSON_STATUS } from "constants/courseContants.js";

export const checkChapterCanLearning = ({ status }) => {
  return status === LESSON_STATUS.LEARNING || status === LESSON_STATUS.COMPLETED || status === LESSON_STATUS.PREPARE_LEARNING;
}

const getCurrElementInner = (tree) => {
  for (let catalog of tree.catalogs) {
    const lesson = catalog.lessons.find(v => v.selected === true);

    if (lesson) {
      return { catalog, lesson };
    }
  }

  return null;
}

export const initialSelectedChapter = (tree) => {
  let catalog = tree.catalogs.find(v => v.status === LESSON_STATUS.LEARNING);
  if (catalog) {
    const lesson = catalog.lessons.find(v => v.status === LESSON_STATUS.LEARNING || v.status === LESSON_STATUS.PREPARE_LEARNING);
    lesson && (lesson.selected = true);
  } else {
    catalog = tree.catalogs.find(v => v.status === LESSON_STATUS.PREPARE_LEARNING);
    if (catalog) {
      const lesson = catalog.lessons.find(v => v.status === LESSON_STATUS.LEARNING || v.status === LESSON_STATUS.PREPARE_LEARNING);
      lesson && (lesson.selected = true);
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

    let lessonCount = 0;    
    const catalogs = treeData.lessons.map(l => {
      const lessons = l.children.map(c => {
        lessonCount += 1;
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
        lessons,
        collapse: false,
      };
    });

    const newTree = {
      catalogCount: catalogs.length,
      catalogs,
      lessonCount,
    }
    initialSelectedChapter(newTree);
    setTree(newTree);
    setLoadedTree(true);

    return newTree;
  }

  const setCurr = async(chapterId, forceExpand = false) => {
    setTree(old => {
      if (!old) {
        return
      }

      const nextState = produce(old, draft => {
        draft.catalogs.forEach(c => {
          c.lessons.forEach(ls => {
            if (ls.id === chapterId) {
              if (forceExpand) {
                c.collapse = false;
              }
              ls.selected = true;
            } else {
              ls.selected = false;
            }
          });
        });
      });

      return nextState;
    });
  }

  const setCurrCatalog = async (catalogId) => {
    if (!tree) {
      return
    }

    const ca = tree.catalogs.find(c => c.id === catalogId);
    if (!ca) {
      return
    }

    const l = ca.lessons[0];
    if (!l) {
      return
    }

    setCurr(l.id);
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

    return catalog.status === LESSON_STATUS.LEARNING || catalog.status === LESSON_STATUS.COMPLETED || catalog.status === LESSON_STATUS.PREPARE_LEARNING;
  }

  const getCurrElement = () => {
    if (!tree) {
      return null;
    }

    return getCurrElementInner(tree);
  }

  const updateChapter = (id, val) => {
    setTree(old => {
      if (!old) {
        return
      }
      const nextState = produce(old, draft => {
        draft.catalogs.forEach(c => {
          const idx = c.lessons.findIndex(ch => ch.id === id)
          if (idx !== -1) {
            const newLesson = {
              ...c.lessons[idx],
              ...val
            };
            newLesson.canLearning = checkChapterCanLearning(newLesson);
            c.lessons[idx] = newLesson;
          }
        })
      });

      return nextState;
    });
  }


  return { tree, loadTree, treeLoaded, setCurr, setCurrCatalog, toggleCollapse, catalogAvailable, getCurrElement, updateChapter }
}
