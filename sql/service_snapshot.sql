-- Denormalization query: flattens service data with metadata for embedding generation
-- Output columns must match the service_snapshots table schema
-- Place your denormalization SQL here
-- ============================================================
-- ShelterTech RAG Denormalization Query
-- One row per active service per address, with full prose + metadata
-- Filters: resources.status = 1, services.status = 1
-- Core categories: id 0-355 excluding 202 (MOHCD)
-- White-label metadata: SFSG (1000001-1000012), UCSF top (2000001-2000006),
--                       UCSF sub (2100001-2100016), OUR415 (356-362)
-- Granularity: service x address (multi-location services fan out)
-- ============================================================


-- -------------------------------------------------------
-- CTE 1: Eligibility name remapping
-- All remaps fully resolved — no ambiguous tags remaining.
-- Infectious Disease, College Students pass through unchanged.
-- Maturing Adult does not exist in DB yet — no handling needed.
-- -------------------------------------------------------
WITH eligibility_remapped AS (
    SELECT
        id,
        CASE name
            -- Previously ambiguous, now resolved
            WHEN 'Adolescents'                          THEN 'Youth (below 21 years old)'
            WHEN 'Alzheimers'                           THEN 'Chronic Illness'
            WHEN 'Cancer'                               THEN 'Chronic Illness'
            WHEN 'Dual Diagnosis'                       THEN 'Mental Illness'
            WHEN 'I live with someone under 18 years of age' THEN 'Families with children below 18 years old'
            WHEN 'Seizure Disorder'                     THEN 'Chronic Illness'
            WHEN 'Smoker'                               THEN 'Substance Dependency'
            WHEN 'Young Adults (18-27 years old)'       THEN 'Transitional Aged Youth (TAY)'
            WHEN 'Young Adults (20-30 years old)'       THEN 'Transitional Aged Youth (TAY)'
            WHEN 'Youth'                                THEN 'Youth (below 21 years old)'
            WHEN 'Intellectual Disability'              THEN 'Special Needs/Disabilities'
            -- Original clear remaps (with updates)
            WHEN 'API'                                  THEN 'API (Asian/Pacific Islander)'
            WHEN 'African American'                     THEN 'African/Black'
            WHEN 'Age 12-17'                            THEN 'Teens (13-18 years old)'
            WHEN 'Alcoholic'                            THEN 'Substance Dependency'
            WHEN 'Asian'                                THEN 'API (Asian/Pacific Islander)'
            WHEN 'Developmental Disability'             THEN 'Special Needs/Disabilities'
            WHEN 'Disabled'                             THEN 'Special Needs/Disabilities'
            WHEN 'Elderly'                              THEN 'I am a Senior'
            WHEN 'I am someone with disabilities'       THEN 'Special Needs/Disabilities'
            WHEN 'Learning Disability'                  THEN 'Special Needs/Disabilities'
            WHEN 'Limited English'                      THEN 'ESL/ELL (English Language Learner)'
            WHEN 'Mentally Incapacitated'               THEN 'Special Needs/Disabilities'
            WHEN 'Opioid Addict'                        THEN 'Substance Dependency'
            WHEN 'People who use drugs'                 THEN 'Substance Dependency'
            WHEN 'Young Children'                       THEN 'Children (0-13 years old)'
            -- Everything else passes through as-is
            ELSE name
        END AS resolved_name,
        is_parent,
        parent_id
    FROM public.eligibilities
),

