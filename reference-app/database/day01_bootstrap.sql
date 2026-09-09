-- Day 1 최소 인증·조직 bootstrap
-- 대상: 폐기 가능한 새 Supabase 실습 프로젝트
-- 반복 실행 가능하며 기존 행을 덮어쓰거나 삭제하지 않는다.
-- Day 2의 refresh_tokens와 Day 3의 audit_logs는 각 Day migration이 소유한다.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corp_code VARCHAR(20) NOT NULL,
    corp_id VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name_kr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    biz_no VARCHAR(20),
    corp_no VARCHAR(20),
    corp_type VARCHAR(1) DEFAULT '1',
    is_sme VARCHAR(1) DEFAULT '0',
    ceo_name VARCHAR(50),
    nationality VARCHAR(1) DEFAULT '0',
    ceo_jumin VARCHAR(255),
    zip_code VARCHAR(10),
    address1 VARCHAR(255),
    address2 VARCHAR(255),
    tel_no VARCHAR(20) NOT NULL,
    fax VARCHAR(20),
    biz_type_code VARCHAR(20),
    biz_status VARCHAR(20),
    branch_type VARCHAR(1) DEFAULT '0',
    main_office_code VARCHAR(20),
    fiscal_year INTEGER,
    corp_category VARCHAR(2) DEFAULT '20',
    bank_name VARCHAR(50),
    bank_account VARCHAR(50),
    bank_holder VARCHAR(50),
    responsible_emp_id UUID,
    create_date TIMESTAMPTZ DEFAULT NOW(),
    update_date TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT ck_companies_corp_category
        CHECK (corp_category IN ('10', '20', '30'))
);

CREATE TABLE IF NOT EXISTS public.departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corp_id VARCHAR(50) NOT NULL
        REFERENCES public.companies(corp_id) ON DELETE CASCADE,
    dept_code VARCHAR(20) NOT NULL,
    dept_name VARCHAR(50) NOT NULL,
    is_used VARCHAR(1) DEFAULT 'Y',
    manager_id UUID,
    create_date TIMESTAMPTZ DEFAULT NOW(),
    update_date TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_departments_corp_code UNIQUE (corp_id, dept_code),
    CONSTRAINT ck_departments_is_used CHECK (is_used IN ('Y', 'N'))
);

CREATE TABLE IF NOT EXISTS public.employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corp_id VARCHAR(50) NOT NULL
        REFERENCES public.companies(corp_id) ON DELETE CASCADE,
    dept_id UUID REFERENCES public.departments(id),
    user_id VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    emp_code VARCHAR(20),
    emp_name VARCHAR(50) NOT NULL,
    class_code INTEGER,
    join_date DATE,
    change_reason VARCHAR(255),
    change_date DATE,
    tel_no VARCHAR(20),
    is_working VARCHAR(1) DEFAULT 'Y',
    role VARCHAR(20) DEFAULT 'STAFF',
    responsible_emp_id UUID,
    create_date TIMESTAMPTZ DEFAULT NOW(),
    update_date TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_employees_corp_emp_code UNIQUE (corp_id, emp_code),
    CONSTRAINT ck_employees_is_working CHECK (is_working IN ('Y', 'N')),
    CONSTRAINT ck_employees_role CHECK (role IN ('STAFF', 'MANAGER', 'ADMIN'))
);

DO $department_manager_fk$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conrelid = 'public.departments'::regclass
           AND conname = 'fk_departments_manager'
    ) THEN
        ALTER TABLE public.departments
            ADD CONSTRAINT fk_departments_manager
            FOREIGN KEY (manager_id)
            REFERENCES public.employees(id)
            ON DELETE SET NULL;
    END IF;
END
$department_manager_fk$;

