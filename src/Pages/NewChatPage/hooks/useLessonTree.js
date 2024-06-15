import { useState } from "react";
import { getLessonTree } from '@Api/lesson.js';
import { produce } from 'immer';

export const useLessonTree = () => {
  const [tree, setTree] = useState(null);

  const loadTree = async () => {
    const resp = await getLessonTree();
    const treeData = resp.data;

    treeData.categoryCount = 0;
    treeData.sectionCount = 0;
    
    treeData.catalogs = treeData.lessons.map(l => {
      const chapters = l.children.map(c => ({
        id: l.lesson_id,
        name: l.lesson_name,
      }));

      return {
        id: l.lesson_id,
        name: l.lesson_name,
        status: l.status,
        chapters,
        collapse: false,
      };
    })

    setTree(treeData);
  }

  const setCurr = async(chapterId) => {
    if (!tree) {
      return
    }

    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        c.chapters.forEach(ch => {
          if (ch.id === chapterId) {
            ch.selected = true;
          } else {
            ch.selected = false;
          }
        });
      });
    });

    setTree(nextState);
  }

  const toggleExpand = (lessonId) => {
    const nextState = produce(tree, draft => {
      draft.catalogs.forEach(c => {
        if (c.id === lessonId) {
          c.collapse = !c.collapse;
        }
      })
    });

    setTree(nextState);
  }

  return [tree, loadTree, setCurr, toggleExpand]
}