-- -------------------------------------------------------
-- CTE 2: Eligibility dimension bucketing
-- Maps each resolved eligibility name to its demographic dimension
-- based on the xlsx taxonomy
-- -------------------------------------------------------
eligibility_bucketed AS (
    SELECT
        e.id,
        e.resolved_name,
        CASE e.resolved_name
            -- AGE
            WHEN 'Age 18-24'                        THEN 'age'
            WHEN 'All Ages'                         THEN 'age'
            WHEN 'I am a Senior'                    THEN 'age'
            WHEN 'Families with children below 18 years old' THEN 'age'
            WHEN 'Youth (below 21 years old)'       THEN 'age'
            WHEN 'Infants'                          THEN 'age'
            WHEN 'Toddlers'                         THEN 'age'
            WHEN 'Children'                         THEN 'age'
            WHEN 'Children (0-13 years old)'        THEN 'age'
            WHEN 'Pre-Teen'                         THEN 'age'
            WHEN 'Teens'                            THEN 'age'
            WHEN 'Teens (13-18 years old)'          THEN 'age'
            WHEN 'Transitional Aged Youth (TAY)'    THEN 'age'
            WHEN 'Adults'                           THEN 'age'
            WHEN 'Maturing Adult'                   THEN 'age'
            WHEN 'Senior'                           THEN 'age'
            -- EDUCATION LEVEL
            WHEN 'ESL/ELL (English Language Learner)' THEN 'education'
            WHEN 'Continuing Education Students'    THEN 'education'
            WHEN 'Preschool'                        THEN 'education'
            WHEN 'Elementary School'                THEN 'education'
            WHEN 'Middle School Students'           THEN 'education'
            WHEN 'High School Students'             THEN 'education'
            WHEN 'Post-Grad'                        THEN 'education'
            WHEN 'College Students'                 THEN 'education'
            -- EMPLOYMENT STATUS
            WHEN 'Active Duty'                      THEN 'employment'
            WHEN 'Employed'                         THEN 'employment'
            WHEN 'National Guard'                   THEN 'employment'
            WHEN 'Retired'                          THEN 'employment'
            WHEN 'Sex Worker'                       THEN 'employment'
            WHEN 'Veterans'                         THEN 'employment'
            WHEN 'Unemployed'                       THEN 'employment'
            -- ETHNICITY
            WHEN 'African/Black'                    THEN 'ethnicity'
            WHEN 'API (Asian/Pacific Islander)'     THEN 'ethnicity'
            WHEN 'Chinese'                          THEN 'ethnicity'
            WHEN 'Filipino/a'                       THEN 'ethnicity'
            WHEN 'Jewish'                           THEN 'ethnicity'
            WHEN 'Latinx'                           THEN 'ethnicity'
            WHEN 'Middle Eastern and North African' THEN 'ethnicity'
            WHEN 'Native American'                  THEN 'ethnicity'
            WHEN 'Pacific Islander'                 THEN 'ethnicity'
            WHEN 'Samoan'                           THEN 'ethnicity'
            -- FAMILY STATUS
            WHEN 'Adoption'                         THEN 'family_status'
            WHEN 'CIP (Children of Incarcerated Parents)' THEN 'family_status'
            WHEN 'Foster Youth'                     THEN 'family_status'
            WHEN 'Individuals'                      THEN 'family_status'
            WHEN 'Single Parent'                    THEN 'family_status'
            WHEN 'Married no children'              THEN 'family_status'
            -- FINANCIAL STATUS
            WHEN 'Benefit Recipients'               THEN 'financial'
            WHEN 'Low-Income'                       THEN 'financial'
            WHEN 'Underinsured'                     THEN 'financial'
            WHEN 'Uninsured'                        THEN 'financial'
            -- GENDER
            WHEN 'LGBTQ+'                           THEN 'gender'
            WHEN 'Men'                              THEN 'gender'
            WHEN 'Non-Binary'                       THEN 'gender'
            WHEN 'Transgender and Gender Non-Conforming' THEN 'gender'
            WHEN 'Women'                            THEN 'gender'
            -- HEALTH CONCERNS
            WHEN 'Abuse or Neglect Survivors'       THEN 'health'
            WHEN 'Chronic Illness'                  THEN 'health'
            WHEN 'Deaf or Hard of Hearing'          THEN 'health'
            WHEN 'HIV/AIDS'                         THEN 'health'
            WHEN 'Limited Mobility'                 THEN 'health'
            WHEN 'Mental Illness'                   THEN 'health'
            WHEN 'Pregnant'                         THEN 'health'
            WHEN 'PTSD'                             THEN 'health'
            WHEN 'Special Needs/Disabilities'       THEN 'health'
            WHEN 'Substance Dependency'             THEN 'health'
            WHEN 'Terminal Illness'                 THEN 'health'
            WHEN 'Visual Impairment'                THEN 'health'
            -- IMMIGRATION STATUS
            WHEN 'Immigrants'                       THEN 'immigration'
            WHEN 'Refugees'                         THEN 'immigration'
            WHEN 'Undocumented'                     THEN 'immigration'
            -- HOUSING STATUS
            WHEN 'Home Owners'                      THEN 'housing'
            WHEN 'Home Renters'                     THEN 'housing'
            WHEN 'Homeless'                         THEN 'housing'
            WHEN 'Homeless Youth'                   THEN 'housing'
            WHEN 'Experiencing Homelessness'        THEN 'housing'
            WHEN 'Imminent Risk of Eviction'        THEN 'housing'
            WHEN 'In Jail'                          THEN 'housing'
            WHEN 'Near Homeless'                    THEN 'housing'
            WHEN 'Re-Entry'                         THEN 'housing'
            -- OTHER
            WHEN 'Anyone in Need'                   THEN 'other'
            WHEN 'Disaster Victim'                  THEN 'other'
            WHEN 'Domestic Violence Survivors'      THEN 'other'
            WHEN 'Gender-Based Violence'            THEN 'other'
            WHEN 'Human Trafficking Survivors'      THEN 'other'
            WHEN 'San Francisco Residents'          THEN 'other'
            WHEN 'Sexual Assault Survivors'         THEN 'other'
            WHEN 'Trauma Survivors'                 THEN 'other'
            ELSE 'other'
        END AS dimension
    FROM eligibility_remapped e
),

