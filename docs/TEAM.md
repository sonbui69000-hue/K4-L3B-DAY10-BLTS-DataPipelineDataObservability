# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** BLTS
- **Mã Nhóm / Lớp:** K4-L3-DAY10
- **Tên Repository Nộp Bài:** K4-L3B-DAY10-BLTS-DataPipelineDataObservability
- **Hình thức:** Cá nhân

## Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Bui Le Thai Son | 02880 | N/A | Phụ trách toàn bộ pipeline: ingestion, cleaning, evaluation, GX 1.x, RAG/ChromaDB, corruption, repair, reporting và kiểm thử end-to-end | reports/individual_02880_BuiLeThaiSon.md |

## Tỷ lệ đóng góp

| Thành viên | MSSV | Tỷ lệ đóng góp | Phạm vi đóng góp |
|---|---:|---:|---|
| Bui Le Thai Son | 02880 | 100% | Toàn bộ mã nguồn, artifacts, báo cáo và kiểm thử pipeline |

Tổng tỷ lệ đóng góp: **100%**.

## Phạm vi deliverable đã thực hiện

- Ingestion Crossref và raw preservation trong src/ingestion/crossref.py.
- Cleaning, age_days và text_for_embedding trong src/ingestion/cleaning.py.
- Great Expectations 1.x Quality Gate và Freshness SLA trong src/observability/quality.py.
- Benchmark test set và evaluation artifacts trong src/evaluation/testset.py.
- Baseline pipeline trong src/pipelines/phase1.py.
- Sáu corruption scenarios trong src/ingestion/corruption.py.
- Corruption, repair từ raw snapshot và comparison report trong src/pipelines/corruption_flow.py.
- ChromaDB indexing, metrics, quality reports và final documentation.

## Bằng chứng chính

- Baseline: retrieval_hit_rate = 1.0, mean_token_f1 = 1.0.
- Corrupted: mean_token_f1 = 0.8741, judge_accuracy = 0.9, quality gate = FAIL.
- Repaired: retrieval_hit_rate = 1.0, mean_token_f1 = 1.0, judge_accuracy = 1.0, quality gate = PASS.
