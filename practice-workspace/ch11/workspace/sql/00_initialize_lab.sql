-- 폐기 가능한 Chapter 11 전용 실습 DB에서만 실행하세요.
-- 이 표식이 없는 데이터베이스에서는 99_reset_lab.sql이 중단됩니다.

CREATE TABLE IF NOT EXISTS public.foundation_lab_marker (
    lab_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.foundation_lab_marker (lab_id)
VALUES ('chapter11')
ON CONFLICT (lab_id) DO NOTHING;