-- -------------------------------------------------------
-- CTE 3: Service eligibilities joined + bucketed
-- -------------------------------------------------------
service_eligibilities AS (
    SELECT
        es.service_id,
        eb.resolved_name,
        eb.dimension
    FROM public.eligibilities_services es
    JOIN eligibility_bucketed eb ON eb.id = es.eligibility_id
),

-- -------------------------------------------------------
-- CTE 4: Categories scoped to 0-399, excluding MOHCD (202)
-- Walk category_relationships to get parent label too
-- -------------------------------------------------------
service_categories AS (
    SELECT
        cs.service_id,
        c.id          AS category_id,
        c.name        AS category_name,
        parent_c.name AS parent_category_name
    FROM public.categories_services cs
    JOIN public.categories c ON c.id = cs.category_id
        AND c.id BETWEEN 0 AND 399
        AND c.id != 202
        AND c.id NOT BETWEEN 356 AND 362
    LEFT JOIN public.category_relationships cr ON cr.child_id = c.id
    LEFT JOIN public.categories parent_c ON parent_c.id = cr.parent_id
        AND parent_c.id BETWEEN 0 AND 399
        AND parent_c.id != 202
        AND parent_c.id NOT BETWEEN 356 AND 362
),

-- -------------------------------------------------------
-- CTE 4b: White-label category CTEs
-- SFSG:       1000001–1000012
-- UCSF top:   2000001–2000006
-- UCSF sub:   2100001–2100016
-- OUR415:     356–362
-- -------------------------------------------------------
sfsg_categories AS (
    SELECT
        cs.service_id,
        c.id   AS category_id,
        c.name AS category_name
    FROM public.categories_services cs
    JOIN public.categories c ON c.id = cs.category_id
        AND c.id BETWEEN 1000001 AND 1000012
),

ucsf_top_categories AS (
    SELECT
        cs.service_id,
        c.id   AS category_id,
        c.name AS category_name
    FROM public.categories_services cs
    JOIN public.categories c ON c.id = cs.category_id
        AND c.id BETWEEN 2000001 AND 2000006
),

ucsf_sub_categories AS (
    SELECT
        cs.service_id,
        c.id   AS category_id,
        c.name AS category_name
    FROM public.categories_services cs
    JOIN public.categories c ON c.id = cs.category_id
        AND c.id BETWEEN 2100001 AND 2100016
),

our415_categories AS (
    SELECT
        cs.service_id,
        c.id   AS category_id,
        c.name AS category_name
    FROM public.categories_services cs
    JOIN public.categories c ON c.id = cs.category_id
        AND c.id BETWEEN 356 AND 362
),

