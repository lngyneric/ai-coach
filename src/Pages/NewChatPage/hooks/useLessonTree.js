import { useState } from "react";
import { getLessonTree } from '@Api/lesson.js';
import { produce } from 'immer';

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

    setTree({
      catalogCount: catalogs.length,
      catalogs,
      chapterCount,
    });
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

  const toggleCollapse = ({id}) => {
    const nextState = produce(tree, draft => {
      console.log('toggle', draft.catalogs, id);
      draft.catalogs.forEach(c => {
        console.log('catalogs.forEach', c)
        if (c.id === id) {
          c.collapse = !c.collapse;
        }
      })
    });

    console.log('nextState', nextState)

    setTree(nextState);
  }

  return [tree, loadTree, setCurr, toggleCollapse]
}
