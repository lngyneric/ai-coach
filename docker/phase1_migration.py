#!/usr/bin/env python3
"""Phase 1: Database migration for learner profile & mentorship system."""
import pymysql

conn = pymysql.connect(host='ai-shifu-mysql', user='root', password='ai-shifu', database='ai-shifu')
cur = conn.cursor()

print('=== Phase 1a: user_users extend ===')
new_cols = {
    'employee_no': "VARCHAR(50) DEFAULT NULL COMMENT 'employee number'",
    'department': "VARCHAR(100) DEFAULT NULL COMMENT 'department'",
    'position_name': "VARCHAR(100) DEFAULT NULL COMMENT 'position'",
    'level': "VARCHAR(20) DEFAULT NULL COMMENT 'level'",
    'mentor_bid': "VARCHAR(32) DEFAULT NULL COMMENT 'mentor user_bid'",
    'supervisor_bid': "VARCHAR(32) DEFAULT NULL COMMENT 'supervisor user_bid'",
    'onboarding_date': "DATE DEFAULT NULL COMMENT 'onboarding date'",
    'probation_end_date': "DATE DEFAULT NULL COMMENT 'probation end date'",
}
for col, definition in new_cols.items():
    try:
        cur.execute(f"ALTER TABLE user_users ADD COLUMN {col} {definition}")
        print(f'  OK  {col}')
    except pymysql.err.OperationalError as e:
        if 'Duplicate' in str(e):
            print(f'  SKIP  {col} (already exists)')
        else:
            raise e
conn.commit()

print()
print('=== Phase 1b: Create 7 tables ===')

tables = {
    'learner_profiles': """
        CREATE TABLE IF NOT EXISTS learner_profiles (
          learner_bid VARCHAR(32) PRIMARY KEY,
          user_bid VARCHAR(32) NOT NULL,
          employee_no VARCHAR(50) DEFAULT NULL,
          department VARCHAR(100) DEFAULT NULL,
          position_name VARCHAR(100) DEFAULT NULL,
          level VARCHAR(20) DEFAULT NULL,
          mentor_bid VARCHAR(32) DEFAULT NULL,
          supervisor_bid VARCHAR(32) DEFAULT NULL,
          onboarding_date DATE DEFAULT NULL,
          probation_end_date DATE DEFAULT NULL,
          status VARCHAR(20) DEFAULT 'active',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_lp_user (user_bid),
          INDEX idx_lp_mentor (mentor_bid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'mentorship_phases': """
        CREATE TABLE IF NOT EXISTS mentorship_phases (
          phase_bid VARCHAR(32) PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          code VARCHAR(20) NOT NULL,
          description TEXT,
          sort_order INT DEFAULT 0,
          duration_days INT DEFAULT 60,
          passing_score DECIMAL(5,2) DEFAULT 60.00,
          theory_weight DECIMAL(3,2) DEFAULT 0.40,
          practice_weight DECIMAL(3,2) DEFAULT 0.30,
          review_weight DECIMAL(3,2) DEFAULT 0.20,
          mentor_weight DECIMAL(3,2) DEFAULT 0.10,
          is_active TINYINT(1) DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'learner_mentorship': """
        CREATE TABLE IF NOT EXISTS learner_mentorship (
          record_bid VARCHAR(32) PRIMARY KEY,
          learner_bid VARCHAR(32) NOT NULL,
          phase_bid VARCHAR(32) NOT NULL,
          status VARCHAR(20) DEFAULT 'pending',
          started_at DATETIME DEFAULT NULL,
          completed_at DATETIME DEFAULT NULL,
          theory_score DECIMAL(5,2) DEFAULT NULL,
          practice_score DECIMAL(5,2) DEFAULT NULL,
          peer_review_score DECIMAL(5,2) DEFAULT NULL,
          mentor_score DECIMAL(5,2) DEFAULT NULL,
          total_score DECIMAL(5,2) DEFAULT NULL,
          retry_count INT DEFAULT 0,
          remark TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_lm_learner (learner_bid),
          INDEX idx_lm_phase (phase_bid),
          INDEX idx_lm_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'mentorship_checklist': """
        CREATE TABLE IF NOT EXISTS mentorship_checklist (
          item_bid VARCHAR(32) PRIMARY KEY,
          phase_bid VARCHAR(32) NOT NULL,
          name VARCHAR(200) NOT NULL,
          description TEXT,
          category VARCHAR(20) NOT NULL,
          max_score DECIMAL(5,2) DEFAULT 5.00,
          sort_order INT DEFAULT 0,
          is_required TINYINT(1) DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_mc_phase (phase_bid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'learner_checklist_items': """
        CREATE TABLE IF NOT EXISTS learner_checklist_items (
          record_bid VARCHAR(32) PRIMARY KEY,
          learner_bid VARCHAR(32) NOT NULL,
          item_bid VARCHAR(32) NOT NULL,
          score DECIMAL(5,2) DEFAULT NULL,
          scored_by VARCHAR(32) DEFAULT NULL,
          comment TEXT,
          status VARCHAR(20) DEFAULT 'pending',
          submitted_at DATETIME DEFAULT NULL,
          scored_at DATETIME DEFAULT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_lci_learner (learner_bid),
          INDEX idx_lci_item (item_bid),
          INDEX idx_lci_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'learner_tasks': """
        CREATE TABLE IF NOT EXISTS learner_tasks (
          task_bid VARCHAR(32) PRIMARY KEY,
          learner_bid VARCHAR(32) NOT NULL,
          title VARCHAR(200) NOT NULL,
          description TEXT,
          task_type VARCHAR(20) NOT NULL,
          related_bid VARCHAR(32) DEFAULT NULL,
          due_at DATETIME DEFAULT NULL,
          completed_at DATETIME DEFAULT NULL,
          status VARCHAR(20) DEFAULT 'pending',
          created_by VARCHAR(32) DEFAULT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_lt_learner (learner_bid),
          INDEX idx_lt_status (status),
          INDEX idx_lt_due (due_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    'task_notifications': """
        CREATE TABLE IF NOT EXISTS task_notifications (
          notif_bid VARCHAR(32) PRIMARY KEY,
          user_bid VARCHAR(32) NOT NULL,
          title VARCHAR(200) DEFAULT NULL,
          content TEXT,
          notif_type VARCHAR(20) DEFAULT NULL,
          related_bid VARCHAR(32) DEFAULT NULL,
          is_read TINYINT(1) DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_tn_user (user_bid),
          INDEX idx_tn_read (is_read)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
}

for name, ddl in tables.items():
    try:
        cur.execute(ddl)
        print(f'  OK  {name}')
    except Exception as e:
        print(f'  FAIL  {name}: {e}')

conn.commit()

print()
print('=== Phase 1c: Insert training categories ===')
categories = [
    ('cat-006', '新人入学', 'onboarding', 6),
    ('cat-007', '学分制带教', 'mentorship', 7),
    ('cat-008', '小灶教学', 'intensive', 8),
    ('cat-009', '领导力课程', 'leadership', 9),
]
for bid, name, slug, sort in categories:
    try:
        cur.execute("INSERT INTO course_categories (category_bid, name, slug, sort_order, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW())", (bid, name, slug, sort))
        print(f'  OK  {name} ({slug})')
    except pymysql.err.IntegrityError as e:
        if 'Duplicate' in str(e):
            print(f'  SKIP  {name} (already exists)')
        else:
            raise e

conn.commit()
conn.close()
print()
print('Phase 1 complete!')