-- -------------------------------------------------------
-- CTE 5: Addresses
-- Fan out all service addresses — one row per service+address combination.
-- This means multi-location services produce multiple chunks, each
-- with their own lat/long and location prose.
-- Resource address is used only as fallback when service has no address at all.
-- -------------------------------------------------------
service_address AS (
    SELECT
        a_svc.service_id,
        a.id        AS address_id,
        a.address_1,
        a.address_2,
        a.city,
        a.state_province,
        a.postal_code,
        a.latitude,
        a.longitude
    FROM public.addresses_services a_svc
    JOIN public.addresses a ON a.id = a_svc.address_id
),

resource_address AS (
    SELECT
        resource_id,
        id          AS address_id,
        address_1,
        address_2,
        city,
        state_province,
        postal_code,
        latitude,
        longitude
    FROM public.addresses
    WHERE resource_id IS NOT NULL
),

-- -------------------------------------------------------
-- CTE 6: Phones
-- service_id is always null in production — resource-scoped only
-- -------------------------------------------------------
service_phones AS (
    SELECT
        resource_id,
        string_agg(
            number || ' (' || service_type || ')',
            ', '
        ) AS phone_text
    FROM public.phones
    GROUP BY resource_id
),

-- -------------------------------------------------------
-- CTE 7: Schedules + schedule_days
-- opens_at/closes_at stored as integers e.g. 900 = 9:00 AM, 1730 = 5:30 PM
-- Produces:
--   hours_text  — human readable prose for embedding
--   schedule    — jsonb array of {day, open_mins, close_mins} for "open now" filtering
-- Service schedule preferred, fallback to resource schedule
-- -------------------------------------------------------
service_schedule AS (
    SELECT
        s.service_id,
        s.resource_id,
        s.hours_known,
        string_agg(
            sd.day || ' ' ||
            to_char(
                (opens_at / 100 * interval '1 hour') + (opens_at % 100 * interval '1 minute'),
                'HH12:MI AM'
            ) || ' - ' ||
            to_char(
                (closes_at / 100 * interval '1 hour') + (closes_at % 100 * interval '1 minute'),
                'HH12:MI AM'
            ),
            ', '
            ORDER BY CASE sd.day
                WHEN 'Monday'    THEN 1
                WHEN 'Tuesday'   THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday'  THEN 4
                WHEN 'Friday'    THEN 5
                WHEN 'Saturday'  THEN 6
                WHEN 'Sunday'    THEN 7
            END
        ) AS hours_text,
        jsonb_agg(
            jsonb_build_object(
                'day',        sd.day,
                'open_mins',  (sd.opens_at / 100 * 60) + (sd.opens_at % 100),
                'close_mins', (sd.closes_at / 100 * 60) + (sd.closes_at % 100)
            )
            ORDER BY CASE sd.day
                WHEN 'Monday'    THEN 1
                WHEN 'Tuesday'   THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday'  THEN 4
                WHEN 'Friday'    THEN 5
                WHEN 'Saturday'  THEN 6
                WHEN 'Sunday'    THEN 7
            END
        ) AS schedule
    FROM public.schedules s
    JOIN public.schedule_days sd ON sd.schedule_id = s.id
    GROUP BY s.id, s.service_id, s.resource_id, s.hours_known
),

-- -------------------------------------------------------
-- CTE 8: Instructions (service-level only)
-- -------------------------------------------------------
service_instructions AS (
    SELECT
        service_id,
        string_agg(instruction, ' | ' ORDER BY id) AS instructions_text
    FROM public.instructions
    GROUP BY service_id
),

-- -------------------------------------------------------
-- CTE 9: Documents (via documents_services)
-- -------------------------------------------------------
service_documents AS (
    SELECT
        ds.service_id,
        string_agg(
            d.url ||
            CASE WHEN d.description IS NOT NULL THEN ' (' || d.description || ')' ELSE '' END,
            ', '
            ORDER BY d.id
        ) AS documents_text
    FROM public.documents_services ds
    JOIN public.documents d ON d.id = ds.document_id
    WHERE d.url IS NOT NULL
    GROUP BY ds.service_id
),