CREATE TABLE IF NOT EXISTS public.login_history (
    id BIGSERIAL PRIMARY KEY,
    corp_id VARCHAR(50),
    user_id UUID,
    user_type VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE,
    failure_reason TEXT,
    login_date TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.basiccode10 (
    id BIGSERIAL PRIMARY KEY,
    main_code VARCHAR(20) NOT NULL,
    sub_code VARCHAR(20) NOT NULL,
    code VARCHAR(20) NOT NULL,
    code_name VARCHAR(100) NOT NULL,
    rem TEXT,
    create_date TIMESTAMPTZ DEFAULT NOW(),
    update_date TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_basiccode10_code UNIQUE (main_code, sub_code, code)
);

CREATE TABLE IF NOT EXISTS public.corp_class (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_code INTEGER UNIQUE NOT NULL,
    class_name VARCHAR(30) NOT NULL,
    class_name_eng VARCHAR(30),
    create_date TIMESTAMPTZ DEFAULT NOW(),
    is_use VARCHAR(1) DEFAULT 'T',
    CONSTRAINT ck_corp_class_is_use CHECK (is_use IN ('T', 'F'))
);

CREATE INDEX IF NOT EXISTS idx_companies_corp_id
    ON public.companies(corp_id);
CREATE INDEX IF NOT EXISTS idx_employees_user_id
    ON public.employees(user_id);
CREATE INDEX IF NOT EXISTS idx_basiccode_main
    ON public.basiccode10(main_code, sub_code);
CREATE INDEX IF NOT EXISTS idx_corp_class_code
    ON public.corp_class(class_code);

INSERT INTO public.basiccode10 (
    main_code, sub_code, code, code_name, rem
) VALUES
    ('MEM100', '100', '10', '본사', '본사 구분 코드'),
    ('MEM100', '100', '20', '가맹점', '가맹점 구분 코드'),
    ('MEM100', '100', '30', '공급사', '공급사 구분 코드'),
    ('EMP100', '110', '0', '선택', ''),
    ('EMP100', '110', '1', '입사', ''),
    ('EMP100', '110', '2', '부서이동', ''),
    ('EMP100', '110', '3', '전출', ''),
    ('EMP100', '110', '4', '퇴출', ''),
    ('EMP100', '110', '9', '기타', ''),
    ('EMP100', '120', 'Y', '근무', ''),
    ('EMP100', '120', 'N', '비근무', '')
ON CONFLICT (main_code, sub_code, code) DO NOTHING;

INSERT INTO public.corp_class (
    class_code, class_name, class_name_eng
) VALUES
    (1, '사원', 'Staff'),
    (2, '대리', 'Assistant Manager'),
    (3, '과장', 'Manager'),
    (4, '차장', 'Deputy General Manager'),
    (5, '부장', 'General Manager')
ON CONFLICT (class_code) DO NOTHING;

-- 로컬·폐기형 실습 프로젝트에서만 사용하는 최초 본사 계정이다.
INSERT INTO public.companies (
    corp_code, corp_id, password, name_kr, corp_category, corp_type, tel_no
) VALUES (
    'HQ001',
    'admin',
    '$2b$12$MuhL3W2/.YXNLnEPkBgz5ekJv8gRL84JzR8GlLWWVYmnSwgQPf1Mu',
    'LDK ERP 본사',
    '10',
    '0',
    '000-0000-0036'
)
ON CONFLICT (corp_id) DO NOTHING;

-- 자격정보가 포함된 테이블은 Day 1에서 Data API 역할에 열지 않는다.
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.basiccode10 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.corp_class ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE
    public.companies,
    public.departments,
    public.employees,
    public.login_history,
    public.basiccode10,
    public.corp_class
FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.basiccode10, public.corp_class TO authenticated;
GRANT ALL ON TABLE
    public.companies,
    public.departments,
    public.employees,
    public.login_history,
    public.basiccode10,
    public.corp_class
TO service_role;
GRANT USAGE, SELECT ON SEQUENCE
    public.login_history_id_seq,
    public.basiccode10_id_seq
TO service_role;

DO $day01_reference_policies$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
         WHERE schemaname = 'public'
           AND tablename = 'basiccode10'
           AND policyname = 'day01_basiccode_authenticated_read'
    ) THEN
        CREATE POLICY day01_basiccode_authenticated_read
            ON public.basiccode10
            FOR SELECT TO authenticated
            USING (TRUE);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
         WHERE schemaname = 'public'
           AND tablename = 'corp_class'
           AND policyname = 'day01_corp_class_authenticated_read'
    ) THEN
        CREATE POLICY day01_corp_class_authenticated_read
            ON public.corp_class
            FOR SELECT TO authenticated
            USING (TRUE);
    END IF;
END
$day01_reference_policies$;

COMMIT;
