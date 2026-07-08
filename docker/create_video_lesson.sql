-- Fill required fields
UPDATE shifu_published_shifus SET llm='', llm_temperature=0.3, llm_system_prompt='', ask_enabled_status=5101, ask_llm='', ask_llm_temperature=0.3, ask_llm_system_prompt='', price=0 WHERE shifu_bid='2136209a044041e99d78973d3c75fa86';
UPDATE shifu_draft_shifus SET llm='', llm_temperature=0.3, llm_system_prompt='', ask_enabled_status=5101, ask_llm='', ask_llm_temperature=0.3, ask_llm_system_prompt='', price=0 WHERE shifu_bid='2136209a044041e99d78973d3c75fa86';

SET @uid = '45cfd6b13cee4a92a311769a401ee29c';
SET @sid = '2136209a044041e99d78973d3c75fa86';
SET @ch = REPLACE(UUID(),'-','');
SET @ls = REPLACE(UUID(),'-','');

-- Chapter outline
INSERT INTO shifu_published_outline_items (outline_item_bid, shifu_bid, title, type, hidden, parent_bid, position, content, prerequisite_item_bids, llm, llm_temperature, llm_system_prompt, ask_enabled_status, ask_llm, ask_llm_temperature, ask_llm_system_prompt, deleted, created_user_bid, updated_user_bid, created_at, updated_at) VALUES (@ch, @sid, '建立主流口碑', 1, 0, '', '01', '', '', '', 0.3, '', 5101, '', 0.3, '', 0, @uid, @uid, NOW(), NOW());
INSERT INTO shifu_draft_outline_items (outline_item_bid, shifu_bid, title, type, hidden, parent_bid, position, content, prerequisite_item_bids, llm, llm_temperature, llm_system_prompt, ask_enabled_status, ask_llm, ask_llm_temperature, ask_llm_system_prompt, deleted, created_user_bid, updated_user_bid, created_at, updated_at) VALUES (@ch, @sid, '建立主流口碑', 1, 0, '', '01', '', '', '', 0.3, '', 5101, '', 0.3, '', 0, @uid, @uid, NOW(), NOW());

-- Lesson with video
INSERT INTO shifu_published_outline_items (outline_item_bid, shifu_bid, title, type, hidden, parent_bid, position, content, prerequisite_item_bids, llm, llm_temperature, llm_system_prompt, ask_enabled_status, ask_llm, ask_llm_temperature, ask_llm_system_prompt, deleted, created_user_bid, updated_user_bid, created_at, updated_at) VALUES (@ls, @sid, 'Lesson 01: 建立主流口碑', 2, 0, @ch, '0101', '# 中欧-建立主流口碑\n\n[video]https://video.sysmex.com.cn/304e2221703571f182df4531959d0102/9cd7112d30a54824bf074039d24cd1a8-325ad47ab11af91da77d997fdde6786f-sd.m3u8[/video]', '', '', 0.3, '', 5101, '', 0.3, '', 0, @uid, @uid, NOW(), NOW());
INSERT INTO shifu_draft_outline_items (outline_item_bid, shifu_bid, title, type, hidden, parent_bid, position, content, prerequisite_item_bids, llm, llm_temperature, llm_system_prompt, ask_enabled_status, ask_llm, ask_llm_temperature, ask_llm_system_prompt, deleted, created_user_bid, updated_user_bid, created_at, updated_at) VALUES (@ls, @sid, 'Lesson 01: 建立主流口碑', 2, 0, @ch, '0101', '# 中欧-建立主流口碑\n\n[video]https://video.sysmex.com.cn/304e2221703571f182df4531959d0102/9cd7112d30a54824bf074039d24cd1a8-325ad47ab11af91da77d997fdde6786f-sd.m3u8[/video]', '', '', 0.3, '', 5101, '', 0.3, '', 0, @uid, @uid, NOW(), NOW());

-- Enroll
INSERT IGNORE INTO course_enrollments (user_bid, shifu_bid, trainer_bid, module, status, progress_pct, created_at, updated_at) VALUES (@uid, @sid, @uid, 'leadership', 'assigned', 0, NOW(), NOW());

SELECT 'Done' AS status;
SELECT shifu_bid, title, keywords FROM shifu_published_shifus WHERE shifu_bid=@sid;
SELECT oi.title, LEFT(oi.content,80) AS preview FROM shifu_published_outline_items oi WHERE oi.shifu_bid=@sid AND oi.content!='' LIMIT 1;