-- -------------------------------------------------------
-- CTE 10: Aggregated eligibility metadata arrays by dimension
-- -------------------------------------------------------
eligibility_meta AS (
    SELECT
        service_id,
        array_agg(resolved_name) FILTER (WHERE dimension = 'age')           AS eligibility_age,
        array_agg(resolved_name) FILTER (WHERE dimension = 'education')     AS eligibility_education,
        array_agg(resolved_name) FILTER (WHERE dimension = 'employment')    AS eligibility_employment,
        array_agg(resolved_name) FILTER (WHERE dimension = 'ethnicity')     AS eligibility_ethnicity,
        array_agg(resolved_name) FILTER (WHERE dimension = 'family_status') AS eligibility_family_status,
        array_agg(resolved_name) FILTER (WHERE dimension = 'financial')     AS eligibility_financial,
        array_agg(resolved_name) FILTER (WHERE dimension = 'gender')        AS eligibility_gender,
        array_agg(resolved_name) FILTER (WHERE dimension = 'health')        AS eligibility_health,
        array_agg(resolved_name) FILTER (WHERE dimension = 'immigration')   AS eligibility_immigration,
        array_agg(resolved_name) FILTER (WHERE dimension = 'housing')       AS eligibility_housing,
        array_agg(resolved_name) FILTER (WHERE dimension = 'other')         AS eligibility_other,
        array_agg(resolved_name)                                            AS eligibility_all
    FROM service_eligibilities
    GROUP BY service_id
),

-- -------------------------------------------------------
-- CTE 11: Aggregated category metadata
-- -------------------------------------------------------
category_meta AS (
    SELECT
        service_id,
        array_agg(DISTINCT category_id)         AS category_ids,
        array_agg(DISTINCT category_name)       AS category_names,
        array_agg(DISTINCT parent_category_name)
            FILTER (WHERE parent_category_name IS NOT NULL) AS parent_category_names
    FROM service_categories
    GROUP BY service_id
),

sfsg_meta AS (
    SELECT
        service_id,
        array_agg(DISTINCT category_id)   AS sfsg_category_ids,
        array_agg(DISTINCT category_name) AS sfsg_category_names
    FROM sfsg_categories
    GROUP BY service_id
),

ucsf_top_meta AS (
    SELECT
        service_id,
        array_agg(DISTINCT category_id)   AS ucsf_top_category_ids,
        array_agg(DISTINCT category_name) AS ucsf_top_category_names
    FROM ucsf_top_categories
    GROUP BY service_id
),

ucsf_sub_meta AS (
    SELECT
        service_id,
        array_agg(DISTINCT category_id)   AS ucsf_sub_category_ids,
        array_agg(DISTINCT category_name) AS ucsf_sub_category_names
    FROM ucsf_sub_categories
    GROUP BY service_id
),

our415_meta AS (
    SELECT
        service_id,
        array_agg(DISTINCT category_id)   AS our415_category_ids,
        array_agg(DISTINCT category_name) AS our415_category_names
    FROM our415_categories
    GROUP BY service_id
)

-- -------------------------------------------------------
-- FINAL SELECT
-- One row per active service
-- -------------------------------------------------------
SELECT

    -- =====================
    -- METADATA ENVELOPE
    -- =====================
    s.id                                AS service_id,
    r.id                                AS resource_id,
    s.program_id,
    s.verified_at,
    s.updated_at,

    -- Address identity — service address preferred, resource address as fallback
    COALESCE(sa.address_id, ra.address_id)  AS address_id,

    -- Location metadata
    COALESCE(sa.latitude,  ra.latitude)     AS latitude,
    COALESCE(sa.longitude, ra.longitude)    AS longitude,

    -- Schedule metadata — jsonb array of {day, open_mins, close_mins} for "open now" filtering
    COALESCE(sched_s.schedule, sched_r.schedule) AS schedule,

    -- Category metadata (scoped 0-355 excluding 202, OUR415 excluded from prose)
    cm.category_ids,
    cm.category_names,
    cm.parent_category_names,

    -- White-label category metadata
    sfsg.sfsg_category_ids,
    sfsg.sfsg_category_names,
    ucsf_top.ucsf_top_category_ids,
    ucsf_top.ucsf_top_category_names,
    ucsf_sub.ucsf_sub_category_ids,
    ucsf_sub.ucsf_sub_category_names,
    our415.our415_category_ids,
    our415.our415_category_names,

    -- Eligibility metadata bucketed by dimension
    em.eligibility_age,
    em.eligibility_education,
    em.eligibility_employment,
    em.eligibility_ethnicity,
    em.eligibility_family_status,
    em.eligibility_financial,
    em.eligibility_gender,
    em.eligibility_health,
    em.eligibility_immigration,
    em.eligibility_housing,
    em.eligibility_other,
    em.eligibility_all,

    -- =====================
    -- PROSE TEXT
    -- Assembled as a single flat string for embedding
    -- =====================
    trim(concat_ws(' ',

        -- Organization identity
        r.name ||
            CASE WHEN r.alternate_name IS NOT NULL
                THEN ', also known as ' || r.alternate_name
                ELSE ''
            END || '.',

        CASE WHEN r.legal_status IS NOT NULL
            THEN 'Organization type: ' || r.legal_status || '.'
            ELSE NULL END,

        CASE WHEN r.short_description IS NOT NULL
            THEN r.short_description
            ELSE NULL END,

        CASE WHEN r.long_description IS NOT NULL
            THEN r.long_description
            ELSE NULL END,

        -- Service identity
        'Service: ' || COALESCE(s.name, 'Unnamed Service') ||
            CASE WHEN s.alternate_name IS NOT NULL
                THEN ' (also known as ' || s.alternate_name || ')'
                ELSE ''
            END || '.',

        CASE WHEN s.short_description IS NOT NULL
            THEN s.short_description
            ELSE NULL END,

        CASE WHEN s.long_description IS NOT NULL
            THEN s.long_description
            ELSE NULL END,

        -- Program
        CASE WHEN p.name IS NOT NULL
            THEN 'Program: ' || p.name ||
                CASE WHEN p.alternate_name IS NOT NULL THEN ' (' || p.alternate_name || ')' ELSE '' END ||
                CASE WHEN p.description IS NOT NULL THEN '. ' || p.description ELSE '' END || '.'
            ELSE NULL END,

        -- Categories (service-level, scoped 0-355 excluding 202)
        CASE WHEN cm.parent_category_names IS NOT NULL AND array_length(cm.parent_category_names, 1) > 0
            THEN 'Categories: ' || array_to_string(cm.parent_category_names, ', ') || '.'
            ELSE NULL END,

        CASE WHEN cm.category_names IS NOT NULL AND array_length(cm.category_names, 1) > 0
            THEN 'Sub-categories: ' || array_to_string(cm.category_names, ', ') || '.'
            ELSE NULL END,

        -- Eligibility (free text field on service)
        CASE WHEN s.eligibility IS NOT NULL
            THEN 'Eligibility: ' || s.eligibility || '.'
            ELSE NULL END,

        -- Eligibility tags (resolved + bucketed)
        CASE WHEN em.eligibility_all IS NOT NULL AND array_length(em.eligibility_all, 1) > 0
            THEN 'Who this service is for: ' || array_to_string(em.eligibility_all, ', ') || '.'
            ELSE NULL END,

        -- Application process
        CASE WHEN s.application_process IS NOT NULL
            THEN 'How to apply: ' || s.application_process
            ELSE NULL END,

        -- Required documents
        CASE WHEN s.required_documents IS NOT NULL
            THEN 'Required documents: ' || s.required_documents || '.'
            ELSE NULL END,

        -- Fee
        CASE WHEN s.fee IS NOT NULL
            THEN 'Fee: ' || s.fee || '.'
            ELSE NULL END,

        -- Wait time
        CASE WHEN s.wait_time IS NOT NULL
            THEN 'Wait time: ' || s.wait_time || '.'
            ELSE NULL END,

        -- Interpretation services (only if available)
        CASE WHEN s.interpretation_services IS NOT NULL
            THEN 'Interpretation services available: ' || s.interpretation_services || '.'
            ELSE NULL END,

        -- Hours of operation (service schedule preferred, fallback to resource)
        CASE
            WHEN sched_s.hours_known = false THEN 'Hours: Call to confirm hours.'
            WHEN sched_s.hours_text IS NOT NULL THEN 'Hours: ' || sched_s.hours_text || '.'
            WHEN sched_r.hours_known = false   THEN 'Hours: Call to confirm hours.'
            WHEN sched_r.hours_text IS NOT NULL THEN 'Hours: ' || sched_r.hours_text || '.'
            ELSE NULL
        END,

        -- Address (service address preferred, fallback to resource)
        CASE WHEN COALESCE(sa.address_1, ra.address_1) IS NOT NULL
            THEN 'Location: ' ||
                COALESCE(sa.address_1, ra.address_1) ||
                CASE WHEN COALESCE(sa.address_2, ra.address_2) IS NOT NULL
                    THEN ', ' || COALESCE(sa.address_2, ra.address_2)
                    ELSE '' END ||
                ', ' || COALESCE(sa.city, ra.city) ||
                ', ' || COALESCE(sa.state_province, ra.state_province) ||
                ' ' || COALESCE(sa.postal_code, ra.postal_code) || '.'
            ELSE NULL END,

        -- Phone numbers (resource-level only)
        CASE WHEN sp.phone_text IS NOT NULL
            THEN 'Phone: ' || sp.phone_text || '.'
            ELSE NULL END,

        -- Email
        CASE WHEN s.email IS NOT NULL
            THEN 'Email: ' || s.email || '.'
            WHEN r.email IS NOT NULL
            THEN 'Email: ' || r.email || '.'
            ELSE NULL END,

        -- Website
        CASE WHEN s.url IS NOT NULL
            THEN 'Service website: ' || s.url || '.'
            WHEN r.website IS NOT NULL
            THEN 'Website: ' || r.website || '.'
            ELSE NULL END,

        -- Instructions
        CASE WHEN si.instructions_text IS NOT NULL
            THEN 'Instructions: ' || si.instructions_text || '.'
            ELSE NULL END,

        -- Documents
        CASE WHEN sd.documents_text IS NOT NULL
            THEN 'Related documents: ' || sd.documents_text || '.'
            ELSE NULL END

    )) AS embedding_text

FROM public.services s

-- Base joins
JOIN public.resources r
    ON r.id = s.resource_id
    AND r.status = 1

LEFT JOIN public.programs p
    ON p.id = s.program_id

-- Address: fan out — one row per service+address
-- Services with no address at all get one row per resource address via fallback below
LEFT JOIN service_address sa
    ON sa.service_id = s.id

-- Address: resource-level fallback — fans out on resource addresses
-- Only joins when the service has no entries in addresses_services
LEFT JOIN resource_address ra
    ON ra.resource_id = r.id
    AND NOT EXISTS (
        SELECT 1 FROM public.addresses_services a_svc2
        WHERE a_svc2.service_id = s.id
    )

-- Phones: resource-level only (service_id always null in production)
LEFT JOIN service_phones sp
    ON sp.resource_id = r.id

-- Schedules: service-level
LEFT JOIN service_schedule sched_s
    ON sched_s.service_id = s.id

-- Schedules: resource-level fallback
LEFT JOIN service_schedule sched_r
    ON sched_r.resource_id = r.id
    AND sched_r.service_id IS NULL

-- Instructions
LEFT JOIN service_instructions si
    ON si.service_id = s.id

-- Documents
LEFT JOIN service_documents sd
    ON sd.service_id = s.id

-- Category metadata
LEFT JOIN category_meta cm
    ON cm.service_id = s.id

-- White-label category metadata
LEFT JOIN sfsg_meta sfsg
    ON sfsg.service_id = s.id

LEFT JOIN ucsf_top_meta ucsf_top
    ON ucsf_top.service_id = s.id

LEFT JOIN ucsf_sub_meta ucsf_sub
    ON ucsf_sub.service_id = s.id

LEFT JOIN our415_meta our415
    ON our415.service_id = s.id

-- Eligibility metadata
LEFT JOIN eligibility_meta em
    ON em.service_id = s.id

-- Active services only
WHERE s.status = 1

ORDER BY r.id, s.id, sa.address_id;